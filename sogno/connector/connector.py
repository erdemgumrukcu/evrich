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

# Get environment variables
aggregator_id           = os.environ.get('CONNECTOR_ID')
aggregator_url          = os.environ.get('AGGREGATOR_URL')
connector_request_topic = os.environ.get('REQUEST_TOPIC')
connector_response_topic= os.environ.get('RESPONSE_TOPIC')

def on_connect(client, userdata, flags, rc):
    print("Connector of "+str(aggregator_id)+" connected with result code "+str(rc))
    client.subscribe(connector_request_topic)
    #print("Subscribed topic:",connector_request_topic,len(connector_request_topic))
    #client.subscribe("test/123")

def on_message(client, userdata, message):
    
    print("Recieved request under topic:",connector_request_topic)

    #Receive request
    print("received request: ", message.payload)
    f=json.loads(message.payload)
    
    url=aggregator_url
    #availability_response={}
    
    ###########################################################################
    # Availability query
    request={}
    request['aggregator_id']=aggregator_id
    request['estimate_arrival_time']=f["estimate_arrival_time"]
    request['estimate_departure_time']  =f["estimate_departure_time"]
    request['query_resolution'] =f["query_resolution"]
    request['energy_demand']    =f["energy_demand"]
        
    print("Request data from connectivity service:",request)
    response_=requests.post(url, json = request)
    response=response_.json()
    #print("Response of connectivity service API:",response)

    availability_response=response
    
    #Send response
    msg_tosend=json.dumps(availability_response)
    client.publish(connector_response_topic,msg_tosend)
    
    #print("sent response: ", msg_tosend)
    print("sent response under topic: ", connector_response_topic)
   
def on_publish(client,userdata,result):
    print("availability response returned...")   

mqtt_broker_url = os.getenv("MQTT_URL", "gatewaymqtt")
mqtt_broker_port = int(os.getenv("MQTT_PORT", 1883))

client = mqtt.Client(aggregator_id)

client.on_connect = on_connect
client.on_message=on_message
client.on_publish=on_publish

client.connect(mqtt_broker_url,mqtt_broker_port)

client.loop_forever()