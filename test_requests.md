#Pick one of the following jsons to send a RoutingRequest to the evrich service API

{
  "vehicle_id": "ev001",
  "vehicle_model": "model1",
  "battery_energy_capacity": 40,
  "battery_power_charging": 11,
  "battery_power_discharge": 11,
  "start_SOC": 0.4,
  "start_time": 1671868800.0,
  "start_location": "loc0",
  "sojourn_location_center": "locX",
  "sojourn_location_radius": 200,
  "sojourn_period": 3600,
  "demand_target_SOC": 1,
  "demand_v2g_allowance": 0
}

{
  "vehicle_id": "ev002",
  "vehicle_model": "model2",
  "battery_energy_capacity": 40,
  "battery_power_charging": 55,
  "battery_power_discharge": 55,
  "start_SOC": 0.4,
  "start_time": 1671868800.0,
  "start_location": "loc0",
  "sojourn_location_center": "locX",
  "sojourn_location_radius": 200,
  "sojourn_period": 3600,
  "demand_target_SOC": 0.6,
  "demand_v2g_allowance": 5
}
