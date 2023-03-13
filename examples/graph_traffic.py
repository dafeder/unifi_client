import logging
import os
import json
import sys

import plotly.express as px
import pandas

import unifi_client
import unifi_client_utils

# Setting up a logger

logger = logging.getLogger("UNIFI_CLIENT")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# set environment var UNIFI_URI to https://username:password@controler_address_ip

if os.environ.get("UNIFI_URI") is None:
    print("Required environment var UNIFI_URI not set. Bailing")
    sys.exit(-1)

unifi_controller_url, unifi_username, unifi_password = unifi_client_utils.url_username_password_from_uri(os.environ.get("UNIFI_URI"))

# create a client instance. this will log in with the credentials provided
unifi_client = unifi_client.UnifiAPIClient(unifi_controller_url, unifi_username, unifi_password, logger, verify=False)
traffic_stats = unifi_client.get_dpi_by_app("default")

pd = {'mac':[], 'tx_bytes':[], 'category': []}
for device in traffic_stats["data"]:
    mac = device["mac"]
    for app in device["by_app"]:
        pd['mac'].append(mac)
        pd['tx_bytes'].append(app['tx_bytes'])
        pd['category'].append(f"{app['x_app']} ({app['x_cat']})")


traffic_data_frame= pandas.DataFrame(data=pd)

fig = px.bar(traffic_data_frame, x="mac", y="tx_bytes", color="category", title="Traffic")
fig.show()