"""
Created on Fri Jan 6 09:28:00 2022

@author: egu
"""

from routing_milp import smart_routing
from datetime import datetime, timedelta, timezone
from pyomo.environ import SolverFactory
import paho.mqtt.client as mqtt
import json
import pandas as pd
import os


def on_connect(client, userdata, flags, rc):
    print("Routing microservice connected with result code " + str(rc))
    client.subscribe("routing/request/emo")


def on_message(client, userdata, message):

    # Receive request
    parameters = json.loads(message.payload)
    # print("received request: ", parameters)

    # Parsing inputs for smart routing algorithm
    solver = SolverFactory("glpk")
    opt_step = parameters["opt_step"]  # seconds
    ecap = parameters["ecap"]
    v2gall = parameters["v2gall"]
    arrsoc = parameters["arrsoc"]
    tarsoc = parameters["tarsoc"]
    p_ch = parameters["p_ch"]
    p_ds = parameters["p_ds"]

    crtsoc = tarsoc
    minsoc = 0.0
    maxsoc = 1.0

    opt_horizon_start = parameters["opt_horizon_start"]
    opt_horizon_end = parameters["opt_horizon_end"]
    opt_horizon_daterange = pd.date_range(
        start=datetime.fromtimestamp(opt_horizon_start),
        end=datetime.fromtimestamp(opt_horizon_end),
        freq=timedelta(seconds=opt_step),
    )
    opt_horizon = list(range(len(opt_horizon_daterange)))
    crttime = opt_horizon[-1]

    aggregators = parameters["candidate_chargers"].keys()

    arrtime = {}
    deptime = {}
    g2v_dps = {}
    v2g_dps = {}

    for agg_id in aggregators:

        arrtime[agg_id] = int(
            (parameters["arrtime"][agg_id] - opt_horizon_start) / opt_step
        )
        deptime[agg_id] = int(
            (parameters["deptime"][agg_id] - opt_horizon_start) / opt_step
        )

        g2v_dps[agg_id] = {}
        v2g_dps[agg_id] = {}

        for t in opt_horizon[:-1]:

            ts = opt_horizon_daterange[t]

            Y = str(ts.year).zfill(4)
            M = str(ts.month).zfill(2)
            D = str(ts.day).zfill(2)
            h = str(ts.hour).zfill(2)
            m = str(ts.minute).zfill(2)
            s = str(ts.second).zfill(2)

            ts_in_dicts = Y + "-" + M + "-" + D + "T" + h + ":" + m + ":" + s

            if ts_in_dicts in parameters["dps_g2v"][agg_id].keys():
                g2v_dps[agg_id][t] = parameters["dps_g2v"][agg_id][ts_in_dicts]
                v2g_dps[agg_id][t] = parameters["dps_v2g"][agg_id][ts_in_dicts]
            else:
                g2v_dps[agg_id][t] = 0.0
                v2g_dps[agg_id][t] = 0.0

    # Execution of smart routing algorithm
    p, s, c = smart_routing(
        solver,
        opt_horizon,
        opt_step,
        ecap,
        v2gall,
        tarsoc,
        minsoc,
        maxsoc,
        crtsoc,
        crttime,
        arrtime,
        deptime,
        arrsoc,
        p_ch,
        p_ds,
        g2v_dps,
        v2g_dps,
    )

    # Formatting the outputs
    response_ = {}
    response_["Aggregator"] = c
    response_["Charger"] = parameters["candidate_chargers"][c]
    response_["P_Schedule"] = {}
    response_["S_Schedule"] = {}
    for step in sorted(s.keys()):

        t = int(step)
        ts = opt_horizon_daterange[t]
        time_stamp = str(ts)

        if ts < max(opt_horizon_daterange):
            response_["P_Schedule"][time_stamp] = p[step]
        response_["S_Schedule"][time_stamp] = s[step]

    # Send response
    msg_tosend = json.dumps(response_)
    client.publish("routing/response/emo", msg_tosend)


def on_publish(client, userdata, result):
    print("routing signal returned...")

mqtt_broker_url = os.getenv("MQTT_URL", "gatewaymqtt")
mqtt_broker_port = int(os.getenv("MQTT_PORT", 1883))

client = mqtt.Client("emo")

client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish

client.connect(mqtt_broker_url, mqtt_broker_port)

client.loop_forever()
