from glob import glob
from PseudoNetCDF import pncopen
from collections import OrderedDict
from datetime import datetime
import json
import os
import sys

dataroot = sys.argv[1]
paths = glob(dataroot + '/*')
out = {}
for path in paths:
    print(path)
    try:
        f = pncopen(path, format = 'woudcsonde', addcf = False)
        stype = f.variables['PLATFORM_Type'].view('S64')[0, 0].decode().strip()
        sid = f.variables['PLATFORM_ID'][:].array()[0]
        key = '%s%03d' % (stype, sid)
        print(key)
        name = f.variables['PLATFORM_Name'].view('S64')[0, 0].decode()
        lat = f.variables['LOCATION_Latitude'][0]
        lon = f.variables['LOCATION_Longitude'][0]
        hghtv = f.variables['LOCATION_Height']
        hght = hghtv[0]
        hght_unit = hghtv.units.strip().replace('unknown', 'meters')
        outdate = f.getTimes()[0]
        datestr = outdate.strftime('%F %H:%M:%S%z')
        print(outdate)
        
        if not key in out:
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
        print(path, e, file = sys.stderr)
        #os.system('vi ' + path)

outf = open('locations.json', 'w')
json.dump(out, outf, indent = 4, sort_keys = True)
outf.close()
print('done')
os.system('date > dataupdated')
