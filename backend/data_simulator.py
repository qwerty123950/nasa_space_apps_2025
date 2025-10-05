# backend/data_simulator.py

import numpy as np

# Define some baseline climate characteristics for our simulation
# In a real app, this would be derived from actual climate data.
# Format: { 'variable_name': (mean, standard_deviation) }
SIMULATION_PARAMS = {
    "max_temp_c": (25, 8),      # Mean 25°C, StdDev 8
    "min_temp_c": (15, 6),
    "precipitation_mm": (2, 5), # Low mean, high variance
    "wind_speed_kph": (15, 7),
    "dust_ug_m3": (50, 25),
}

def get_historical_data(variable: str, num_years: int = 30) -> list[float]:
    """
    Simulates fetching 30 years of historical data for a given variable
    on a specific day of the year.
    """
    if variable not in SIMULATION_PARAMS:
        return []

    mean, std_dev = SIMULATION_PARAMS[variable]
    
    # Generate random data following a normal (Gaussian) distribution
    # This mimics the natural variation of weather data.
    simulated_data = np.random.normal(loc=mean, scale=std_dev, size=num_years)
    
    # Ensure physical constraints (e.g., precipitation can't be negative)
    if "precipitation" in variable or "dust" in variable:
        simulated_data = np.maximum(0, simulated_data) # Set any negative values to 0

    # Return as a list of floating-point numbers rounded to 2 decimal places
    return [round(val, 2) for val in simulated_data]