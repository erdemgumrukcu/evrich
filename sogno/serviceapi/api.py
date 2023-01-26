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

class RoutingRequest(BaseModel):
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
    
class ConnectorEntry(BaseModel):
    aggregator_id: str
    availability_request_topic: str
    availability_response_topic: str    

#MQTT jobs     
def on_connect(client, userdata, flags, rc):
    print("Service API is connected to MQTT broker with result code "+str(rc))
      
def on_publish(client,userdata,result):
    print("Published an MQTT message under the topic.")
     
def on_message(client, userdata, msg):
       
    topic=str(msg.topic) 
    _topic=topic.split('/')
        
    if _topic[:2]==['availability','response']:
        
        aggregator_name=_topic[2]
        message_loaded= json.loads(msg.payload)
        #dps = {float(key) : message_loaded[key] for key in message_loaded}
        #dps=message_loaded
        
        print("Availability response received from",aggregator_name)
        print("Availability response:",message_loaded)
        
        availability[aggregator_name]=message_loaded
    
    elif _topic[:2]==['routing','response']:
        
        emo_name=topic[2]
        message_loaded=json.loads(msg.payload)
        
        print("Routing response received from",emo_name)
        print("Routing response",message_loaded)
        
        response_to_ev['Charger']   =message_loaded['Charger']
        response_to_ev['Aggregator']=message_loaded['Aggregator']
        
        response_to_ag['P Schedule']=message_loaded['P Schedule']
        response_to_ag['S Schedule']=message_loaded['S Schedule']

    else:
        print("Undefined MQTT message recieved.")


#Traffic service request
def request_traffic_forecast(url,item,list_of_aggregators):

    #TODO: Transfer this function to a microservice
    
    #HTTP request to traffic forecast api
    request={}
    
    #Inputs for vehicle characterization
    request['vehicle_model']=item.vehicle_model                                
    request['battery_energy_capacity']=item.battery_energy_capacity
    
    #Inputs for starting conditions (drive before arrival in sojourn location)
    request['drive_start_location']= item.start_location
    request['drive_start_time']=item.start_time
    request['drive_start_SOC']=item.start_SOC
    
    #Inputs related to the suitable clusters in the sojourn location
    #TODO: More sophisticated filtering based on sojourn_location_center and sojourn_location_radius
    request['candidate_hosts']=list_of_aggregators 
    
    print("The API sends an HTTP request to the external traffic service:")
    print(request)
    
    response_=requests.post(url, json = request)
    response=response_.json()
    
    print("The received traffic response:")
    print(response)   
    
    return response
   
#Platfrom data bus
#TODO: Instead of hard-coding specify the broker port as an environment variable in docker-compose.yml 
mqtt_broker_url=os.getenv("MQTT_URL","gatewaymqtt")
mqtt_broker_port=int(os.getenv("MQTT_PORT",1883))   

#MQTT client of the reservation service
client = mqtt.Client("ServiceAPI")
client.connect(mqtt_broker_url,mqtt_broker_port)
client.on_connect = on_connect
client.on_publish = on_publish
client.on_message = on_message
client.loop_start()

#Subcribe to the response messages of the Optimization microservice
client.subscribe("routing/response/emo")
  
#List of Connector microservices and the MQTT topics to interact with them
connector_list=[]
availability_request_topics={}
availability_response_topics={}
#TODO: Instead of hard-coding, specify the microservice identifiers as environment variables in docker-compose.yml
for agg_ in ['aggregator1','aggregator2','aggregator3']:
    
    connector_list.append(agg_)
    availability_request_topics[agg_]='availability/request/'+agg_
    availability_response_topics[agg_]='availability/response/'+agg_
    
    client.subscribe('availability/response/'+agg_)


#Start a restAPI for the routing service
app = FastAPI()
print("Api started")

#Define a post request to register a Connector microservice 
@app.post("/routing/register_connector")
async def register_connector_microservice(item: ConnectorEntry):
    
    #TODO: Check if the connector is already in the list
    connector_list.append(item.aggregator_id)
    availability_request_topics[item.aggregator_id]=item.availability_request_topic
    availability_response_topics[item.aggregator_id]=item.availability_response_topic 
    
    client.subscribe(item.availability_response_topic)
        
    return {'message':'Connector '+item.aggregator_id+' registered'}

#Define a post request to enable routing request
@app.post("/routing/post_request")                                         
async def post_request(item: RoutingRequest):
 
    #Setting global parameters which will be populated through on_message callbacks
    global availability
    global response_to_ev
    global response_to_ag
    availability={}
    response_to_ev={}
    response_to_ag={}
        
    #An HTTP request is send to the external traffic service
    #TODO: Consider delegating this function to a TrafficServiceConnector in the future
    traffic_forecast=request_traffic_forecast(traffic_service_url,item,connector_list)
    #TODO: Make the sleep time adaptive: if the response comes early then go to the next step without waiting for 0.5 seconds
    time.sleep(0.5)
    
    #Collecting optimization parameters for SmartRouting microservice
    opt_parameters={}
    opt_parameters['opt_step']=300                                    #TODO: Specify the resolution of the optimization in the configuration file or making it adaptive
    opt_parameters['ecap']    =item.battery_energy_capacity*3600
    opt_parameters['v2gall']  =item.demand_v2g_allowance*3600
    opt_parameters['arrtime'] ={}
    opt_parameters['deptime'] ={}
    opt_parameters['arrsoc']  ={}
    opt_parameters['p_ch']    ={}
    opt_parameters['p_ds']    ={}
    opt_parameters['dps_g2v'] ={}
    opt_parameters['dps_v2g'] ={}
    opt_parameters['candidate_chargers']={}
    
    #Some of the optimization parameters are specified by the Connector microservice (as result of communication with external end-points)
    #TODO: Parallelize the process of publishing messages
    for agg_id in connector_list:
        
        #Assing the optimization parameters specified by the Traffic service
        opt_parameters['arrtime'][agg_id]=traffic_forecast[agg_id]['estimate_arrival_time']
        opt_parameters['deptime'][agg_id]=traffic_forecast[agg_id]['estimate_arrival_time']+item.sojourn_period
        opt_parameters['arrsoc'][agg_id] =traffic_forecast[agg_id]['estimate_arrival_SOC']
                
        #Inputs for availability queries (the data that will be sent to the Connector microservices)
        inputs_for_availability_query={}
        inputs_for_availability_query['estimate_arrival_time']  =opt_parameters['arrtime'][agg_id]
        inputs_for_availability_query['estimate_departure_time']=opt_parameters['deptime'][agg_id]
        inputs_for_availability_query['query_resolution']=300                       
        
        charging_demand_limited_by_target_SOC=((item.demand_target_SOC-opt_parameters['arrsoc'][agg_id])*item.battery_energy_capacity)*3600
        charging_demand_limited_by_pow_limit =item.battery_power_charging*item.sojourn_period
        inputs_for_availability_query['energy_demand']=min(charging_demand_limited_by_target_SOC,charging_demand_limited_by_pow_limit)
        
        message_client=availability_request_topics[agg_id]
        message_payload=json.dumps(inputs_for_availability_query)        
    
        #Publishing the availablity query messages 
        # #print("Publishing under topic",message_client)  
        client.publish(message_client, message_payload)
                    
    #TODO: Make the sleep time adaptive: if the response comes early then go to the next step without waiting for 0.5 seconds
    time.sleep(2)
    
    #This block calculates the maximum energy that can be offered to the EV that request RoutingService
    tarsocs={}    
    
    for agg_id in connector_list:
        
        agg_response=availability[agg_id]
        
        opt_parameters['p_ch'][agg_id]=min(agg_response['p_ch_max'],item.battery_power_charging)
        opt_parameters['p_ds'][agg_id]=min(agg_response['p_ds_max'],item.battery_power_discharge)
        opt_parameters['dps_g2v'][agg_id]=agg_response['dps_g2v']
        opt_parameters['dps_v2g'][agg_id]=agg_response['dps_v2g']
        opt_parameters['candidate_chargers'][agg_id]=agg_response['charger_id']
        
        delta_soc=agg_response['max_energy_supply']/opt_parameters['ecap']
        tarsocs[agg_id]=opt_parameters['arrsoc'][agg_id]+delta_soc
        
    opt_parameters['tarsoc'] =pd.Series(tarsocs).max()
    opt_parameters['opt_horizon_start']=pd.Series(opt_parameters['arrtime']).min()
    opt_parameters['opt_horizon_end']  =pd.Series(opt_parameters['deptime']).max()
     
    #Parsing the inputs for Optimization microservice
    routing_optimization_parameters=json.dumps(opt_parameters)
    
    #Execution of routing microservice
    client.publish("routing/request/emo",routing_optimization_parameters)    
    
    #TODO: Make the sleep time adaptive: if the response comes early then go to the next step without waiting for 0.5 seconds
    time.sleep(1.5)
    
    #Convert the result dictionary (including the charger to be reserved) into json
    routing_outputs_to_ev=json.dumps(response_to_ev)
    # routing_outputs_to_ag=json.dumps(response_to_ag)

    del availability
    del response_to_ev
    del response_to_ag
   
    #Send the response of the service to the EV client
    return {'status':'success','response':routing_outputs_to_ev}
    
