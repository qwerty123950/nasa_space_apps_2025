# backend/nasa_data_fetcher.py

import xarray as xr
import datetime
import io
import tempfile
from functools import lru_cache
import requests # Still need this for exception handling

# Import our new, powerful authenticator
from nasa_auth import create_authenticated_session

# --- Configuration (remains the same) ---
OPENDAP_BASE_URL = "https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2T1NXSLV.5.12.4"
VARIABLE_MAP = {
    "max_temp_c": {"name": "T2MMAX", "unit_conversion": lambda x: x - 273.15},
    "min_temp_c": {"name": "T2MMIN", "unit_conversion": lambda x: x - 273.15},
    "precipitation_mm": {"name": "PRECTOTCORR", "unit_conversion": lambda x: x * 86400},
    "wind_speed_kph": {"name": "WSC", "unit_conversion": lambda x: x * 3.6},
    "dust_ug_m3": {"name": "DUSMASS", "unit_conversion": lambda x: x * 1e9},
}
CLIMATE_START_YEAR = 1991
CLIMATE_END_YEAR = 2020

@lru_cache(maxsize=128)
def get_nasa_data(latitude: float, longitude: float, month: int, day: int, variable: str) -> list[float]:
    """
    Final, definitive version. Uses a custom authentication handler to correctly
    navigate the NASA Earthdata login redirects. Downloads to memory for stability.
    """
    if variable not in VARIABLE_MAP:
        return []

    nasa_var_info = VARIABLE_MAP[variable]
    nasa_var_name = nasa_var_info["name"]
    unit_conversion_func = nasa_var_info["unit_conversion"]
    
    historical_values = []
    
    # Create a session that knows how to log into NASA
    session = create_authenticated_session()
    
    print(f"Starting DEFINITIVE fetch for {variable} with custom auth...")

    for year in range(CLIMATE_START_YEAR, CLIMATE_END_YEAR + 1):
        try:
            date = datetime.date(year, month, day)
            month_str, day_str = f"{date.month:02d}", f"{date.day:02d}"

            stream = (
                "100" if year <= 1991 else
                "200" if year <= 2000 else
                "300" if year <= 2010 else
                "400"
            )
            url = (
                f"{OPENDAP_BASE_URL}/{year}/{month_str}/"
                f"MERRA2_{stream}.tavg1_2d_slv_Nx.{year}{month_str}{day_str}.nc4"
            )
            
            # Use our powerful session to download the file content.
            # This session will automatically handle the login redirects.
            response = session.get(url, timeout=30)
            response.raise_for_status()

            # Load via a closed temporary file (Windows: netcdf4 cannot re-open an open NamedTemporaryFile)
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".nc4", delete=False) as tmpf:
                    tmpf.write(response.content)
                    tmp_path = tmpf.name
                with xr.open_dataset(tmp_path, engine='netcdf4') as ds:
                    data_point = ds[nasa_var_name].sel(lat=latitude, lon=longitude, method="nearest").item()
                    converted_value = unit_conversion_func(data_point)
                    historical_values.append(converted_value)
                    print(f"  + Successfully processed data for {year}")
            finally:
                if tmp_path:
                    try:
                        import os
                        os.remove(tmp_path)
                    except Exception:
                        pass

        except ValueError:
            continue
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                continue
            else:
                print(f"  - HTTP Error for year {year}: {e}")
        except Exception as e:
            print(f"  - Unexpected error for year {year}: {e}")
            continue
            
    print(f"...Fetching complete. Successfully retrieved {len(historical_values)} data points.")
    return historical_values