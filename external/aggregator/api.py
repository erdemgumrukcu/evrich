# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 14:33:32 2022

@author: egu
"""
import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict

class AvailabilityRequest(BaseModel):
    estimate_arrival_time: float
    estimate_departure_time:float
    query_resolution: int
    energy_demand: float

# Get environment variables DATAFEV_INIT_URL and DATAFEV_UPDATE_URL
datafev_charger_selection_url = os.environ.get('DATAFEV_CHARGER_SELECTION_URL')
datafev_update_url = os.environ.get('DATAFEV_RESERVATION_URL')
# Get environment variable Cluster ID
cluster_id = os.environ.get('CLUSTER_ID')

app = FastAPI()

@app.post("/availability/")
async def request_charging_offer(item: AvailabilityRequest):
    try:
        print('Received availability request from connector.')
        request_data = item.dict()
        # Add the cluster_id to the request data
        request_data['cluster_id'] = cluster_id
        print('Sending charger_selection request to datafev.')
        response = requests.post(datafev_charger_selection_url, json=request_data, timeout=5)
        print('Received charger_selection response from datafev.', response)

        if response.status_code == 200:
            response_data = response.json()
            print('Sending availability response to connector.')
            return response_data
        else:
            raise HTTPException(status_code=500, detail="External service returned an error.")
    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, and other request exceptions
        raise HTTPException(status_code=503, detail="Failed to connect to the external service")

class Schedule(BaseModel):
    Aggregator: str
    Charger: str
    P_Schedule: Dict[str, float]
    S_Schedule: Dict[str, float]
    VehicleID: str
    ArrivalTime: float

@app.post("/schedule/")
async def request_charging_offer(item: Schedule):
    try:
        print('Received charger schedule from connector.')
        schedule = item.dict()
        print('Sending charger schedule to datafev.')
        response = requests.post(datafev_update_url, json=schedule)
        if response.status_code == 200:
            return {"message": "Datafev reservation data received and sent successfully."}
        else:
            raise HTTPException(status_code=500, detail="External service returned an error.")
    except requests.exceptions.RequestException as e:
        # Handle connection errors, timeouts, and other request exceptions
        raise HTTPException(status_code=503, detail="Failed to connect to the external service")