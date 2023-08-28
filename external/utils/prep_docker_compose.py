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
            "container_name": f"aggregator{row['cluster_id']}",
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
                "PYTHONUNBUFFERED=1"
            ],
            "ports": [
                f"{row['port_number']}:{row['port_number']}"
            ],
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
        }
    }
}

for service in services:
    compose_config["services"][service["container_name"]] = service

# Save the YAML configuration to the output file
with open(output_file_path, 'w') as f:
    yaml.dump(compose_config, f)