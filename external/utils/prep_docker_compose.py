import os
import pandas as pd
import yaml

# Get the current directory of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the path to input.xlsx
excel_file_path = os.path.join(script_directory, 'input.xlsx')

# Read the Excel file
cluster_df = pd.read_excel(excel_file_path, sheet_name="SocketInfoCluster")
other_df = pd.read_excel(excel_file_path, sheet_name="SocketInfoOther")
other_df = other_df.set_index('service_name')

# Construct the path to save the generated docker-compose.yml
output_file_path = os.path.join(script_directory, '../docker-compose.yml')

services = []

for _, row in cluster_df.iterrows():
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
                f"DATAFEV_CHARGER_SELECTION_URL=http://host.docker.internal:{other_df.at['datafev', 'port_number']}/charger_selection/",
                f"DATAFEV_RESERVATION_URL=http://host.docker.internal:{other_df.at['datafev', 'port_number']}/reservation/"
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
                f"{other_df.at['trafficapi', 'port_number']}:{other_df.at['trafficapi', 'port_number']}"
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
                f"DATAFEV_INIT_URL=http://host.docker.internal:{other_df.at['datafev', 'port_number']}/datafev_init/",
                f"DATAFEV_GET_REQUEST_COUNTER_URL=http://host.docker.internal:{other_df.at['datafev', 'port_number']}/get_request_counter/",
                f"DATAFEV_SYNCHRONIZE_URL=http://host.docker.internal:{other_df.at['datafev', 'port_number']}/synchronize/",
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
                f"{other_df.at['datafev', 'port_number']}:{other_df.at['datafev', 'port_number']}"
            ],
            "environment": [
                "MYSQL_HOST=mysql",
                "MYSQL_PORT=3306",
                "MYSQL_USER=root",
                "MYSQL_PASSWORD=root",
                "MYSQL_DB=mydatabase",
                "PYTHONUNBUFFERED=1"
            ],
            "volumes": [
                "/C/Users/aytugy/Documents/workspace/evrich/external/datafev/outputs:/app/outputs"
            ]
        },
        "mysql": {
            "image": "mysql:latest",
            "container_name": "mysql",
            "environment": [
                "MYSQL_ROOT_PASSWORD=root",
                "MYSQL_DATABASE=mydatabase"
            ],
            "ports": [
                f"{other_df.at['mysql', 'port_number']}:{other_df.at['mysql', 'port_number']}"
            ],
            "networks": [
                "external_network"
            ]
        }
    }
}

for service in services:
    compose_config["services"][service["container_name"]] = service

# Save the YAML configuration to the output file
with open(output_file_path, 'w') as f:
    yaml.dump(compose_config, f)