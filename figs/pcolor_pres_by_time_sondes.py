from PseudoNetCDF import pncopen
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import argparse

mdates = plt.matplotlib.dates
parser = argparse.ArgumentParser()
parser.add_argument(
    '--showbias', default=False, action='store_true',
    help='Print bias on plot for each bin (every fifth between 1000-500hPa)'
)
parser.add_argument('--label', default='Mod', help='Label for model in figure')
parser.add_argument(
    '--npoint', default=10, type=int,
    help='Points for time smoothing'
)
parser.add_argument(
    '--figsize', default=(12, 6),
    type=lambda x: tuple([eval(s) for s in x.split(',')]),
    help='Label for model in figure'
)
parser.add_argument(
    '--modreplace', default='SONDE_,', help='Remove,replace on sonde files'
)
parser.add_argument('sondes', nargs='+', help='Sonde files')
parser.add_argument('figpath', help='Path for output figure')

args = parser.parse_args()
modellabel = args.label
mf = None
sf = None
tk = None
for path in args.sondes:
    modpath = path.replace(*args.modreplace.split(','))
    modf = pncopen(modpath, format='netcdf', addcf=False)
    if tk is None:
        if 'TSTEP' in modf.dimensions:
            tk = 'TSTEP'
        else:
            tk = 'time'
    if mf is None:
        mf = modf
    else:
        mf = mf.stack(modf, tk)
    sonf = pncopen(path, format='netcdf', addcf=False)
    if sf is None:
        sf = sonf
    else:
        sf = sf.stack(sonf, tk)

sortidx = np.argsort(sf.getTimes())


def avgn(x, n=args.npoint):
    return np.ma.mean([
        np.ma.masked_values(x[i:-(n-i)], -999) for i in range(n)
    ], axis=0)


ssf = sf.sliceDimensions(**{tk: sortidx})
sf = ssf.applyAlongDimensions(**{tk: avgn})
smf = mf.sliceDimensions(**{tk: sortidx})
mf = smf.applyAlongDimensions(**{tk: avgn})
times = mf.getTimes()
mxd = [datetime(t.year, t.month, t.day) for t in times]
t = times[-1]
mxd.append(datetime(t.year, t.month, t.day) + timedelta(hours=24))
mxd = np.array(mxd)
# sf = sf.sliceDimensions(**{tk: sti})
# mf = mf.sliceDimensions(**{tk: mti})

if 'Press' in sf.variables:
    psrf = sf.variables['Press'][:].mean()
else:
    psrf = sf.variables['Pressure'][:].mean()

if 'hyai' in mf.variables and 'hybi' in mf.variables:
    myi = mf.variables['hyai'][:] + mf.variables['hybi'][:] * psrf
else:
    myi = mf.VGLVLS * (psrf - mf.VGTOP / 100) + mf.VGTOP / 100

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
fig = plt.figure(figsize=args.figsize)
soax = fig.add_axes([.05, .2, .26, .7])
moax = fig.add_axes([.325, .2, .26, .7])

cax = fig.add_axes([.6, .2, .025, .7])
doax = fig.add_axes([.675, .2, .25, .7])
dax = fig.add_axes([.925, .2, .025, .7])
onorm = plt.matplotlib.colors.LogNorm(vmin=10, vmax=2000)
patches = moax.pcolor(mxd, myi, mO3.T, label='mod', norm=onorm, cmap='jet')
soax.pcolor(mxd, myi, sO3.T, label='mod', norm=patches.norm, cmap='jet')
vmin = dO3.min()
vmax = dO3.max()
vmax = max(np.abs(vmin), vmax)
vmin = 1/vmax
vmin = .5
vmax = 2
cbar = plt.colorbar(patches, cax=cax)
dedges = [.5, .66, .8, 1.2, 1.5, 2]
dnorm = plt.matplotlib.colors.BoundaryNorm(dedges, 256)
dpatches = doax.pcolor(mxd, myi, dO3.T, label='mod', cmap='bwr', norm=dnorm)
dbar = plt.colorbar(dpatches, cax=dax, ticks=dedges, format='%.2f')
for ax in [moax, doax, soax]:
    ax.set_ylim(psrf, 50)
    ax.xaxis.set_major_locator(mdates.DayLocator([1]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax.get_xticklabels(), rotation=90)

moax.yaxis.set_major_formatter(plt.NullFormatter())
doax.yaxis.set_major_formatter(plt.NullFormatter())
# plt.setp(moax.get_xticklabels(), rotation=90)
soax.set_ylabel('pressure (hPa; psrf=station)')
titlestr = 'WOUDC'
moax.set_title(args.label + ' (ppb)', size=24)
soax.set_title('Sonde (ppb)', size=24)
doax.set_title('Ratio', size=24)
# fig.suptitle(titlestr)
# if prefix == 'hh':
#     import pdb; pdb.set_trace()
plt.savefig(args.figpath)
