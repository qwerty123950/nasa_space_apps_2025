# Technology Stack & Requirements (Paste into PDF)

Placement suggestion: insert as a new slide after "How it Works" (page 4) in your current PDF. Note: On page 4, your Technology Stack references NASA POWER and OpenWeatherMap. This app uses NASA GES DISC MERRA-2 (M2T1NXSLV). Update that bullet accordingly if needed.

## Overview
- Project: TerraClime Planner (Weather Likelihood)
- Goal: Estimate likelihood of weather conditions at a lat/lon and date using NASA MERRA-2 data
- Data Provider: NASA GES DISC (MERRA-2, M2T1NXSLV v5.12.4)

## System Prerequisites
- OS: Windows, macOS, or Linux
- Python: 3.11 (Conda environment available)
- CPU/RAM: Any modern CPU; ≥ 2 GB RAM recommended
- Disk: ~1 GB free (environment + temporary NetCDFs)
- Network (HTTPS egress to):
  - urs.earthdata.nasa.gov (Earthdata Login)
  - goldsmr4.gesdisc.eosdis.nasa.gov (GES DISC MERRA-2 data)

## Accounts & Authorization
- Earthdata Account: https://urs.earthdata.nasa.gov/
- One-time Authorization: In Earthdata profile, authorize "NASA GESDISC Data Archive"
  - Shortcut: https://disc.gsfc.nasa.gov/earthdata-login
- Browser Verification: Access a protected MERRA-2 file (e.g., 2011-01-01) and confirm it downloads without further prompts.

## Credentials Configuration (Programmatic)
Choose one option:
- NetRC (recommended):
  - Windows path: `C:\Users\\<User>\\_netrc` (no extension)
  - Content:
    ```
    machine urs.earthdata.nasa.gov
      login YOUR_USERNAME
      password YOUR_PASSWORD
    ```
  - Optional: set `NETRC` env var if stored elsewhere.
- Environment variables:
  - `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD`
  - Also supported: `NASA_EARTHDATA_USERNAME`/`NASA_EARTHDATA_PASSWORD`, `URS_USERNAME`/`URS_PASSWORD`

## Backend/API
- FastAPI (service layer, OpenAPI schema)
- Pydantic (request/response models)
- Uvicorn (ASGI server)
- Requests (HTTP client)
- Authentication: NASA Earthdata Login (URS) via HTTP Basic Auth across redirects

## Scientific & Data Stack
- Xarray (NetCDF handling and labeled arrays)
- netCDF4 (I/O engine; HDF5-backed NetCDF)
- NumPy (numeric computations)
- SciPy (statistics; exceedance probability via normal distribution)

## Dataset & Access
- Collection: MERRA-2 M2T1NXSLV v5.12.4 (1-hour time-averaged, single-level fields)
- Host: `https://goldsmr4.gesdisc.eosdis.nasa.gov`
- Stream IDs by year (for file prefix):
  - 1980–1991 → `MERRA2_100`
  - 1992–2000 → `MERRA2_200`
  - 2001–2010 → `MERRA2_300`
  - 2011–present → `MERRA2_400`

## Computation & Method
- Spatial sampling: nearest-neighbor at requested lat/lon
- Unit conversions:
  - Temperature: K → °C (x − 273.15)
  - Wind speed: m/s → km/h (x × 3.6)
  - Precipitation: kg/m²/s → mm/day (x × 86400)
- Likelihoods:
  - Normal exceedance probability for temperature/wind
  - Event probability for precipitation (fraction of days exceeding threshold)
- Caching: `functools.lru_cache` for repeated queries

## Python Dependencies (requirements.txt)
- fastapi
- uvicorn[standard]
- numpy
- scipy
- requests
- xarray
- netcdf4

## Run Instructions (Backend)
- Install: `pip install -r requirements.txt` (or `conda env create -f environment.yml`)
- Launch: `uvicorn weather-likelihood.backend.main:app --host 0.0.0.0 --port 8000`
- Endpoint: `POST /analyze` with JSON containing latitude, longitude, month, day, variables (e.g., `["max_temp_c"]`)

## Security & Privacy
- Credentials kept locally in `_netrc`/`.netrc` or environment variables
- Credentials are not stored in the repository
- All data access over HTTPS

## Acknowledgments
- NASA GES DISC for MERRA-2 data services
- NASA Earthdata Login (URS) for authentication infrastructure
