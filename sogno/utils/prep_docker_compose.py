import os
import pandas as pd
import yaml

# Get the current directory of the script
script_directory = os.path.dirname(os.path.abspath(__file__))

# Construct the path to input.xlsx
excel_file_path = os.path.join(script_directory, "./input.xlsx")

# Read the Excel file and get cluster and others dataframes
cluster_df = pd.read_excel(excel_file_path, sheet_name="SocketInfoCluster")
other_df = pd.read_excel(excel_file_path, sheet_name="SocketInfoOther")
other_df = other_df.set_index("service_name")

# Construct the path to save the generated docker-compose.yml
output_file_path = os.path.join(script_directory, "../docker-compose.yml")


# Function to get AGGREGATOR_AVAILABILITY_URL based on cluster_id
def get_aggregator_availability_url(cluster_id):
    matching_row = cluster_df[
        cluster_df["cluster_id"] == cluster_id
    ]  # Find the rows in the Excel input file (DataFrame) where the cluster_id column matches the provided cluster_id value
    if not matching_row.empty:  # If a matching row is found
        port_number = matching_row.iloc[0]["port_number"]
        return f"http://aggregator_{cluster_id}:{port_number}/availability/"
    return ""


# Function to get AGGREGATOR_SCHEDULE_URL based on cluster_id
def get_aggregator_schedule_url(cluster_id):
    matching_row = cluster_df[
        cluster_df["cluster_id"] == cluster_id
    ]  # Find the rows in the Excel input file (DataFrame) where the cluster_id column matches the provided cluster_id value
    if not matching_row.empty:  # If a matching row is found
        port_number = matching_row.iloc[0]["port_number"]
        return f"http://aggregator_{cluster_id}:{port_number}/schedule/"
    return ""


# Convert cluster_id to strings to ensure consistency
cluster_df["cluster_id"] = cluster_df["cluster_id"].apply(lambda x: str(x))

connector_list = cluster_df["cluster_id"].tolist()  # list of container ids in strings

compose_config = {
    "version": "3",
    "networks": {
        "sogno_network": {"driver": "bridge"},
        "external_external_network": {"external": True},
    },
    "services": {
        "gatewaymqtt": {
            "image": "toke/mosquitto",
            "container_name": "broker",
            "expose": [f"{other_df.at['mqtt_broker', 'port_number']}"],
            "ports": [
                f"{other_df.at['mqtt_broker', 'port_number']}:{other_df.at['mqtt_broker', 'port_number']}"
            ],
            "restart": "unless-stopped",
            "networks": ["sogno_network"],
        },
        "api": {
            "container_name": "ServiceAPI",
            "build": {"context": "./api", "dockerfile": "./Dockerfile"},
            "networks": ["sogno_network", "external_external_network"],
            "ports": [
                f"{other_df.at['service_api', 'port_number']}:{other_df.at['service_api', 'port_number']}"
            ],
        },
        "coordinator": {
            "container_name": "coordinator",
            "build": {"context": "./coordinator", "dockerfile": "./Dockerfile"},
            "networks": ["sogno_network", "external_external_network"],
            "environment": [
                f"TRAFFIC_URL=http://trafficapi:{other_df.at['trafficapi', 'port_number']}/trafficforecast/",
                "PYTHONUNBUFFERED=1",
            ],
        },
        "routingalgorithm": {
            "container_name": "Optimizer",
            "build": {"context": "./optimizer", "dockerfile": "./Dockerfile"},
            "networks": ["sogno_network"],
            "environment": ["PYTHONUNBUFFERED=1"],
        },
    },
}

for connector in connector_list:
    service_name = f"connector_{connector.lower()}"
    aggregator_availability_url = get_aggregator_availability_url(connector)
    aggregator_schedule_url = get_aggregator_schedule_url(connector)

    if aggregator_availability_url:
        compose_config["services"][service_name] = {
            "container_name": f"connector_{connector}",
            "build": {"context": f"./connector", "dockerfile": "./Dockerfile"},
            "networks": ["sogno_network", "external_external_network"],
            "depends_on": ["coordinator"],
            "environment": [
                f"CONNECTOR_ID=aggregator_{connector}",
                f"AGGREGATOR_AVAILABILITY_URL={aggregator_availability_url}",
                f"AGGREGATOR_SCHEDULE_URL={aggregator_schedule_url}",
                f"REQUEST_TOPIC=availability/request/aggregator_{connector}",
                f"RESPONSE_TOPIC=availability/response/aggregator_{connector}",
                "PYTHONUNBUFFERED=1",
            ],
        }


# Save the YAML configuration to the output file
with open(output_file_path, "w") as f:
    yaml.dump(compose_config, f)
