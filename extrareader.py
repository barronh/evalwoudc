__all__ = ['readers']

import numpy as np
from PseudoNetCDF.geoschemfiles._bpch import bpch_base
from PseudoNetCDF import pncopen

# List of readers that are implemented here
readers = ['GCNC']


class GCNC(bpch_base):
    def __init__(self, *args, **kwds):
        """
        GCNC is defined here for the sole purpose of evalwoudc
        It copies variables and attributes from the new netCDF
        formatted GEOS-Chem and renames them to be consistent
        with the PseudoNetCDF bpch reader output. This allows
        the PseudoNetCDF bpch_base class to provide coordinate
        manipulation avgSigma and ll2ij
        """
        # Read the GEOS-Chem netCDF file
        ds = pncopen(*args, format='netcdf', **kwds)

        # Make quick references to object dictionaries
        gvs = ds.variables
        gds = ds.dimensions

        # Copy all global attributes
        self.setncatts(ds.getncatts())

        # Make a list of coordinate variables to copy
        coordkeys = 'time lat lon lev ilev hyai hybi'.split()
        for coordk in coordkeys:
            if coordk in gds:
                self.copyDimension(gds[coordk], key=coordk)
            self.copyVariable(gvs[coordk], key=coordk)

        # Copy SpeciesConc_O3 as O3
        self.copyVariable(gvs['SpeciesConc_O3'], 'O3')

        # Rename lat/lon dimensions and coordinate variables
        self.renameDimensions(lat='latitude', lon='longitude', inplace=True)
        self.renameVariables(lat='latitude', lon='longitude', inplace=True)

        # Get lat/lon for calculating edges
        lat = self.variables['latitude'][:]
        lon = self.variables['longitude'][:]
        dlat = np.abs(np.median(np.diff(lat))) / 2.
        dlon = np.abs(np.median(np.diff(lon))) / 2.

        # Create variables for holding lat/lon boundaries
        self.createDimension('nv', 2)
        latb = self.createVariable(
            'latitude_bounds', lat.dtype, ('latitude', 'nv')
        )
        latb[:, 0] = np.maximum(lat - dlat, -90)
        latb[:, 1] = np.minimum(lat + dlat, 90)
        lonb = self.createVariable(
            'longitude_bounds', lat.dtype, ('longitude', 'nv')
        )
        lonb[:, 0] = lon - dlon
        lonb[:, 1] = lon + dlon

        # Convert the units of O3 to ppb
        ov = self.variables['O3']
        ov[:] *= 1e9
        ov.units = 'ppb'

        # Convert times to have an absolute reference
        # much more convenient stacking later.
        times = self.getTimes()
        tv = self.variables['time']
        tv.units = 'seconds since 1970-01-01 00:00:00+0000'
        tv[:] = np.array([t.timestamp() for t in times])
