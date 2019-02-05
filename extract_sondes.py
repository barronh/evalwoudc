import os
from collections import OrderedDict
from datetime import datetime
import json
import argparse
from PseudoNetCDF import pncopen, pncwrite
from extrareader import readers

strptime = datetime.strptime
parser = argparse.ArgumentParser()
parser.add_argument(
    '-v', '--verbose', action='count', default=0,
    help='Show more by adding more -v'
)
parser.add_argument(
    '--hourly-interval', type=float, default=1,
    help='Hours between times', dest='hours'
)
parser.add_argument(
    '-t', '--in-type', default='GEOS-Chem',
    choices=['GEOS-Chem', 'CMAQ', 'CAMx'] + readers, help='Model for meta-data'
)
parser.add_argument(
    '--sonde-format', default='l100', choices=['l100', 'woudcsonde'],
    dest='sondeformat',
    help='Sonde text format (NOAA l100 or woudc sonde format',
)
parser.add_argument(
    '-l', '--locations', default='locations.json',
    help='File with sonde locations'
)
parser.add_argument(
    '--sondes', type=lambda x: x.split(','), default=[],
    help='Two character sonde ids'
)
parser.add_argument(
    '--year', type=int, default=None, help='Restrict to a year, default any'
)
parser.add_argument('--season', help='Restrict to a season', default='ALL')
parser.add_argument('intemplate', help='Strftime template for conc inputs')
parser.add_argument('modouttemp', help='Strftime template for conc outputs')
parser.add_argument('sondeouttemp', help='Strftime template for sodne outputs')

args = parser.parse_args()

locations = json.load(open(args.locations), object_pairs_hook=OrderedDict)
intype = args.in_type
intemplate = args.intemplate

sondekeepvars = dict(
    l100=['time', 'Press', 'latitude', 'longitude', 'O3'],
    woudcsonde=[
        'time', 'Pressure', 'PLATFORM_Name', 'PLATFORM_ID',
        'LOCATION_Latitude', 'LOCATION_Longitude', 'LOCATION_Height', 'O3'
    ]
)
sondekeepvar = sondekeepvars[args.sondeformat]
keepsondedims = [
    'LAY', 'STRLEN', 'ROW', 'COL', 'TSTEP', 'latitude', 'longitude', 'time',
    'site', 'level', 'Pressure'
]

# input format options
modformats = {
    'GEOS-Chem': dict(format='bpch', nogroup=True),
    'CAMx': dict(format='uamiv'),
    'CMAQ': dict(format='ioapi'),
}
if intype in modformats:
    modformat = modformats[intype]
else:
    modformat = dict(format=intype)

# dimensions translations
dim2dims = {
    'CAMx': dict(time='TSTEP', longitude='COL', latitude='ROW'),
    'CMAQ': dict(time='TSTEP', longitude='COL', latitude='ROW')
}

if intype in dim2dims:
    dim2dim = dim2dims[intype]
else:
    dim2dim = dict(time='time', longitude='longitude', latitude='latitude')

# vars to keep from model in output
keepvars = {
    'GEOS-Chem': ['time', 'longitude', 'latitude', 'O3', 'hyai', 'hybi'],
    'CAMx': ['TFLAG', 'O3'],
    'CMAQ': ['TFLAG', 'O3']
}

keepvar = keepvars.get(intype, None)

season_months = dict(
    DJF=[12, 1, 2], MAM=[3, 4, 5], JJA=[6, 7, 8], SON=[9, 10, 11]
)
if args.season == 'ALL':
    months = range(1, 13)
elif args.season in season_months:
    months = season_months[args.season]
else:
    months = eval(args.season)

print(months)
debug = False
dothese = args.sondes
for prefix, opts in locations.items():
    modoutpath = args.modouttemp.format(prefix, args.season)
    sondeoutpath = args.sondeouttemp.format(prefix, args.season)
    if os.path.exists(modoutpath) and os.path.exists(sondeoutpath):
        print('Using cached:\n - {}\n - {}' .format(modoutpath, sondeoutpath))
        continue

    if prefix not in dothese and len(dothese) != 0:
        continue
    print(prefix)
    lon = opts['Longitude']
    lat = opts['Latitude']
    """
    asl, aslu = opts['Station Height'].split(' ')
    assert(aslu.strip() == 'meters')
    asl = float(asl)
    dP_Pa = 1.225 * -9.81 * asl
    dP_hPa = dP_Pa / 100
    """

    # All *.l100 files are sondes
    sondepathdict = opts['datapaths']

    # Get the date string from the file path
    datestrs = list(sondepathdict)

    # Sort, which will sort by date
    datestrs.sort()

    # Convert date strings to date objects
    dates = dict([
        (datestr, strptime(datestr, '%Y-%m-%d %H:%M:%S%z'))
        for datestr in datestrs
    ])

    # filter for correct month
    possibledatestrs = [
        datestr for datestr in datestrs if dates[datestr].month in months
    ]

    if args.year is not None:
        possibledatestrs = [
            datestr for datestr in possibledatestrs
            if dates[datestr].year == args.year
        ]

    mydatestrs = [
        datestr for datestr in possibledatestrs
        if os.path.exists(dates[datestr].strftime(args.intemplate))
    ]
    notmydatestrs = [
        datestr for datestr in possibledatestrs
        if not os.path.exists(dates[datestr].strftime(args.intemplate))
    ]
    if len(notmydatestrs) > 0:
        print('Skipping', ', '.join(notmydatestrs))

    if len(mydatestrs) == 0:
        print('Skipping', prefix, 'no files match filter')
        continue

    # Make a list of model paths for the sonde files in teh season of interest
    modpaths = [
        dates[datestr].strftime(args.intemplate) for datestr in mydatestrs
    ]

    # Make a list of paths for the sonde files in the season of interest
    sondepaths = [sondepathdict[datestr] for datestr in mydatestrs]

    # Open an example file for metadata
    tmpf = pncopen(modpaths[0], **modformat, addcf=False)

    # Use temp file to calculate i, j indices and ensure they are not arrays
    nrow = len(tmpf.dimensions[dim2dim['latitude']])
    ncol = len(tmpf.dimensions[dim2dim['longitude']])
    try:
        modi, modj = tmpf.ll2ij(lon, lat)
        modi = int(modi)
        modj = int(modj)
        if (
            (modi < 0) or (modj < 0) or
            (modi >= ncol) or (modj >= nrow)
        ):
            raise ValueError()
    except Exception:
        print('Skipping', prefix, 'not in domain')
        continue

    # For CMAQ construct a "hybrid" sigma eta
    if hasattr(tmpf, 'VGLVLS'):
        levelkwds = dict(vglvls=tmpf.VGLVLS, vgtop=tmpf.VGTOP)
    else:
        hyai = tmpf.variables['hyai'][:].array()
        hybi = tmpf.variables['hybi'][:].array()
        levelkwds = dict(hyai=hyai, hybi=hybi)

    # Get a list of model UTC hours
    modhs = [dates[datestr].hour for datestr in mydatestrs]

    # Initialize outputs to None
    modoutfile = None
    sondeoutfile = None

    for sondepath, modpath, modh in zip(sondepaths, modpaths, modhs):
        print(prefix, sondepath)
        print(prefix, modpath)
        # Open SONDE files using the PNC.noaafiles.l100 reader
        sondef = pncopen(sondepath, format=args.sondeformat, addcf=False)

        # 1. Open SONDE files using the PNC.geoschemfiles.bpch,
        #    PNC.camxfiles.Memmaps.uamv, or PNC.cmaqfiles.ioapi
        # 2. optionally, subset variables
        vmodf = pncopen(modpath, **modformat, addcf=False)
        if keepvar is not None:
            vmodf = vmodf.subsetVariables(keepvar)

        # create a slicing dictionary where modh is converted
        # t otime index and dimension names are consistent
        # with the time step
        hoffset = int(vmodf.getTimes()[0].hour)
        hidx = int(modh // args.hours)
        if hoffset != 0:
            print('Not starting at 0:', hoffset)
            print('Old hidx:', hidx)
            hidx = int((modh - hoffset) // args.hours)
            print('New hidx:', hidx)

        sdims = {dim2dim['time']: [hidx],
                 dim2dim['latitude']: modj,
                 dim2dim['longitude']: modi}

        # 3. slice dimensions to get sonde location
        # 4. remove latitude and longitude, which sould now be singletons
        modf = vmodf.sliceDimensions(**sdims)\
                    .removeSingleton(dim2dim['latitude'])\
                    .removeSingleton(dim2dim['longitude'])

        # 1. Average sondefile to Sigma structure
        # 2. subest for just eh variables to keep
        # 3. rename the singleton site dimension to time
        # 4. take only the first sonde "level" (all sigma levels are retained
        satmodf = sondef.avgSigma(**levelkwds, copyall=True)\
                        .subsetVariables(sondekeepvar)\
                        .renameDimension('flight', dim2dim['time'])\
                        .sliceDimensions(level=0)
        for dk in list(satmodf.dimensions):
            if dk not in keepsondedims:
                del satmodf.dimensions[dk]
        # If output files are not present, use modf and satmodf
        #                                  to initialize
        # Otherise, stack exiting out file and new outfile
        if modoutfile is None:
            modoutfile = modf
        else:
            modoutfile = modoutfile.stack(modf, dim2dim['time'])
        if sondeoutfile is None:
            sondeoutfile = satmodf
        else:
            sondeoutfile = sondeoutfile.stack(satmodf, dim2dim['time'])

    # After all flights for a sonde have been processed
    # write out the model and sonde file
    pncwrite(modoutfile, modoutpath, format='NETCDF4')
    pncwrite(sondeoutfile, sondeoutpath, format='NETCDF4')

os.system('date > ncupdated')
