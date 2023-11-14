import os
import pandas as pd
import yaml

# Get the current directory of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the path to aggregator_info.xlsx
excel_file_path = os.path.join(script_directory, 'aggregator_info.xlsx')

# Read the Excel file
df = pd.read_excel(excel_file_path)

# Construct the path to save the generated docker-compose.yml
output_file_path = os.path.join(script_directory, '../docker-compose.yml')

services = []

#TODO: Comment each block
for _, row in df.iterrows():
    services.append(
        {
            "container_name": f"aggregator_{row['cluster_id']}",
            "build": {
                "context": "./aggregator",
                "dockerfile": "./Dockerfile"
            },
            "networks": [
                "aggregator_network"
            ],
            "environment": [
                f"CLUSTER_ID={row['cluster_id']}",
                f"IP_ADDRESS={row['ip_address']}",
                f"PORT_NUMBER={row['port_number']}",
                "PYTHONUNBUFFERED=1",
                "DATAFEV_CHARGER_SELECTION_URL=http://host.docker.internal:9004/charger_selection/",
                "DATAFEV_RESERVATION_URL=http://host.docker.internal:9004/reservation/"
            ],
            "ports": [
                f"{row['port_number']}:{row['port_number']}"
            ],
            "depends_on": [
                "datafev"
            ]
        }
    )

compose_config = {
    "version": "3",
    "networks": {
        "traffic_network": {
            "driver": "bridge"
        },
        "aggregator_network": {
            "driver": "bridge"
        },
        "external_network": {
            "driver": "bridge"
        }
    },
    "services": {
        "trafficapi": {
            "container_name": "TrafficAPI",
            "build": {
                "context": "./traffic",
                "dockerfile": "./Dockerfile"
            },
            "networks": [
                "traffic_network"
            ],
            "ports": [
                "8000:8000" #TODO: Traffic API should be a user parameter
            ],
            "environment": [
                "PYTHONUNBUFFERED=1"
            ]
        },
        "event_manager": {
            "container_name": "event_manager",
            "build": {
                "context": "./event_manager",
                "dockerfile": "./Dockerfile"
            },
            "networks": [
                "external_network"
            ],
            "environment": [
                "SERVICE_API_URL=http://host.docker.internal:7000/routing/post_request_type1/",
                "DATAFEV_INIT_URL=http://host.docker.internal:9004/datafev_init/",
                "DATAFEV_GET_REQUEST_COUNTER_URL=http://host.docker.internal:9004/get_request_counter/",
                "DATAFEV_SYNCHRONIZE_URL=http://host.docker.internal:9004/synchronize/",
                "PYTHONUNBUFFERED=1"
            ],
            "depends_on": [
                "datafev"
            ]
        },
        "datafev": {
            "container_name": "datafev",
            "build": {
                "context": "./datafev",
                "dockerfile": "./Dockerfile"
            },
            "networks": [
                "external_network"
            ],
            "ports": [
                "9004:9004" #TODO: datafev port should be a user parameter
            ],
            "environment": [
                "PYTHONUNBUFFERED=1"
            ]
        }
    }
}

for service in services:
    compose_config["services"][service["container_name"]] = service

# Save the YAML configuration to the output file
with open(output_file_path, 'w') as f:
    yaml.dump(compose_config, f)