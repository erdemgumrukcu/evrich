# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 10:44:57 2022

@author: egu
"""

from datetime import datetime,timedelta,timezone
import time
from typing import Union
from pydantic import BaseModel
import json
import pandas as pd
import os
import requests
from fastapi import FastAPI
import paho.mqtt.client as mqtt

# Get environment variables
traffic_service_url= os.environ.get('TRAFFIC_URL')

class ClientRequest(BaseModel):
    vehicle_id: str
    vehicle_model: str
    battery_energy_capacity: float
    battery_power_charging: float
    battery_power_discharge: float
    start_SOC: float = 0.0
    start_time: Union[float,None]=None
    start_location: Union[str,None]=None
    sojourn_location_center: str
    sojourn_location_radius: Union[float,None]=100.0
    sojourn_period: Union[float,None]=3600.0
    demand_target_SOC: float = 1.0
    demand_v2g_allowance: float = 0.0
    
#MQTT jobs     
def on_connect(client, userdata, flags, rc):
    print("Service API is connected to MQTT broker with result code "+str(rc))
      
def on_publish(client,userdata,result):
    print("Published an MQTT message.")
     
def on_message(client, userdata, msg):
       
    topic=str(msg.topic) 
    _topic=topic.split('/')
        
    if _topic[:2]==['client','response']:

        if _topic[2]=='type1':

            message_loaded=json.loads(msg.payload)
            
            response_to_ev['Charger']   =message_loaded['Charger']
            response_to_ev['Aggregator']=message_loaded['Aggregator']
            
    else:
        print("Undefined MQTT message recieved.")



#Platfrom data bus
mqtt_broker_url = os.getenv("MQTT_URL", "gatewaymqtt")
mqtt_broker_port = int(os.getenv("MQTT_PORT", 1883))

#MQTT client of the reservation service
client = mqtt.Client("ServiceAPI")
client.connect(mqtt_broker_url,mqtt_broker_port)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message
client.loop_start()

#Subcribe to the (type 1) response messages of the Controller microservice
client.subscribe("client/response/type1")
  
#Start a restAPI for the routing service
app = FastAPI()

#Define a post request to enable routing request
@app.post("/routing/post_request_type1")                                         
async def post_request(item: ClientRequest):

    post_time=time.time()

    global response_to_ev
    response_to_ev={}

    print('EV client request post:',item.json())

    client.publish("client/request/type1",item.json())
    publish_time=time.time()

    while len(response_to_ev)==0:

        current_time=time.time()

        if current_time-publish_time>=30:
            break
        else:
            pass

    if len(response_to_ev)==0:
        status='fail'
    else:
        status='succes'

    routing_outputs_to_ev=json.dumps(response_to_ev)

    del response_to_ev
    
    resp_time=str(round(time.time()-post_time,2))

    #Send the response of the service to the EV client
    return {'status':status,'response':routing_outputs_to_ev,"response_time":resp_time}
    
