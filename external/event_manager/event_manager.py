import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta
from data_handling.input_parser import parse_standard_xlsx_input
from data_handling.simulation import Simulation
import time


# Simulation parameters
sim_start = datetime(2022, 1, 8, 7)
sim_end = datetime(2022, 1, 8, 12)
sim_length = sim_end - sim_start
sim_step = timedelta(minutes=5)
sim_horizon = [sim_start + t * sim_step for t in range(int(sim_length / sim_step))]
sim_parameters = {'sim_start': sim_start, 'sim_end': sim_end, 'sim_step': sim_step, 'sim_horizon': sim_horizon}

# Get the current directory of the script
abs_path = os.path.dirname(os.path.abspath(__file__))
file_path = "data_handling/input.xlsx"

# Construct the file path for the input XLSX file
abs_input_file_path = os.path.join(abs_path, file_path)

# Parse input from the XLSX input file (TODO: Implement data loading logic here)
input_clusters_dict, input_capacities_dict, input_service_fleet, input_fleet, input_tariff_dict = parse_standard_xlsx_input(file_path=abs_input_file_path)

# Convert the tariff to a DataFrame to include an index
#tariff_as_dataframe = pd.DataFrame({'tariff_data': tou_tariff})

# Get environment variable DATAFEV_INIT_URL
datafev_init_url = os.environ.get('DATAFEV_INIT_URL')
print(datafev_init_url)

# Try to reach datafev (Wait until its ready to receive requests)
# Maximum number of retries
max_retries = 5
retry_delay = 5  # Number of seconds to wait between retries

# Initialize the number of retries
retry_count = 0
connected = False

while not connected and retry_count < max_retries:
    # Serialize the dictionary to JSON
    datafev_data_to_send = {
    "input_clusters_dict": {key: df.to_dict(orient='split') for key, df in input_clusters_dict.items()},
    "input_capacities_dict": {key: df.to_dict(orient='split') for key, df in input_capacities_dict.items()},
    "input_service_fleet": input_service_fleet.to_dict(orient='split'),
    "input_fleet": input_fleet.to_dict(orient='split'),
    "input_tariff_dict": {key: df.to_dict(orient='split') for key, df in input_tariff_dict.items()},
    "sim_parameters": sim_parameters
}
    data_to_send_json = json.dumps(datafev_data_to_send, default=lambda o: str(o) if isinstance(o, (datetime, timedelta)) else None)

    try:
        # Send a POST request to the datafev endpoint
        response = requests.post(datafev_init_url, data=data_to_send_json, headers={"Content-Type": "application/json"})
        
        if response.status_code == 200:
            print("Data for datafev objects' initialization sent successfully.")
            connected = True
        else:
            print("Failed to send data. Retrying...")
    except requests.exceptions.ConnectionError:
        print("Connection to datafev failed. Retrying...")
    
    retry_count += 1
    time.sleep(retry_delay)  # Wait before the next retry

if not connected:
    print(f"Max retry attempts ({max_retries}) reached. Unable to establish a connection to datafev.")
else:
    # Create simulation object
    sim = Simulation(sim_start, sim_end, sim_step, sim_horizon, input_service_fleet)

    print('Simulation object created. Ready to start requesting.')

    # Get environment variable SERVICE_API_URL
    service_API_url = os.environ.get('SERVICE_API_URL')
    # Get environment variables DATAFEV_GET_REQUEST_COUNTER_URL and DATAFEV_CHARGE_URL
    datafev_get_counter_url = os.environ.get('DATAFEV_GET_REQUEST_COUNTER_URL')
    datafev_synchronize_url = os.environ.get('DATAFEV_SYNCHRONIZE_URL')

    # Counters to keep track of the number of requests made and stay synchronized with datafev
    event_manager_request_counter = 0
    datafev_request_counter = 0


    # Start looping in the simulation
    for ts in sim_horizon:
        print("Simulating time step:", ts)
        for index, row in sim.service_fleet.iterrows():
            # If there are reservations to be made at the current timestamp, make service requests for the EVs requesting
            # To compare, convert the "start_time" column from input_service_fleet dataframe to datetime objects
            if (pd.to_datetime(row['start_time'], unit='s')) == ts:
                print("Request to be made for", row['vehicle_id'])
                # Prepare the EV client request data
                ev_client_request = {
                    "vehicle_id": row['vehicle_id'],
                    "vehicle_model": row['vehicle_model'],
                    "battery_energy_capacity": row['battery_capacity_kWh'],
                    "battery_power_charging": row['p_max_ch_kW'],
                    "battery_power_discharge": row['p_max_ds_kW'],
                    "start_SOC": row['start_SoC'],
                    "start_time": row['start_time'],
                    "start_location": row['start_location'],
                    "sojourn_location_center": row['sojourn_location_center'],
                    "sojourn_location_radius": row['sojourn_location_radius'],
                    "sojourn_period": row['sojourn_period'],
                    "demand_target_SOC": row['demand_target_SoC'],
                    "demand_v2g_allowance": row['v2g_allowance_kWh'],
                }
                print("Sending an HTTP request to the service API:", ev_client_request)
                # Increment the counter
                event_manager_request_counter += 1
                response_request = requests.post(service_API_url, json=ev_client_request)
                if response_request.status_code == 200:
                    response_request_data = response_request.json()
                    print("Response from the service API:", response_request_data)
                else:
                    print("Failed to send the request to the service API")
        
        # Receive messages from datafev until the counters match or timeout
        timeout = 60  # Adjust the timeout value as needed
        start_time = time.time()
        while event_manager_request_counter != datafev_request_counter:
            if time.time() - start_time > timeout:
                raise TimeoutError("Timeout waiting for counters to match")
            datafev_request_counter_response = requests.get(datafev_get_counter_url)
            if datafev_request_counter_response.status_code == 200:
                data = datafev_request_counter_response.json()
                datafev_request_counter = data.get("value")
            else:
                print(f"Error: {datafev_request_counter_response.status_code}")

        # Reset counters for the next timestamp
        event_manager_request_counter = 0
        datafev_request_counter = 0


        # Send reset counter post to datafev
        # Convert ts datetime to string using isoformat
        ts_string = ts.isoformat()
        # Convert the timedelta object to total seconds (to able to send)
        sim_step_seconds = sim.step.total_seconds()
        # Send the ts datetime object as part of the JSON payload to datafev for charging the objects in the current
        datafev_charge_response = requests.post(datafev_synchronize_url, json={"ts": ts_string, "sim_step": sim_step_seconds})
        if datafev_charge_response.status_code == 200:
            pass
        else:
            print(f"Error: {datafev_charge_response.status_code}")

        # TODO: Send charge request to datafev, datafev will charge its connected EVs for the curren ts

