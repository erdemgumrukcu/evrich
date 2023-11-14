from typing import Dict, Any
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta
from data_handling.pricing_rule import idp
from data_handling.cluster import ChargerCluster
from data_handling.multi_cluster import MultiClusterSystem
from data_handling.fleet import EVFleet

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
    global clusters_dict, capacities_dict, service_fleet, fleet, tariff, sim_parameters, system, ts

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
    # Multi cluster system of the simulation
    system = MultiClusterSystem("multicluster")
    service_fleet = EVFleet("fleet", service_fleet_parameters, sim_parameters['sim_horizon'], service=True)
    fleet = EVFleet("fleet", fleet_parameters, sim_parameters['sim_horizon'], service=False)

    # Iterate through input_clusters_dict
    for key, df in clusters_dict.items():
        charger_cluster = ChargerCluster(key, df)
        system.add_cc(charger_cluster)
        charger_cluster.enter_power_limits(sim_parameters['sim_start'], sim_parameters['sim_end'], sim_parameters['sim_step'], capacities_dict.get(key))
    system.enter_tou_price(tariff, sim_parameters['sim_step'])

    '''
    # Reserve chargers for the fleet, which are not using the service
    for ev in fleet.objects.values():
        cluster_id = ev.cluster_target
        charger_id = ev.charger_target
        cluster = system.clusters[cluster_id]
        selected_charger = cluster.chargers[charger_id]
        res_from = ev.t_arr_real
        res_until = ev.t_dep_real
        cluster.reserve(res_from, res_until, ev, selected_charger)
    '''
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
    
    available_chargers_dict = system.clusters[cluster_id].query_availability(start, end, step)
    
    # If there are no available chargers return None
    if available_chargers_dict.empty:
        print("Response sent to Aggregator.")
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
        schedule = system.clusters[cluster_id].query_actual_schedule(start, end, step)
        upper_bound = system.clusters[cluster_id].upper_limit[start:end]
        lower_bound = system.clusters[cluster_id].lower_limit[start:end]
        tou_tariff = system.tou_price

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

# Datafev reservation request counter to be used for timestamp-synchronization with event manager
datafev_request_counter = 0

@app.post("/reservation/")
async def receive_reservation(item: ReservationData):

    global datafev_request_counter

    print('Reservation data received successfully.')

    # Update objects and their schedule
    cluster_id = item.Aggregator.replace("aggregator_", "")
    selected_cluster = system.clusters[cluster_id]
    selected_charger = selected_cluster.chargers[item.Charger]
    # Extract and convert the first and last keys to datetime objects to obtain res_from and res_until
    res_from = datetime.strptime(next(iter(item.P_Schedule)), "%Y-%m-%d %H:%M:%S")
    res_until = datetime.strptime(next(reversed(item.P_Schedule)), "%Y-%m-%d %H:%M:%S")
    ev = service_fleet.objects[item.VehicleID] 
    # Reserve selected charger in the cluster
    selected_cluster.reserve(res_from, res_until, ev, selected_charger)
    print('Reservation made.')
    # Add 1 to datafev reservation request counter
    datafev_request_counter += 1
    # TODO: Maybe there will be cases that EV are not coming/coming lately(traffic independent reasons, maybe personal driver behaviour) 
    # even they are told so, incoming_at should be changed/upgraded in the future -- same for outgoing_at
    service_fleet.incoming_at[res_from].append(ev)
    service_fleet.outgoing_at[res_until].append(ev)
    p_schedule_str = item.P_Schedule
    s_schedule_str = item.S_Schedule
    # Convert strings to datetime objects
    p_schedule = {datetime.strptime(key, '%Y-%m-%d %H:%M:%S'): value for key, value in p_schedule_str.items()}
    s_schedule = {datetime.strptime(key, '%Y-%m-%d %H:%M:%S'): value for key, value in s_schedule_str.items()}
    # Setting schedule for selected charger
    selected_charger.set_schedule(ts, pd.Series(p_schedule), pd.Series(s_schedule))

    # Get the first and the last key of s_schedule to initialize estimated/real arrival/departure datetimes and SoCs of EV
    # TODO: This estimated and real may vary, an approach should be developed here accordingly
    first_item = next(iter(s_schedule.items()))
    first_key = first_item[0]
    ev.t_arr_est = first_key
    ev.t_arr_real = ev.t_arr_est
    ev.soc_arr_est = s_schedule[first_key]
    ev.soc_arr_real = ev.soc_arr_est
    ev.soc[first_key] = s_schedule[first_key]
    last_key = list(s_schedule.keys())[-1]
    ev.t_dep_est = last_key
    ev.t_dep_real = ev.t_dep_est

    return {"message": "Reservation data received successfully."}


@app.get("/get_request_counter/")
async def send_request_counter():
    global datafev_request_counter
    return {"value": datafev_request_counter}


class SynchronizeRequest(BaseModel):
    ts: datetime
    sim_step: float


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
            available_chargers_dict = system.clusters[cluster_id].query_availability(ev.t_arr_real, ev.t_dep_real, step)
            # If there are no available chargers return None
            if available_chargers_dict.empty:
                print("There are no available chargers in the cluster",cluster_id, "for EV", ev.vehicle_id, ". EV", ev.vehicle_id, "could not be admitted to the system.")
                # TODO: Re-routing
            else:
                available_chargers=(pd.DataFrame(available_chargers_dict))
                parking_duration = ev.t_dep_real - ev.t_arr_real
                charging_demand_limited_by_target_SOC = (ev.soc_tar_at_t_dep_est - ev.soc_arr_real) * ev.bCapacity
                charging_demand_limited_by_pow_limit = ev.p_max_ch * parking_duration.total_seconds()
                ev_energy_demand = min(charging_demand_limited_by_target_SOC, charging_demand_limited_by_pow_limit)
                energy_supply_by_chargers = available_chargers["max p_ch"] * parking_duration.total_seconds()
                chargers_with_sufficient_supply_rating = energy_supply_by_chargers[energy_supply_by_chargers >= ev_energy_demand]
                if len(chargers_with_sufficient_supply_rating):
                    selected_charger_id=chargers_with_sufficient_supply_rating.idxmin()
                else:
                    selected_charger_id=available_chargers["max p_ch"].idxmax()
                cluster = system.clusters[cluster_id]
                selected_charger = cluster.chargers[selected_charger_id]
                # Reserve charger for the EV arrived in ts
                cluster.reserve(ev.t_arr_real, ev.t_dep_real, ev, selected_charger)
                fleet.incoming_at[ev.t_arr_real].append(ev)
                fleet.outgoing_at[ev.t_dep_real].append(ev)
                print("EV", ev.vehicle_id, "is connected to charger", selected_charger_id, "in cluster", cluster_id, '.')
                # Calculating p_schedule and s_schedule
                # Create and update p_schedule and s_schedule for the EV
                time_index = pd.date_range(ev.t_arr_real, ev.t_dep_real, freq=step)
                p_schedule = pd.Series(0, index=time_index)
                s_schedule = pd.Series(ev.soc_arr_real, index=time_index)
                for i, ts_ in enumerate(time_index):
                    # Calculate the charging power
                    charging_power = min(selected_charger.p_max_ch, ev.p_max_ch)

                    # Update p_schedule with charging power
                    p_schedule.at[ts_] = charging_power

                    # Update s_schedule with SOC changes due to charging
                    if i > 0:  # Skip the first step for s_schedule.at[ts_] since it's already set
                        soc_changes = charging_power / (ev.bCapacity * 3600)  # Assuming bCapacity is in kWh
                        s_schedule.at[ts_] = s_schedule.at[ts_ - step] + soc_changes
                    else:
                        s_schedule.at[ts_] = ev.soc_arr_real

                    # Check if desired SOC is reached and stop charging
                    if ts_ == ev.t_dep_real and s_schedule.at[ts_] >= ev.soc_tar_at_t_dep_est:
                        # Stop charging beyond the desired SOC
                        p_schedule.at[ts_:] = 0
                        break  # Break the loop as charging is complete for this EV

                selected_charger.set_schedule(ts, p_schedule, s_schedule)

    #####################################################################################################################################        

    #####################################################################################################################################
    # Adding arriving and leaving EV to the dataset of the system, connecting it to the assigned charger, and charging
    #####################################################################################################################################
    
    # Arriving EVs
    # For EV Fleet, which are not using the service
    incoming_vehicles = fleet.incoming_vehicles_at(ts)
    for ev in incoming_vehicles:
        #TODO: Future work: There might be casses that reserved chargers are still occupied and available, then system must use a re-routing routine
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
    for ev in incoming_vehicles_ser:
        #TODO: Future work: There might be casses that reserved chargers are still occupied and available, then system must use a re-routing routine
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

    # Departing EVs
    # For EV Fleet, which are not using the service
    outgoing_vehicles = fleet.outgoing_vehicles_at(ts)
    for ev in outgoing_vehicles:
        if ev.admitted == True:
            cu = ev.connected_cu
            cu.disconnect(ts)
            cc = ev.connected_cc
            cc.unreserve(ts, ev.reservation_id)
            cc.enter_data_of_outgoing_vehicle(ts, ev)
    # For EV Fleet using the service
    outgoing_vehicles_ser = service_fleet.outgoing_vehicles_at(ts)
    for ev in outgoing_vehicles_ser:
        if ev.admitted == True:
            cu = ev.connected_cu
            cu.disconnect(ts)
            cc = ev.connected_cc
            cc.unreserve(ts, ev.reservation_id)
            cc.enter_data_of_outgoing_vehicle(ts, ev)

    # Charging
    for cc_id in system.clusters.keys():
        cluster = system.clusters[cc_id]
        if cluster.query_actual_occupation(ts) > 0:
            # The cluster includes connected EVs
            for cu_id in system.clusters[cc_id].chargers.keys():
                cu = system.clusters[cc_id].chargers[cu_id]
                if cu.connected_ev != None:
                    cu.supply(ts, step, cu.schedule_pow[cu.active_schedule_instance][ts])

    #####################################################################################################################################

    return {"message": "Synchronization done"}