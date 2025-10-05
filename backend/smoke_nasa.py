import os
import xarray as xr
import numpy as np

# Local offline NetCDF file
local_file = "offline_merra2.nc4"

def create_offline_dataset():
    print("🧩 Creating dummy offline dataset...")

    # Create fake data arrays
    time = np.arange(0, 24)  # 24 hours
    lat = np.linspace(-90, 90, 10)
    lon = np.linspace(-180, 180, 20)
    t2m = 280 + 10 * np.random.rand(len(time), len(lat), len(lon))  # Temperature (K)
    u10m = np.random.randn(len(time), len(lat), len(lon))  # Wind component

    # Build dataset
    ds = xr.Dataset(
        {
            "T2M": (("time", "lat", "lon"), t2m),
            "U10M": (("time", "lat", "lon"), u10m),
        },
        coords={
            "time": time,
            "lat": lat,
            "lon": lon,
        },
        attrs={
            "title": "Offline MERRA2-like Weather Dataset",
            "description": "Simulated dataset for offline testing",
            "creator": "frees0ul05",
        },
    )

    # Save as NetCDF
    ds.to_netcdf(local_file)
    print(f"✅ Dummy dataset created and saved as {local_file}")
    return ds


def load_offline_dataset():
    print(f"📂 Loading offline dataset from {local_file}...")
    ds = xr.open_dataset(local_file)
    print("✅ Dataset loaded successfully!")
    print(ds)
    return ds


def analyze_dataset(ds):
    print("📊 Running offline analysis...")
    mean_t2m = float(ds["T2M"].mean().values)
    max_t2m = float(ds["T2M"].max().values)
    min_t2m = float(ds["T2M"].min().values)
    print(f"🌡️ Mean Temperature: {mean_t2m:.2f} K")
    print(f"🔥 Max Temperature:  {max_t2m:.2f} K")
    print(f"❄️ Min Temperature:  {min_t2m:.2f} K")


if __name__ == "__main__":
    if not os.path.exists(local_file):
        ds = create_offline_dataset()
    else:
        ds = load_offline_dataset()

    analyze_dataset(ds)
