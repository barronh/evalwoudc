from PseudoNetCDF import pncopen
import numpy as np
import matplotlib.pyplot as plt
import argparse
seasons = {'ALL': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
           'DJF': [1, 2, 12],
           'MAM': [3, 4, 5],
           'JJA': [6, 7, 8],
           'SON': [9, 10, 11]
          }
parser = argparse.ArgumentParser()
parser.add_argument('--showbias', default = False, action = 'store_true', help = 'Print bias on plot for each bin (every fifth between 1000-500hPa)')
parser.add_argument('--label', default = 'Mod', help = 'Label for model in figure')
parser.add_argument('--figsize', default = (12,6), type = lambda x: tuple([eval(s) for s in x.split(',')]), help = 'Label for model in figure')
parser.add_argument('--season', default = 'ALL', choices = list(seasons), help = 'Choose a season, default ALL')
parser.add_argument('--modreplace', default='SONDE_,', help = 'Remove,replace on sonde files')
parser.add_argument('sondes', nargs = '+', help = 'Sonde files')
parser.add_argument('figpath', help = 'Path for output figure')

args = parser.parse_args()
modellabel = args.label
args.season = seasons[args.season]
mf = None
sf = None
sids = []
lats = []
tk = None
for path in args.sondes:
    modpath = path.replace(*args.modreplace.split(','))
    modf = pncopen(modpath, format = 'netcdf', addcf = False)
    mt = modf.getTimes()
    ismine = np.array([i for i, t in enumerate(mt) if t.month in args.season])
    if ismine.size == 0: continue
    if tk is None:
        if 'TSTEP' in modf.dimensions:
            tk = 'TSTEP'
        else:
            tk = 'time'
    modf = modf.sliceDimensions(**{tk: ismine}).applyAlongDimensions(**{tk: 'mean'})
    if mf is None:
        mf = modf
    else:
        mf = mf.stack(modf, tk)
    sonf = pncopen(path, format = 'netcdf', addcf = False).sliceDimensions(**{tk: ismine}).applyAlongDimensions(**{tk: 'mean'})
    sids.append(sonf.variables['PLATFORM_ID'][0])
    lats.append(sonf.variables['LOCATION_Latitude'][0])
    if sf is None: sf = sonf
    else: sf = sf.stack(sonf, tk)

sortidx = np.argsort(lats)
sids = np.array(sids)[sortidx]
lats = np.array(lats)[sortidx]
sf = sf.sliceDimensions(**{tk: sortidx})
mf = mf.sliceDimensions(**{tk: sortidx})
#sf = sf.sliceDimensions(**{tk: sti})
#mf = mf.sliceDimensions(**{tk: mti})

try: psrf = sf.variables['Press'][:].mean()
except: psrf = sf.variables['Pressure'][:].mean()

try: myi = mf.variables['hyai'] + mf.variables['hybi'] * psrf
except: myi = mf.VGLVLS * (psrf - mf.VGTOP / 100) + mf.VGTOP / 100
my = (myi[:-1] + myi[1:]) / 2
mO3v = mf.variables['O3']
if mO3v.units.strip().startswith('ppm'):
    mO3 = mO3v[:] * 1000.
else:
    mO3 = mO3v[:]
mxi = np.arange(mO3.shape[0] + 1)
mx = np.arange(mO3.shape[0]) + .5
sO3 = np.ma.masked_invalid(sf.variables['O3'][:]) * 1000
mO3 = np.ma.masked_where(np.ma.getmaskarray(sO3), mO3)
dO3 = mO3 / sO3
plt.close()
fig = plt.figure(figsize = args.figsize)
soax = fig.add_axes([.05, .1, .275, .8])
moax = fig.add_axes([.325, .1, .275, .8])
cax = fig.add_axes([.6, .1, .025, .8])
doax = fig.add_axes([.675, .1, .25, .8])
dax = fig.add_axes([.925, .1, .025, .8])
onorm = plt.matplotlib.colors.LogNorm(vmin = 10, vmax = 2000)
patches = moax.pcolor(mxi, myi, mO3.T, label = 'mod', norm = onorm, cmap='jet')
soax.pcolor(mxi, myi, sO3.T, label = 'mod', norm = patches.norm, cmap='jet')
vmin = dO3.min()
vmax = dO3.max()
vmax = max(np.abs(vmin), vmax)
vmin = 1/vmax
vmin = .5; vmax = 2
cbar = plt.colorbar(patches, cax = cax)
dedges = [.5, .66, .8, 1.2, 1.5, 2]
dnorm = plt.matplotlib.colors.BoundaryNorm(dedges, 256)
dpatches = doax.pcolor(mxi, myi, dO3.T, label = 'mod', cmap = 'bwr', norm = dnorm)
dbar = plt.colorbar(dpatches, cax = dax, ticks = dedges, format = '%.2f')
for ax in [moax, doax, soax]:
    ax.set_ylim(psrf, 50)
    ax.set_xticks(mx)
    ax.set_xticklabels(['%.2f' % s for s in lats], rotation = 90)
    
moax.yaxis.set_major_formatter(plt.NullFormatter())
doax.yaxis.set_major_formatter(plt.NullFormatter())
#plt.setp(moax.get_xticklabels(), rotation = 90)
soax.set_ylabel('pressure (hPa; psrf = station)')
titlestr = 'WOUDC'
moax.set_title(args.label + ' (ppb)')
soax.set_title('Sonde (ppb)')
doax.set_title('Ratio')
fig.suptitle(titlestr)
#if prefix == 'hh':
#    import pdb; pdb.set_trace()
plt.savefig(args.figpath)
