from PseudoNetCDF import pncopen
import numpy as np
import matplotlib.pyplot as plt
import argparse
parser = argparse.ArgumentParser()
seasons = {'ALL': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
           'DJF': [1, 2, 12],
           'MAM': [3, 4, 5],
           'JJA': [6, 7, 8],
           'SON': [9, 10, 11]
          }
parser.add_argument('--showbias', default = False, action = 'store_true', help = 'Print bias on plot for each bin (every fifth between 1000-500hPa)')
parser.add_argument('--label', default = 'Mod', help = 'Label for model in figure')
parser.add_argument('--season', default = 'ALL', choices = list(seasons), help = 'Choose a season, default ALL')
parser.add_argument('obs', help = 'Sonde observations')
parser.add_argument('mod', help = 'Mod for sondes')
parser.add_argument('figpath', help = 'Path for output figure')

args = parser.parse_args()
modellabel = args.label
args.season = seasons[args.season]
sf = pncopen(args.obs, format = 'ioapi', addcf = False)
mf = pncopen(args.mod, format = 'ioapi', addcf = False)
st = sf.getTimes()
sti = np.array([ti for ti, t in enumerate(st) if t.month in args.season])
mt = mf.getTimes()
mti = np.array([ti for ti, t in enumerate(mt) if t.month in args.season])
if 'TSTEP' in sf.dimensions:
    tk = 'TSTEP'
else:
    tk = 'time'

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

sO3 = np.ma.masked_invalid(sf.variables['O3'][:]) * 1000
mO3 = np.ma.masked_where(np.ma.getmaskarray(sO3), mO3)
mx = mO3[:].mean(0)
mx0 = mO3[:].min(0)
mx1 = mO3[:].max(0)

sx = sO3.mean(0)
sx0 = sO3.min(0)
sx1 = sO3.max(0)
sy = my

if args.showbias:
    b = (mO3 - sO3)
    mfb = 2 * (b / (mO3 + sO3)).mean(0) * 100
    nmb = b.mean() / sO3.mean(0) * 100

plt.close()
ax = plt.gca()
ax.fill_betweenx(sy, sx0, sx1, color = 'red', alpha = 0.5)
ax.fill_betweenx(my, mx0, mx1, color = 'grey', alpha = 0.5)
ax.plot(sx, sy, color = 'red', label = 'Sonde')
ax.plot(mx, my, color = 'grey', label = modellabel)
plt.xscale('log', subsx = [2.5,5])
plt.yscale('log', subsy = [2.5,5])
ax.yaxis.set_major_formatter(plt.matplotlib.ticker.FormatStrFormatter('%d'))
ax.yaxis.set_minor_formatter(plt.matplotlib.ticker.FormatStrFormatter('%d'))
ax.xaxis.set_major_formatter(plt.matplotlib.ticker.FormatStrFormatter('%d'))
ax.xaxis.set_minor_formatter(plt.matplotlib.ticker.FormatStrFormatter('%d'))
plt.ylim(psrf, 50)
plt.xlim(10, 5e3)
if args.showbias:
    for tti, (ty, ymfb, ynmb) in enumerate(zip(sy, mfb, nmb)):
        if (tti % 5 == 0) or ty < 500: plt.text(5e3, ty, '{0:.0f}, {1:.0f}'.format(ynmb, ymfb))

plt.ylabel('pressure (hPa; psrf = station)')
plt.xlabel('Ozone (ppb)')
plt.legend(loc = 'lower right')
dates = mf.getTimes()
if hasattr(sf, 'Station'):
    titlestr = '{} ({}, {}) ({}, {}, {})'.format(sf.Station, sf.Longitude, sf.Latitude, len(dates), min(dates).strftime('%Y-%m-%d'), max(dates).strftime('%Y-%m-%d'))
else:
    Station = sf.variables['PLATFORM_Name'][0,:].filled('').view('S64')[0].decode()
    Latitude = float(sf.variables['LOCATION_Latitude'][0])
    Longitude = float(sf.variables['LOCATION_Longitude'][0])
    titlestr = '{} ({}, {}) ({}, {}, {})'.format(Station, Longitude, Latitude, len(dates), min(dates).strftime('%Y-%m-%d'), max(dates).strftime('%Y-%m-%d'))
ax.set_title(titlestr)
#if prefix == 'hh':
#    import pdb; pdb.set_trace()
plt.savefig(args.figpath)
