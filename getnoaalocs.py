from glob import glob
from PseudoNetCDF import pncopen
from collections import OrderedDict
import json
import sys

dataroot = sys.argv[1]
paths = glob(dataroot + '/*.l100')
out = {}
for path in paths:
    print(path)
    try:
        f = pncopen(path, format='l100', addcf=False)
        stype = 'NOAA'
        sid = f.Flight_Number[:2]
        key = '%s%s' % (stype, sid)
        print(key)
        name = f.Station
        lat = f.variables['latitude'][0]
        lon = f.variables['longitude'][0]
        hght = f.Station_Height
        hght_unit = hght.split(' ')[1]
        outdate = f.getTimes()[0]
        datestr = outdate.strftime('%F %H:%M:%S%z')
        print(outdate)

        if key not in out:
            print('addedkey', key)
            mine = out[key] = OrderedDict()
            mine['Station'] = name
            mine['Station Height'] = '{} {}'.format(hght, hght_unit)
            mine['Latitude'] = lat
            mine['Longitude'] = lon
            mine['datapaths'] = {}
        else:
            mine = out[key]
        mine['datapaths'][datestr] = path
    except Exception as e:
        raise #print(path, e, file=sys.stderr)

print(json.dumps(out, indent=4, sort_keys=True))
