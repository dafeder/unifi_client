import logging
import os
import json
import sys
import urllib.parse

import boto3
import arrow

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

if os.environ.get("S3_BUCKET_NAME") is None:
    print("Required environment var S3_BUCKET_NAME not set. Bailing")
    sys.exit(-1)

# set environment var UNIFI_URI into it's parts

unifi_controller_url, unifi_username, unifi_password = unifi_client_utils.url_username_password_from_uri(os.environ.get("UNIFI_URI"))

# create a client instance. this will log in with the credentials provided
unifi_client = unifi_client.UnifiAPIClient(unifi_controller_url, unifi_username, unifi_password, logger, verify=False)

site = "default"
s3_bucket_name = os.environ.get("S3_BUCKET_NAME")

ap_daily_stats =  unifi_client.get_daily_ap_all_stats(site)

s3_client = boto3.client('s3')
s3_object_name = f"{urllib.parse.urlsplit(os.environ.get('UNIFI_URI')).hostname}_{site}_ap_daily_stats_{arrow.utcnow().format('YYYY-MM-DD_HH:mm:ss_UTC')}.json"

try:
    s3 = boto3.resource('s3')
    s3object = s3.Object(s3_bucket_name, s3_object_name)
    s3object.put(Body=(bytes(json.dumps(ap_daily_stats).encode('UTF-8'))))
    print(f"Uploaded {s3_object_name} to S3 bucket {s3_bucket_name}!")
except Exception as e:
    logging.error(e)

