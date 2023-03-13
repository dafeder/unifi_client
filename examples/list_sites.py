import logging
import os
import json
import sys

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

# set environment var UNIFI_URI into it's parts

unifi_controller_url, unifi_username, unifi_password = unifi_client_utils.url_username_password_from_uri(os.environ.get("UNIFI_URI"))

# create a client instance. this will log in with the credentials provided
print(json.dumps(unifi_client.UnifiAPIClient(unifi_controller_url, unifi_username, unifi_password, logger, verify=False).get_sites(), indent=4))

