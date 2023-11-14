# -*- coding: utf-8 -*-
"""
Created on Mon Dec 19 11:15:39 2022

@author: egu
"""

import paho.mqtt.client as mqtt
import os
import requests
import json

# Get environment variables
aggregator_id = os.environ.get('CONNECTOR_ID')
aggregator_availability_url = os.environ.get('AGGREGATOR_AVAILABILITY_URL')
aggregator_schedule_url = os.environ.get('AGGREGATOR_SCHEDULE_URL')
connector_request_topic = os.environ.get('REQUEST_TOPIC')
connector_response_topic = os.environ.get('RESPONSE_TOPIC')
response_to_ag_topic = f"response_to_{aggregator_id}"
print(response_to_ag_topic)

def on_connect(client, userdata, flags, rc):
    print("Connector of " + str(aggregator_id) + " connected with result code " + str(rc))
    client.subscribe(connector_request_topic)
    client.subscribe(response_to_ag_topic)

    # Publish the aggregator ID to the controller
    client.publish("connector_ids", aggregator_id)

def on_message(client, userdata, message):
    
    print("Received message under topic:", message.topic)

    if message.topic == connector_request_topic:
        # Handle request messages
        print("Received request under topic:", connector_request_topic)

        # Receive request
        print("Received request: ", message.payload)
        f = json.loads(message.payload)

        # Availability query
        request = {}
        request['aggregator_id'] = aggregator_id
        request['estimate_arrival_time'] = f["estimate_arrival_time"]
        request['estimate_departure_time'] = f["estimate_departure_time"]
        request['query_resolution'] = f["query_resolution"]
        request['energy_demand'] = f["energy_demand"]

        print("Request data from connectivity service:", request)
        response_ = requests.post(aggregator_availability_url, json=request)
        response = response_.json()

        availability_response = response

        # Send response
        msg_to_send = json.dumps(availability_response)
        client.publish(connector_response_topic, msg_to_send)

        print("Sent response under topic:", connector_response_topic)
    elif message.topic == response_to_ag_topic:
        # Handle response_to_ag messages
        received_schedule = json.loads(message.payload)
        response_ = requests.post(aggregator_schedule_url, json=received_schedule)
        response = response_.json()
        
    else:
        print("Received a message on an unexpected topic:", message.topic)
   
def on_publish(client, userdata, result):
    print("Availability response returned...")   

mqtt_broker_url = os.getenv("MQTT_URL", "gatewaymqtt")
mqtt_broker_port = int(os.getenv("MQTT_PORT", 1883))

client = mqtt.Client(aggregator_id)

client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

client.connect(mqtt_broker_url, mqtt_broker_port)

client.loop_forever()
