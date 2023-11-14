# -*- coding: utf-8 -*-
"""
Created on Tue Dec 20 17:50:39 2022

@author: egu
"""

from typing import Union
from pydantic import BaseModel
from fastapi import FastAPI

class TFRequest(BaseModel):
       
    vehicle_model: str
    battery_energy_capacity: float
    drive_start_location: Union[str,None]=None
    drive_start_SOC: float = 0.0
    drive_start_time: Union[float,None]=None
    candidate_hosts: list
    
    
app = FastAPI()

@app.post("/trafficforecast/")
async def provide_forecast(item: TFRequest):
    
    print('Received trafficforecast request from the coordinator.')
    response={}
    
    for aggregator in item.candidate_hosts:
        
        #TODO: Add more sophisticated estimation logic or another request post
        #Currently each cluster is accessed through identical road conditions: no delay-no deviations
        response[aggregator]={}
        response[aggregator]['estimate_arrival_SOC']=item.drive_start_SOC
        
        if aggregator=='aggregator_5':
            response[aggregator]['estimate_arrival_time']=item.drive_start_time+300
        else:
            response[aggregator]['estimate_arrival_time']=item.drive_start_time
         
    print('Sending trafficforecast response to the coordinator.')
    return response
