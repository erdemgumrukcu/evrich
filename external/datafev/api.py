from typing import Dict, Any
import os
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
import pymysql
from sqlalchemy import create_engine
from data_handling.pricing_rule import idp
from data_handling.cluster import ChargerCluster
from data_handling.multi_cluster import MultiClusterSystem
from data_handling.fleet import EVFleet

'''
def reset_mysql_database(host, user, password, db_name):
    """
    Resets a MySQL database by dropping it if it exists and creating a new one.

    Parameters
    ----------
    host : str
        The host address of the MySQL server.
    user : str
        The username to authenticate to the MySQL server.
    password : str
        The password to authenticate to the MySQL server.
    db_name : str
        The name of the MySQL database to be reset.

    Returns
    -------
    None

    Raises
    ------
    pymysql.err.OperationalError
        If there is an issue with MySQL operations.

    Example
    -------
    >>> reset_mysql_database('localhost', 'root', 'root', 'mydatabase')
    """

    # Connect to MySQL
    connection = pymysql.connect(
        host=host,
        user=user,
        password=password,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        with connection.cursor() as cursor:
            # Drop the database if it exists
            cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
            # Create a new database
            cursor.execute(f"CREATE DATABASE {db_name}")
    finally:
        connection.close()

# Get environment MySQL variables
mysql_host = os.environ.get('MYSQL_HOST')
mysql_port = os.environ.get('MYSQL_PORT')
mysql_user = os.environ.get('MYSQL_USER')
mysql_password = os.environ.get('MYSQL_PASSWORD')
mysql_database = os.environ.get('MYSQL_DB')

# Reset MySQL Database for re-usage
reset_mysql_database(mysql_host, mysql_user, mysql_password, mysql_database)
'''
'''
# Define the date and time strings
date_string1 = "01/08/2022 07:05:00"
date_string2 = "01/08/2022 07:10:00"
date_string3 = "01/08/2022 07:15:00"
date_string4 = "01/08/2022 07:20:00"
date_string5 = "01/08/2022 07:25:00"
date_string6 = "01/08/2022 07:30:00"
date_string7 = "01/08/2022 07:35:00"
date_string8 = "01/08/2022 07:40:00"

# Create datetime objects from the strings
dt1 = datetime.strptime(date_string1, "%m/%d/%Y %H:%M:%S")
dt2 = datetime.strptime(date_string2, "%m/%d/%Y %H:%M:%S")
dt3 = datetime.strptime(date_string3, "%m/%d/%Y %H:%M:%S")
dt4 = datetime.strptime(date_string4, "%m/%d/%Y %H:%M:%S")
dt5 = datetime.strptime(date_string5, "%m/%d/%Y %H:%M:%S")
dt6 = datetime.strptime(date_string6, "%m/%d/%Y %H:%M:%S")
dt7 = datetime.strptime(date_string7, "%m/%d/%Y %H:%M:%S")
dt8 = datetime.strptime(date_string8, "%m/%d/%Y %H:%M:%S")

# Get the Unix timestamps
timestamp1 = int(dt1.timestamp())
timestamp2 = int(dt2.timestamp())
timestamp3 = int(dt3.timestamp())
timestamp4 = int(dt4.timestamp())
timestamp5 = int(dt5.timestamp())
timestamp6 = int(dt6.timestamp())
timestamp7 = int(dt7.timestamp())
timestamp8 = int(dt8.timestamp())

print("Unix timestamp for 01/08/2022 07:05:00:", timestamp1)
print("Unix timestamp for 01/08/2022 07:10:00:", timestamp2)
print("Unix timestamp for 01/08/2022 07:15:00:", timestamp3)
print("Unix timestamp for 01/08/2022 07:20:00:", timestamp4)
print("Unix timestamp for 01/08/2022 07:25:00:", timestamp5)
print("Unix timestamp for 01/08/2022 07:30:00:", timestamp6)
print("Unix timestamp for 01/08/2022 07:35:00:", timestamp7)
print("Unix timestamp for 01/08/2022 07:40:00:", timestamp8)
'''
app = FastAPI()

# Define a Pydantic model to represent the data datafev will receive
class DatafevInitData(BaseModel):
    input_clusters_dict: Dict[str, Dict[str, Any]]
    input_capacities_dict: Dict[str, Dict[str, Any]]
    input_service_fleet: Dict[str, Any]
    input_fleet: Dict[str, Any]
    tariff_as_dataframe: Dict[str, Any]
    sim_parameters: Dict[str, Any]

# Store received data in these variables
clusters_dict = {}
capacities_dict = {}
fleet_parameters = None
service_fleet_parameters = None
tariff = None
sim_parameters = {}
ts = None

@app.post("/datafev_init/")
async def receive_datafev_init(data: DatafevInitData):
    global clusters_dict, capacities_dict, service_fleet, fleet, tariff, sim_parameters, mcsystem, ts

    print('Datafev initialization data received successfully.')

    # Extract data from the received JSON and convert them into proper object types
    # Cluster dictionary
    clusters_dict = {key: pd.DataFrame(data['data'], columns=data['columns']) for key, data in data.input_clusters_dict.items()}
    # Capacities dictionary
    # Create Pandas DataFrames from the capacities data dictionary while converting and rounding datetime strings
    for key, sub_dict in data.input_capacities_dict.items():
        # Convert the datetime strings to datetime objects and round them to the nearest second
        sub_dict['data'] = [[pd.to_datetime(dt_str).round('S'), lb, ub] for dt_str, lb, ub in sub_dict['data']]
        # Create the Pandas DataFrame
        df = pd.DataFrame(sub_dict['data'], index=sub_dict['index'], columns=sub_dict['columns'])
        capacities_dict[key] = df
    # Sim parameters dictionary
    # Convert the datetime strings in sim_parameters to datetime objects and round them
    sim_parameters['sim_start'] = datetime.strptime(data.sim_parameters['sim_start'], '%Y-%m-%d %H:%M:%S')
    ts = sim_parameters['sim_start']
    sim_parameters['sim_end'] = datetime.strptime(data.sim_parameters['sim_end'], '%Y-%m-%d %H:%M:%S')
    sim_step_str = data.sim_parameters['sim_step']
    hours, minutes, seconds = map(int, sim_step_str.split(':'))
    sim_parameters['sim_step'] = timedelta(hours=hours, minutes=minutes, seconds=seconds)
    sim_parameters['sim_horizon'] = [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in data.sim_parameters['sim_horizon']]
    # Fleet pandas Dataframe
    service_fleet_parameters = pd.DataFrame(data.input_service_fleet['data'], index=data.input_service_fleet['index'], columns=data.input_service_fleet['columns'])
    fleet_parameters = pd.DataFrame(data.input_fleet['data'], index=data.input_fleet['index'], columns=data.input_fleet['columns'])
    # Tariff pandas Series
    tariff_df = pd.DataFrame(data.tariff_as_dataframe['data'], index=data.tariff_as_dataframe['index'], columns=data.tariff_as_dataframe['columns'])
    tariff_df.index = pd.to_datetime(tariff_df.index)
    tariff = tariff_df['tariff_data']

    # Initialize datafev objects
    # Multi cluster mcsystem of the simulation
    mcsystem = MultiClusterSystem("multicluster")
    service_fleet = EVFleet("fleet", service_fleet_parameters, sim_parameters['sim_horizon'], service=True)
    fleet = EVFleet("fleet", fleet_parameters, sim_parameters['sim_horizon'], service=False)

    # Iterate through input_clusters_dict
    for key, df in clusters_dict.items():
        charger_cluster = ChargerCluster(key, df)
        mcsystem.add_cc(charger_cluster)
        charger_cluster.enter_power_limits(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], capacities_dict.get(key))
    mcsystem.enter_tou_price(tariff, sim_parameters['sim_step'])

    return {"message": "Datafev initialization data received successfully."}


class ChargerSelectionRequest(BaseModel):
    estimate_arrival_time: float
    estimate_departure_time:float
    query_resolution: int
    energy_demand: float
    cluster_id: str

@app.post("/charger_selection/")
async def request_charging_offer(item: ChargerSelectionRequest):
    
    # Handle the request once MQTT communication is done
    start=datetime.fromtimestamp(item.estimate_arrival_time)
    end  =datetime.fromtimestamp(item.estimate_departure_time)
    step =timedelta(seconds=item.query_resolution)
    estimate_parking_period=pd.date_range(start=start,
                                        end=end-step,
                                        freq=step)
    cluster_id = item.cluster_id
    ###########################################################################
    ###########################################################################
    #Charger selection algorithm
    
    available_chargers_dict = mcsystem.clusters[cluster_id].query_availability(start, end, step)
    
    # If there are no available chargers return None
    if available_chargers_dict.empty:
        print("There are no available chargers in this cluster. Response sent to Aggregator.")
        return None

    else:
        available_chargers=(pd.DataFrame(available_chargers_dict))
        
        parking_duration=item.estimate_departure_time-item.estimate_arrival_time
        ev_energy_demand=item.energy_demand
        
        energy_supply_by_chargers=available_chargers["max p_ch"]*parking_duration
        
        chargers_with_sufficient_supply_rating=energy_supply_by_chargers[energy_supply_by_chargers>=ev_energy_demand]
        if len(chargers_with_sufficient_supply_rating):
            selected_charger_id=chargers_with_sufficient_supply_rating.idxmin()
        else:
            selected_charger_id=available_chargers["max p_ch"].idxmax()

        ###########################################################################
        ###########################################################################
        
        ###########################################################################
        #Dynamic pricing algorithm
        
        f_discount     =0.0
        f_markup       =0.05
        arbitrage_coeff=0.1
        schedule = mcsystem.clusters[cluster_id].query_actual_schedule(start, end, step)
        upper_bound = mcsystem.clusters[cluster_id].upper_limit[start:end]
        lower_bound = mcsystem.clusters[cluster_id].lower_limit[start:end]
        tou_tariff = mcsystem.tou_price

        # TODO: to be given under XLSX input
        #f_discount : global parameter
        #f_markup: global parameter
        #arbitrage_coef: global parameter
            
        dlp=idp(schedule, upper_bound, lower_bound, tou_tariff, f_discount, f_markup)  
        
        ###########################################################################
        ###########################################################################
        
        p_ch=available_chargers.loc[selected_charger_id,"max p_ch"]
        p_ds=available_chargers.loc[selected_charger_id,"max p_ch"]
        
        response={}
        response['charger_id']=selected_charger_id       
        response['p_ch_max']= float(p_ch) 
        response['p_ds_max']= float(p_ds)
        response['max_energy_supply']=min(p_ch*parking_duration,ev_energy_demand) #kWs
        response['dps_g2v'] = dict([(k, dlp[k]) for k in sorted(dlp.keys())])
        response['dps_v2g'] = dict([(k, dlp[k] * (1 - arbitrage_coeff)) for k in sorted(dlp.keys())])
        
        # ###########################################################################
        
        print("Response sent to Aggregator.")
        return response


# Define a Pydantic model to represent the data datafev will receive
class ReservationData(BaseModel):
    Aggregator: str
    Charger: str
    P_Schedule: Dict[str, float]
    S_Schedule: Dict[str, float]
    VehicleID: str
    ArrivalTime: float

# Datafev reservation request counter to be used for timestamp-synchronization with event manager
datafev_request_counter = 0

@app.post("/reservation/")
async def receive_reservation(item: ReservationData):

    global datafev_request_counter

    print('Reservation data received successfully.')

    # Update objects and their schedule
    cluster_id = item.Aggregator.replace("aggregator_", "")
    selected_cluster = mcsystem.clusters[cluster_id]
    selected_charger = selected_cluster.chargers[item.Charger]
    # Extract and convert the first and last keys to datetime objects to obtain res_from and res_until
    res_from = datetime.strptime(next(iter(item.P_Schedule)), "%Y-%m-%d %H:%M:%S")
    res_until = datetime.strptime(next(reversed(item.P_Schedule)), "%Y-%m-%d %H:%M:%S")
    ev = service_fleet.objects[item.VehicleID] 

    # TODO: Maybe there will be cases that EV are not coming/coming lately(traffic independent reasons, maybe personal driver behaviour) 
    # even they are told so, incoming_at should be changed/upgraded in the future -- same for outgoing_at
    arrival_time = datetime.fromtimestamp(item.ArrivalTime)
    service_fleet.incoming_at[arrival_time].append(ev)
    service_fleet.outgoing_at[res_until+sim_parameters['sim_step']].append(ev)
    p_schedule_str = item.P_Schedule
    s_schedule_str = item.S_Schedule
    # Convert strings to datetime objects
    p_schedule = {datetime.strptime(key, '%Y-%m-%d %H:%M:%S'): value for key, value in p_schedule_str.items()}
    s_schedule = {datetime.strptime(key, '%Y-%m-%d %H:%M:%S'): value for key, value in s_schedule_str.items()}
    # Reserve selected charger in the cluster and setting schedule for selected charger
    selected_cluster.reserve(ts, res_from, res_until+sim_parameters['sim_step'], ev, selected_charger,pd.Series(p_schedule), pd.Series(s_schedule))

    # Get the first and the last key of s_schedule to initialize estimated/real arrival/departure datetimes and SoCs of EV
    # TODO: This estimated and real may vary, an approach should be developed here accordingly
    first_item = next(iter(s_schedule.items()))
    first_key = first_item[0]
    ev.t_arr_est = first_key
    ev.t_arr_real = ev.t_arr_est
    ev.soc_arr_est = s_schedule[arrival_time]
    ev.soc_arr_real = ev.soc_arr_est
    ev.soc[arrival_time] = s_schedule[arrival_time]
    last_key = list(s_schedule.keys())[-1]
    ev.t_dep_est = last_key
    ev.t_dep_real = ev.t_dep_est
    # Add 1 to datafev reservation request counter
    datafev_request_counter += 1

    return {"message": "Reservation data received successfully."}


@app.get("/get_request_counter/")
async def send_request_counter():
    global datafev_request_counter
    return {"value": datafev_request_counter}


class SynchronizeRequest(BaseModel):
    ts: datetime
    sim_step: float
# TODO: Do we need sim_step here? Is it equal to sim_parameters['sim_step'], if yes we don't

@app.post("/synchronize/")
async def synchronizer(charge_request: SynchronizeRequest):
    global datafev_request_counter, ts
    # Parse the received string back into a datetime object, update timestamp in datafev
    ts = charge_request.ts
    sim_step_seconds = charge_request.sim_step
    step = timedelta(seconds=sim_step_seconds)
    # Reset datafev reservation request counter for the next timestamp
    datafev_request_counter = 0
    
    ###################################################################################################################################
    # Charger selection and charging schedule algorithm for the e-vehicles, which are not using the Service
    ###################################################################################################################################
    for ev in fleet.objects.values():
        if ev.t_arr_real == ts:
            cluster_id = ev.cluster_target
            available_chargers_dict = mcsystem.clusters[cluster_id].query_availability(ev.t_arr_real, ev.t_dep_real, step)

            if available_chargers_dict.empty:
                print(f"There are no available chargers in the cluster {cluster_id} for EV {ev.vehicle_id}. EV {ev.vehicle_id} could not be admitted to the Multi-Cluster-System.")
                # TODO: Re-routing
            else:
                available_chargers = pd.DataFrame(available_chargers_dict)
                parking_duration = ev.t_dep_real - ev.t_arr_real
                charging_demand_limited_by_target_SOC = (ev.soc_tar_at_t_dep_est - ev.soc_arr_real) * ev.bCapacity
                charging_demand_limited_by_pow_limit = ev.p_max_ch * parking_duration.total_seconds()
                ev_energy_demand = min(charging_demand_limited_by_target_SOC, charging_demand_limited_by_pow_limit)
                energy_supply_by_chargers = available_chargers["max p_ch"] * parking_duration.total_seconds()
                chargers_with_sufficient_supply_rating = energy_supply_by_chargers[energy_supply_by_chargers >= ev_energy_demand]

                if len(chargers_with_sufficient_supply_rating):
                    selected_charger_id = chargers_with_sufficient_supply_rating.idxmin()
                else:
                    selected_charger_id = available_chargers["max p_ch"].idxmax()

                cluster = mcsystem.clusters[cluster_id]
                selected_charger = cluster.chargers[selected_charger_id]

                fleet.incoming_at[ev.t_arr_real].append(ev)
                fleet.outgoing_at[ev.t_dep_real].append(ev)

                # Create and update p_schedule and s_schedule for the EV
                time_index = pd.date_range(ev.t_arr_real, ev.t_dep_real, freq=step)
                p_schedule = pd.Series(0, index=time_index)
                s_schedule = pd.Series(0, index=time_index)
                s_schedule.at[ts - step] = ev.soc_arr_real

                for ts_ in time_index:
                    # Calculate the charging power
                    charging_power = min(selected_charger.p_max_ch, ev.p_max_ch)

                    # Update p_schedule with charging power
                    p_schedule.at[ts_] = charging_power

                    # Update s_schedule with SOC changes due to charging
                    soc_changes = (charging_power / ev.bCapacity) * step.total_seconds()
                    s_schedule.at[ts_] = s_schedule.at[ts_ - step] + soc_changes

                    # Check if desired SOC is reached and stop charging
                    if s_schedule.at[ts_] >= ev.soc_tar_at_t_dep_est:
                        # Stop charging beyond the desired SoC
                        # Calculate energy needed to reach desired SoC level
                        soc_diff = ev.soc_tar_at_t_dep_est - s_schedule.at[ts_-step]
                        energy_diff = soc_diff * ev.bCapacity
                        p_schedule.loc[ts_] = energy_diff / step.total_seconds()
                        p_schedule.loc[ts_+step:] = 0
                        s_schedule.loc[ts_:] = ev.soc_tar_at_t_dep_est
                        break  # Break the loop as charging is complete for this EV           
                
                # Reserve selected charger in the cluster and setting schedule for selected charger
                cluster.reserve(ts, ev.t_arr_real, ev.t_dep_real, ev, selected_charger, p_schedule, s_schedule)
                print(f"EV {ev.vehicle_id} is connected to charger {selected_charger_id} in cluster {cluster_id}.")

    #####################################################################################################################################        

    #####################################################################################################################################
    # Adding arriving and leaving EV to the dataset of the mcsystem, connecting it to the assigned charger, and charging
    #####################################################################################################################################

    # Departing EVs
    # For EV Fleet, which are not using the service
    outgoing_vehicles = fleet.outgoing_vehicles_at(ts)
    for ev in outgoing_vehicles:
        if ev.admitted == True:
            cu = ev.connected_cu
            cu.disconnect(ts)
            cc = ev.connected_cc
            cc.unreserve(ts, ev.reservation_id)
            cc.enter_data_of_outgoing_vehicle(ts, sim_parameters['sim_step'], ev)

    # For EV Fleet using the service
    outgoing_vehicles_ser = service_fleet.outgoing_vehicles_at(ts)
    for ev in outgoing_vehicles_ser:
        if ev.admitted == True:
            cu = ev.connected_cu
            cu.disconnect(ts)
            cc = ev.connected_cc
            cc.unreserve(ts, ev.reservation_id)
            cc.enter_data_of_outgoing_vehicle(ts, sim_parameters['sim_step'], ev)


    # Arriving EVs
    # For EV Fleet, which are not using the service
    incoming_vehicles = fleet.incoming_vehicles_at(ts)
    for ev in incoming_vehicles:
        #TODO: Future work: There might be casses that reserved chargers are still occupied and available, then mcsystem must use a re-routing routine
        # The EV approaches the cluster where it has reservation
        reserved_cluster = ev.reserved_cluster
        reserved_charger = ev.reserved_charger
        # Connect to the reserved charger and enter the data to the cluster dataset
        reserved_charger.connect(ts, ev)
        # Enter the data of the EV to the connection dataset of the cluster
        reserved_cluster.enter_data_of_incoming_vehicle(
            ts, ev, reserved_charger
        )
        ev.admitted = True
    # For EV Fleet using the service
    incoming_vehicles_ser = service_fleet.incoming_vehicles_at(ts)
    # TODO: Future work: For the EVs which are not coming on time(failure of traffic data), we need to assign a new charging schedule and maybe a new charging unit
    for ev in incoming_vehicles_ser:
        #TODO: Future work: There might be cases that reserved chargers are still occupied and not available, then mcsystem must use a re-routing routine
        # The EV approaches the cluster where it has reservation
        reserved_cluster = ev.reserved_cluster
        reserved_charger = ev.reserved_charger
        # Connect to the reserved charger and enter the data to the cluster dataset
        reserved_charger.connect(ts, ev)
        # Enter the data of the EV to the connection dataset of the cluster        
        reserved_cluster.enter_data_of_incoming_vehicle(
            ts, ev, reserved_charger
        )
        ev.admitted = True


    # Charging
    for cc_id in mcsystem.clusters.keys():
        cluster = mcsystem.clusters[cc_id]
        if cluster.query_actual_occupation(ts) > 0:
            # The cluster includes connected EVs
            for cu_id in mcsystem.clusters[cc_id].chargers.keys():
                cu = mcsystem.clusters[cc_id].chargers[cu_id]
                if cu.connected_ev != None:
                    cu.supply(ts, step, cu.schedule_pow[cu.active_schedule_instance][ts])

    '''
    #####################################################################################################################################
    #####################################################################################################################################
    # Data upload to MySQL database
    #####################################################################################################################################

    # Database connection parameters
    db_params = {
        'host': mysql_host,
        'user': mysql_user,
        'password': mysql_password,
        'db': mysql_database,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

    # Open a connection to the database
    engine = create_engine(f"mysql+pymysql://{db_params['user']}:{db_params['password']}@{db_params['host']}/{db_params['db']}")
    
    # EV data
    # For EV Fleet using the service
    for ev_id, ev in service_fleet.objects.items():
        # Generate a unique table name for each EV
        table_name = f"ev_{ev_id}_data"

        if ev.connected_cu is not None: 
            # TODO: In the table of EVs a new entry should be added where values could be 'drive', 'wait' etc. and this way EVs which are not connected to a cu can also be added
            # Fill EV database DataFrame with current values (values at ts)
            ev.databank_df.loc[len(ev.databank_df)] = [ts, ev.soc[ts], ev.g2v[ts], ev.v2g[ts],  ev.admitted]

            # Open a connection to the database
            connection = pymysql.connect(**db_params)

            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    timestamp TIMESTAMP PRIMARY KEY,
                    soc FLOAT,
                    g2v FLOAT,
                    v2g FLOAT,
                    admission BOOL
                )
            """

            with connection.cursor() as cursor:
                cursor.execute(create_table_query)

            # Save DataFrame to the database
            ev.databank_df.to_sql(table_name, con=engine, if_exists='replace', index=False)

            # Commit and close the connection
            connection.commit()
            connection.close()

    # For EV Fleet, which are not using the service
    for ev_id, ev in fleet.objects.items():
        # Generate a unique table name for each EV
        table_name = f"ev_{ev_id}_data"

        if ev.connected_cu is not None:
            # Fill EV database DataFrame with current values (values at ts)
            ev.databank_df.loc[len(ev.databank_df)] = [ts, ev.soc[ts], ev.g2v[ts], ev.v2g[ts],  ev.admitted]

            # Open a connection to the database
            connection = pymysql.connect(**db_params)

            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    timestamp TIMESTAMP PRIMARY KEY,
                    soc FLOAT,
                    g2v FLOAT,
                    v2g FLOAT,
                    admission BOOL
                )
            """

            with connection.cursor() as cursor:
                cursor.execute(create_table_query)

            # Save DataFrame to the database
            ev.databank_df.to_sql(table_name, con=engine, if_exists='replace', index=False)

            # Commit and close the connection
            connection.commit()
            connection.close()
    
    # Create a dictionary to store cluster data DataFrames
    cc_data_dict = {}

    # Charging unit, cluster, and multi-cluster-system data
    for cc_id, cc in mcsystem.clusters.items():
        # Create a dictionary to store charging unit data DataFrames
        cu_data_dict = {}

        for cu_id, cu in mcsystem.clusters[cc_id].chargers.items():
            # Generate a unique table name for each charging unit
            table_name = f"cu_{cu_id}_data"

            if cu.connected_ev is not None:
                # Fill CU database DataFrame with current values (values at ts)
                cu.databank_df.loc[len(cu.databank_df)] = [ts, cu.supplied_power[ts], cu.consumed_power[ts], cu.connected_ev.vehicle_id]
            else:
                # Fill CU database DataFrame with current values (values at ts)
                cu.databank_df.loc[len(cu.databank_df)] = [ts, 0, 0, None]
            # Open a connection to the database
            connection = pymysql.connect(**db_params)

            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    timestamp TIMESTAMP PRIMARY KEY,
                    supplied_power FLOAT,
                    consumed_power FLOAT,
                    connected_ev_id VARCHAR(255)
                )
            """

            # Assign a key to each DataFrame and store it in the dictionary
            cu_data_dict[cu_id] = cu.databank_df.copy()

            with connection.cursor() as cursor:
                cursor.execute(create_table_query)

            # Save DataFrame to the database
            cu.databank_df.to_sql(table_name, con=engine, if_exists='replace', index=False)

            # Commit and close the connection
            connection.commit()
            connection.close()
            
        # Merge charging unit DataFrames into a single DataFrame for cluster database
        cc_table_name = f"cc_{cc_id}_data"
        # Create a dictionary to store cluster data DataFrames
        if cu_data_dict:  # Check if cu_data_dict is not empty before concatenating
            # Merge DataFrames
            cc.databank_df = pd.concat(cu_data_dict.values(), keys=cu_data_dict.keys(), axis=1)
            # Assign a key to each DataFrame and store it in the dictionary
            cc_data_dict[cc_id] = cc.databank_df.copy()
            # Open a connection to the database
            connection = pymysql.connect(**db_params)
            with connection.cursor() as cursor:
                    cursor.execute(create_table_query)
            # Save the merged DataFrame to the database
            cc.databank_df.to_sql(cc_table_name, con=engine, if_exists='replace', index=False)
            # Commit and close the connection
            connection.commit()
            connection.close()
    # Merge cluster DataFrames into a single DataFrame for multi-cluster-system database
    mcsystem_table_name = f"mcsystem_{mcsystem.id}_data"
    if cc_data_dict:  # Check if cc_data_dict is not empty before concatenating
        # Merge DataFrames
        mcsystem.databank_df = pd.concat(cc_data_dict.values(), axis=1)
        # Open a connection to the database
        connection = pymysql.connect(**db_params)
        with connection.cursor() as cursor:
                cursor.execute(create_table_query)
        # Save the merged DataFrame to the database
        mcsystem.databank_df.to_sql(mcsystem_table_name, con=engine, if_exists='replace', index=False)
        # Commit and close the connection
        connection.commit()
        connection.close()
    '''
    # Save datafev XLSX outputs if its the last timestamp of the simulation
    if ts==sim_parameters['sim_end']-sim_parameters['sim_step']:

        mcsystem.export_results_to_excel(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], 'outputs/mcsysytem_output.xlsx')
        mcsystem.visualize_cluster_loading(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], 'outputs/mcsystem_cluster_loading.png')
        mcsystem.visualize_cluster_occupation(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], 'outputs/mcsystem_cluster_occupation.png')

        fleet.export_results_to_excel(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], 'outputs/fleet_output.xlsx')
        service_fleet.export_results_to_excel(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], 'outputs/service_fleet_output.xlsx')

    
    return {"message": "Synchronization done"}