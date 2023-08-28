# -*- coding: utf-8 -*-
"""
Created on Sun Dec 25 14:33:32 2022

@author: egu
"""

from typing import Union
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime,timedelta,timezone
import pandas as pd
import numpy as np
import os

from pricing_rule import idp

class AvailabiltiyRequest(BaseModel):
    estimate_arrival_time: float
    estimate_departure_time:float
    query_resolution: int
    energy_demand: float
    
app = FastAPI()

@app.post("/availability/")
async def request_charging_offer(item: AvailabiltiyRequest):
 
    start=datetime.fromtimestamp(item.estimate_arrival_time)
    end  =datetime.fromtimestamp(item.estimate_departure_time)
    step =timedelta(seconds=item.query_resolution)
    estimate_parking_period=pd.date_range(start=start,
                                          end=end-step,
                                          freq=step)
    
    
    ###########################################################################
    ###########################################################################
    #Charger selection algorithm
    
    ###################################################
    #Placeholder
    available_chargers_dict={}
    available_chargers_dict['cu_01_01']={}
    available_chargers_dict['cu_01_01']["max p_ch"]=11
    available_chargers_dict['cu_01_01']["max p_ds"]=0
    available_chargers_dict['cu_01_01']["eff"]=1.0
    available_chargers_dict['cu_01_02']={}
    available_chargers_dict['cu_01_02']["max p_ch"]=22
    available_chargers_dict['cu_01_02']["max p_ds"]=22
    available_chargers_dict['cu_01_02']["eff"]=1.0
    available_chargers_dict['cu_01_03']={}
    available_chargers_dict['cu_01_03']["max p_ch"]=55
    available_chargers_dict['cu_01_03']["max p_ds"]=55
    available_chargers_dict['cu_01_03']["eff"]=1.0
    available_chargers=(pd.DataFrame(available_chargers_dict)).T
    ###################################################
    
    #TODO: available_chargers=cluster.query_availability(start,end,step)
    ###########################################################################
    ###########################################################################
    
    ###########################################################################
    ###########################################################################
    #Charger selection algorithm
    
    parking_duration=item.estimate_departure_time-item.estimate_arrival_time
    ev_energy_demand=item.energy_demand
    
    energy_supply_by_chargers=available_chargers["max p_ch"]*parking_duration
    
    chargers_with_sufficient_supply_rating=energy_supply_by_chargers[energy_supply_by_chargers>=ev_energy_demand]
    
    if len(chargers_with_sufficient_supply_rating):
        selected_charger_id=chargers_with_sufficient_supply_rating.idxmin()
    else:
        selected_charger_id=available_chargers["max p_ch"].idxmax()

    ###########################################################################
    ###########################################################################
    
    ###########################################################################
    #Dynamic pricing algorithm
    
    ###################################################
    #Placeholder
    np.random.seed(1)
    schedule       =(pd.Series(np.random.uniform(low=33.0,high=55.5,size=len(estimate_parking_period)),index=estimate_parking_period)).to_dict()
    upper_bound    =(pd.Series(44.0,index=estimate_parking_period)).to_dict()
    lower_bound    =(pd.Series(0.0,index=estimate_parking_period)).to_dict()
    tou_tariff     =(pd.Series(0.3,index=estimate_parking_period)).to_dict()
    f_discount     =0.0
    f_markup       =0.05
    arbitrage_coeff=0.1
    ###################################################
    
    #TODO: Get relevant queries on datafev.data_handling.cluster.Cluster object
    #schedule   =cc.query_actual_schedule(start, end)
    #upper_bound=cc.upper_limit[start:end]
    #lower_bound=cc.lower_limit[start:end]
    #f_discount : global parameter
    #f_markup: global parameter
    #arbitrage_coef: global parameter
        
    dlp=idp(schedule, upper_bound, lower_bound, tou_tariff, f_discount, f_markup)  
    
    ###########################################################################
    ###########################################################################
    
    p_ch=available_chargers.loc[selected_charger_id,"max p_ch"]
    p_ds=available_chargers.loc[selected_charger_id,"max p_ch"]
    
    response={}
    response['charger_id']=selected_charger_id       
    response['p_ch_max']= float(p_ch) 
    response['p_ds_max']= float(p_ds)
    response['max_energy_supply']=min(p_ch*parking_duration,ev_energy_demand) #kWs
    response['dps_g2v'] = dict([(k, dlp[k]) for k in sorted(dlp.keys())])
    response['dps_v2g'] = dict([(k, dlp[k] * (1 - arbitrage_coeff)) for k in sorted(dlp.keys())])
    
    # ###########################################################################
    
    print("Response sent to EMO:",response)
               
    return response