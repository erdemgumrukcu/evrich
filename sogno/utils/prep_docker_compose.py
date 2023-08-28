import os
import pandas as pd
import yaml

# Get the current directory of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the path to aggregator_info.xlsx
excel_file_path = os.path.join(script_directory, './aggregator_info.xlsx')

# Read the Excel file
df = pd.read_excel(excel_file_path, sheet_name='socket_info')

# Construct the path to save the generated docker-compose.yml
output_file_path = os.path.join(script_directory, '../docker-compose.yml')

connector_list = df['cluster_id'].apply(lambda x: f"{x}").tolist()


compose_config = {
    "version": "3",
    "networks": {
        "sogno_network": {
            "driver": "bridge"
        },
        "external_traffic_network": {
            "external": True
        },
        "external_aggregator_network": {
            "external": True
        }
    },
    "services": {
        "gatewaymqtt": {
            "image": "toke/mosquitto",
            "container_name": "broker",
            "expose": ["1883"],
            "ports": ["1883:1883"],
            "restart": "unless-stopped",
            "networks": ["sogno_network"]
        },
        "api": {
            "container_name": "ServiceAPI",
            "build": {
                "context": "./api",
                "dockerfile": "./Dockerfile"
            },
            "networks": ["sogno_network"],
            "ports": ["7000:7000"]          #TODO: It should be user defined
        },
        "coordinator": {
            "container_name": "coordinator",
            "build": {
                "context": "./coordinator",
                "dockerfile": "./Dockerfile"
            },
            "networks": ["sogno_network", "external_traffic_network"],
            "environment": [
                "TRAFFIC_URL=http://host.docker.internal:8000/trafficforecast/", #TODO: It should be user defined
                "PYTHONUNBUFFERED=1"
            ],
        },
        "routingalgorithm": {
            "container_name": "Optimizer",
            "build": {
                "context": "./optimizer",
                "dockerfile": "./Dockerfile"
            },
            "networks": ["sogno_network"],
            "environment": [
                "PYTHONUNBUFFERED=1"
            ]
        }
    }
}

for connector in connector_list:
    service_name = f"connector{connector.lower()}"
    compose_config["services"][service_name] = {
        "container_name": f"connector{connector}",
        "build": {
            "context": f"./connector",
            "dockerfile": "./Dockerfile"
        },
        "networks": ["sogno_network", "external_aggregator_network"],
        "depends_on": ["coordinator"],
        "environment": [
                f"CONNECTOR_ID=aggregator{connector}",
                f"AGGREGATOR_URL=http://host.docker.internal:{df[df['cluster_id'] == int(connector[-1])]['port_number'].values[0]}/availability/",  #TODO: This does not yield the port number 
                f"REQUEST_TOPIC=availability/request/aggregator{connector}",
                f"RESPONSE_TOPIC=availability/response/aggregator{connector}",
                "PYTHONUNBUFFERED=1"
            ]
    }

# Save the YAML configuration to the output file
with open(output_file_path, 'w') as f:
    yaml.dump(compose_config, f)
