# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 11:15:39 2022

@author: egu
"""

import paho.mqtt.client as mqtt
import pandas as pd
import requests
import os
import json
from datetime import datetime,timedelta,timezone
import time


# Get environment variables
traffic_service_url= os.environ.get('TRAFFIC_URL')

connector_list = []  # Initialize an empty list for connector IDs

#MQTT handlers   
def on_connector_ids_connect(client, userdata, flags, rc):
    print("Controller connected to connector IDs topic with result code " + str(rc))
    client.subscribe("connector_ids")

def on_connect(client, userdata, flags, rc):

    print("Controller connected with result code "+str(rc))
    
    #Subscribe to the client request messages coming from the Service API
    client.subscribe("client/request/type1")    
    #TODO: Subscribe to the client request messages of other types

    #Subcribe to the response messages of the Optimization microservice
    client.subscribe("routing/response/emo") 

    #Subscribe to the response messages of the Connector microservices

    global availability_request_topics
    global availability_response_topics
    availability_request_topics={}
    availability_response_topics={}

    for connector_name in connector_list:
        availability_request_topics[connector_name]='availability/request/'+connector_name
        availability_response_topics[connector_name]='availability/response/'+connector_name
        client.subscribe(availability_response_topics[connector_name])

def on_connector_id_message(client, userdata, msg):
    global connector_list
    connector_id = msg.payload.decode("utf-8")
    if connector_id not in connector_list:
        connector_list.append(connector_id)
        print(f"Connector with ID '{connector_id}' has been saved to the connectors list.")
     
def on_message(client, userdata, msg):
       
    topic=str(msg.topic) 
    _topic=topic.split('/')
        
    if _topic[:2]==['client','request']:

        if _topic[2]=='type1':

            print("Controller recieved a routing request of Type1")
            global ev_client_request
            ev_client_request=json.loads(msg.payload)
            print(ev_client_request)

            #Setting global parameters which will be populated through on_message callbacks
            global availability
            availability={}
            
            # The Controller microservice requests traffic data from external services
            #TODO: Consider delegating this function to a TrafficServiceConnector in the future
            traffic_service_request={}
            
            #Inputs for vehicle characterization
            traffic_service_request['vehicle_model']=ev_client_request['vehicle_model']                                
            traffic_service_request['battery_energy_capacity']=ev_client_request['battery_energy_capacity']
            
            #Inputs for starting conditions (drive before arrival in sojourn location)
            traffic_service_request['drive_start_location']=ev_client_request['start_location']
            traffic_service_request['drive_start_time']=ev_client_request['start_time']
            traffic_service_request['drive_start_SOC']=ev_client_request['start_SOC']
            
            #Inputs related to the suitable clusters in the sojourn location
            #TODO: More sophisticated filtering based on sojourn_location_center and sojourn_location_radius
            traffic_service_request['candidate_hosts']=connector_list 
            print("Sending an HTTP request to the external traffic service:")
            traffic_servive_response_=requests.post(traffic_service_url, json = traffic_service_request)
            traffic_servive_response=traffic_servive_response_.json()
            print("The received traffic response:")
            print(traffic_servive_response)   
            
            #TODO: Make the sleep time adaptive: if the response comes early then go to the next step without waiting for 0.5 seconds
            time.sleep(0.5)
            ########################################################################################################################
            
            #Collecting optimization parameters for SmartRouting microservice
            global opt_parameters
            opt_parameters={}
            opt_parameters['opt_step']=300                                    #TODO: Specify the resolution of the optimization in the configuration file or making it adaptive
            opt_parameters['ecap']    =ev_client_request['battery_energy_capacity']*3600
            opt_parameters['v2gall']  =ev_client_request['demand_v2g_allowance']*3600
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
                opt_parameters['arrtime'][agg_id]=traffic_servive_response[agg_id]['estimate_arrival_time']
                opt_parameters['deptime'][agg_id]=traffic_servive_response[agg_id]['estimate_arrival_time']+ev_client_request['sojourn_period']
                opt_parameters['arrsoc'][agg_id] =traffic_servive_response[agg_id]['estimate_arrival_SOC']
                        
                #Inputs for availability queries (the data that will be sent to the Connector microservices)
                inputs_for_availability_query={}
                inputs_for_availability_query['estimate_arrival_time']  =opt_parameters['arrtime'][agg_id]
                inputs_for_availability_query['estimate_departure_time']=opt_parameters['deptime'][agg_id]
                inputs_for_availability_query['query_resolution']=300                       
                
                charging_demand_limited_by_target_SOC=((ev_client_request['demand_target_SOC']-opt_parameters['arrsoc'][agg_id])*ev_client_request['battery_energy_capacity'])*3600
                charging_demand_limited_by_pow_limit =ev_client_request['battery_power_charging']*ev_client_request['sojourn_period']
                inputs_for_availability_query['energy_demand']=min(charging_demand_limited_by_target_SOC,charging_demand_limited_by_pow_limit)

                mqtt_topic=availability_request_topics[agg_id]
                message_payload=json.dumps(inputs_for_availability_query)        
            
                #Publishing the availablity query messages
                print("Query to",agg_id,"under topic:",mqtt_topic) 
                client.publish(mqtt_topic, message_payload)

        else:
            print("Request type undefined") 
    
    elif _topic[:2]==['availability','response']:
        
        agg_id=_topic[2]
        message_loaded= json.loads(msg.payload)
        
        print("Availability response received from", agg_id, ".")       
        availability[agg_id]=message_loaded
        if availability[agg_id] is not None:
            agg_response=availability[agg_id]
            
            opt_parameters['p_ch'][agg_id]=min(agg_response['p_ch_max'],ev_client_request['battery_power_charging'])
            opt_parameters['p_ds'][agg_id]=min(agg_response['p_ds_max'],ev_client_request['battery_power_discharge'])
            opt_parameters['dps_g2v'][agg_id]=agg_response['dps_g2v']
            opt_parameters['dps_v2g'][agg_id]=agg_response['dps_v2g']
            opt_parameters['candidate_chargers'][agg_id]=agg_response['charger_id']
                    
        # Timer check to continue process even if not all connectors return reply
        # TODO: Wait 5-10-15 secs if its not equal --> calculate with data received till now
        # TODO: Take this logic to datafev, add todos there (delay control)
        if len(availability)==len(connector_list): 

            #Target SOC is the maximum achievable SOC under the given options
            tarsocs={}
            for agg_name in availability.keys():
                delta_soc=agg_response['max_energy_supply']/opt_parameters['ecap']
                tarsocs[agg_name]=opt_parameters['arrsoc'][agg_id]+delta_soc
            opt_parameters['tarsoc'] =pd.Series(tarsocs).max()

            #Optimization horizon covers earliest arrival and latest departure 
            opt_parameters['opt_horizon_start']=pd.Series(opt_parameters['arrtime']).min()
            opt_parameters['opt_horizon_end']  =pd.Series(opt_parameters['deptime']).max()

            #Parsing the inputs for Optimization microservice
            routing_optimization_parameters=json.dumps(opt_parameters)
            
            #Execution of routing microservice
            client.publish("routing/request/emo",routing_optimization_parameters)
            print("Controller published a routing/request/emo MQTT message.")


    elif _topic[:2]==['routing','response']:
        
        emo_name=topic[2]
        message_loaded=json.loads(msg.payload)
        print("Response received from optimization microservice ",emo_name)
        print("Routing response",message_loaded)
             
        #The response to be sent to the EV client
        response_to_ev={}
        response_to_ev['Charger']   =message_loaded['Charger']
        response_to_ev['Aggregator']=message_loaded['Aggregator']
        response_to_ev_json=json.dumps(response_to_ev)
       
        #Publish the Type1 response to be read by the API and directed to the EV client
        client.publish("client/response/type1",response_to_ev_json)
        print("Controller published a client/response/type1 MQTT message.")

        
        #TODO: Publish routing response for the Connector microservices
        for agg_id in connector_list:
            aggregator_id = message_loaded['Aggregator']
            # Send response just to selected aggregator
            if agg_id == aggregator_id:
                response_to_ag = message_loaded  # Prepare the response to the aggregator's connector
                response_to_ag['VehicleID'] = ev_client_request['vehicle_id'] 
                response_to_ag_json = json.dumps(response_to_ag)
                response_topic = f"response_to_{aggregator_id}"
                client.publish(response_topic, response_to_ag_json)
                print("Controller published a ", response_topic, " MQTT message.")

    
        del availability
        del ev_client_request
        del opt_parameters

    else:
        print("Undefined MQTT message recieved.")

# Get URL and PORT from env variables
mqtt_broker_url = os.getenv("MQTT_URL", "gatewaymqtt")
mqtt_broker_port = int(os.getenv("MQTT_PORT", 1883))

client_connector_ids = mqtt.Client("Controller")

# Create MQTT connection for the Controller and set up subscriber callbacks
client_connector_ids.on_connect = on_connector_ids_connect
client_connector_ids.on_message = on_connector_id_message
client_connector_ids.connect(mqtt_broker_url, mqtt_broker_port)

# Start the loop and begin listening to the "connector_ids" topic
client_connector_ids.loop_start()
print("Gathering controller IDs.")
# Wait for a while to collect Connector IDs
time.sleep(5)  # Adjust the appropriate time

# End the loop to ensure the Controller's connection is not cut off
client_connector_ids.loop_stop()
print("Finished gathering controller IDs.")
print(connector_list)
# Create another MQTT connection for the Controller and set up other callbacks
client = mqtt.Client("Controller")
client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_broker_url, mqtt_broker_port)

# Start the MQTT loop to listen to Controller messages
client.loop_forever()
