import io
import sys

import xarray as xr

# Ensure local imports work
sys.path.append('weather-likelihood/backend')
from nasa_auth import create_authenticated_session

URL = (
    'https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXSLV.5.12.4/2011/01/'
    'MERRA2_400.tavg1_2d_slv_Nx.20110101.nc4'
)

print('Fetching:', URL)
s = create_authenticated_session()
r = s.get(URL, timeout=60)
r.raise_for_status()

print('HTTP OK, opening dataset...')
with xr.open_dataset(io.BytesIO(r.content), engine='netcdf4') as ds:
    print('Variables:', sorted(ds.data_vars))
    print('Coordinates:', sorted(ds.coords))
    print('Attributes keys:', sorted(ds.attrs.keys()))

    # Check for expected variables used in the app
    expected = ['T2MMAX', 'T2MMIN', 'PRECTOTCORR', 'WSC', 'DUSMASS', 'T2M', 'U10M', 'V10M']
    for name in expected:
        print(f"has {name}?", name in ds.variables)
