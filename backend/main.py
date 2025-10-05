# backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np
from scipy.stats import norm
from nasa_data_fetcher import get_nasa_data

app = FastAPI(
    title="TerraClime Planner API",
    description="An API for analyzing the likelihood of weather conditions based on NASA MERRA-2 data."
)

# THIS IS THE CRITICAL PART FOR THE BACKEND
class AnalysisRequest(BaseModel):
    latitude: float = Field(..., example=37.74)
    longitude: float = Field(..., example=-119.59)
    month: int = Field(..., gt=0, lt=13, example=7)
    day: int = Field(..., gt=0, lt=32, example=15)
    variables: List[str] = Field(..., example=["max_temp_c"])

class ThresholdAnalysis(BaseModel):
    probability_exceeding: Optional[float] = Field(None, example=0.40)
    probability_of_event: Optional[float] = Field(None, example=0.10)

class VariableResult(BaseModel):
    variable: str
    unit: str
    mean: float
    std_dev: float
    likelihood: ThresholdAnalysis
    raw_data_points: int

class AnalysisResponse(BaseModel):
    query: AnalysisRequest
    results: List[VariableResult]
    metadata: dict = {
        "data_source": "NASA MERRA-2 M2T1NXSLV.5.12.4 via GES DISC OPe_NDAP",
        "climate_period": "1991-2020"
    }

@app.post("/analyze", response_model=AnalysisResponse)
def analyze_weather_likelihood(request: AnalysisRequest):
    all_results = []
    variable_details = {
        "max_temp_c": {"unit": "°C", "threshold": 32},
        "min_temp_c": {"unit": "°C", "threshold": 0},
        "precipitation_mm": {"unit": "mm", "threshold": 1},
        "wind_speed_kph": {"unit": "kph", "threshold": 40},
        "dust_ug_m3": {"unit": "µg/m³", "threshold": 150},
    }

    for var in request.variables:
        if var not in variable_details:
            continue

        # THIS IS ALSO CRITICAL - PASSING THE RIGHT ARGS
        historical_data = get_nasa_data(
            latitude=request.latitude,
            longitude=request.longitude,
            month=request.month,
            day=request.day,
            variable=var
        )
        
        if not historical_data:
            continue

        mean_val = np.mean(historical_data)
        std_dev_val = np.std(historical_data)
        threshold = variable_details[var]["threshold"]
        likelihood_results = {}

        if "precipitation" in var:
            event_count = sum(1 for day_val in historical_data if day_val > threshold)
            likelihood_results["probability_of_event"] = event_count / len(historical_data)
        else:
            prob = norm.sf(x=threshold, loc=mean_val, scale=std_dev_val if std_dev_val > 0 else 0.01)
            likelihood_results["probability_exceeding"] = prob

        result = VariableResult(
            variable=var,
            unit=variable_details[var]["unit"],
            mean=round(mean_val, 2),
            std_dev=round(std_dev_val, 2),
            likelihood=ThresholdAnalysis(**likelihood_results),
            raw_data_points=len(historical_data)
        )
        all_results.append(result)

    return AnalysisResponse(query=request, results=all_results)