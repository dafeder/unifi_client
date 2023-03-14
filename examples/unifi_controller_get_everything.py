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
unifi_client = unifi_client.UnifiAPIClient(unifi_controller_url, unifi_username, unifi_password, logger, verify=False)

controller_data_results_dict = dict()
site = "default"

controller_data_results_dict["get_self"] = {"end_point": "/api/self", "result": unifi_client.get_self()}

controller_data_results_dict["get_sites"] = {"end_point": "/api/self/sites", "result": unifi_client.get_sites()}

controller_data_results_dict["get_self_site_stats"] = {"end_point": "/api/stat/sites", "result": unifi_client.get_self_site_stats()}

controller_data_results_dict[f"get_devices_for_site ({site})"] = {"end_point": f"/api/s/{site}/stat/device", "result": unifi_client.get_devices_for_site(site)}

controller_data_results_dict["get_devices_for_default_site"] = {"end_point": f"/api/s/default/stat/device", "result": unifi_client.get_devices_for_default_site()}

#controller_data_results_dict[f"get_stats_for_site ({site}, 5min,user)"] = {"end_point": "/api/self", "result": unifi_client.get_self()}

controller_data_results_dict[f"get_5min_site_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/5minutes.site", "result": unifi_client.get_5min_site_all_stats(site)}
controller_data_results_dict[f"get_5min_ap_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/5minutes.ap", "result": unifi_client.get_5min_ap_all_stats(site)}
controller_data_results_dict[f"get_5min_user_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/5minutes.user", "result": unifi_client.get_5min_user_all_stats(site)}

controller_data_results_dict[f"get_hourly_site_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/hourly.site", "result": unifi_client.get_hourly_site_all_stats(site)}
controller_data_results_dict[f"get_hourly_ap_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/hourly.ap", "result": unifi_client.get_hourly_ap_all_stats(site)}
controller_data_results_dict[f"get_hourly_user_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/hourly.user", "result": unifi_client.get_hourly_user_all_stats(site)}

controller_data_results_dict[f"get_daily_site_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/daily.site", "result": unifi_client.get_daily_site_all_stats(site)}
controller_data_results_dict[f"get_daily_ap_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/daily.ap", "result": unifi_client.get_daily_ap_all_stats(site)}
controller_data_results_dict[f"get_daily_user_all_stats ({site}, default time)"] = {"end_point": f"/api/s/{site}/stat/report/daily.user", "result": unifi_client.get_daily_user_all_stats(site)}

controller_data_results_dict[f"get_5min_site_all_stats ({site}, last hour)"] = {"end_point": f"/api/s/{site}/stat/report/5minutes.site", "result": unifi_client.get_5min_site_all_stats(site, *unifi_client_utils.one_hour_ago())}

controller_data_results_dict[f"get_active_clients_for_site ({site})"] = {"end_point": f"/api/s/{site}/stat/sta", "result": unifi_client.get_active_clients_for_site(site)}

controller_data_results_dict[f"get_known_clients_for_site ({site})"] = {"end_point": f"/api/s/{site}/rest/sta", "result": unifi_client.get_known_clients_for_site(site)}

controller_data_results_dict[f"get_ddns_information_for_site ({site})"] = {"end_point": f"/api/s/{site}/stat/dynamicdns", "result": unifi_client.get_ddns_information_for_site(site)}

controller_data_results_dict[f"get_site_dpi_by_app ({site})"] = {"end_point": f"/api/s/{site}/stat/sitedpi", "result": unifi_client.get_site_dpi_by_app(site)}

controller_data_results_dict[f"get_site_dpi_by_category ({site})"] = {"end_point": f"/api/s/{site}/stat/sitedpi", "result": unifi_client.get_site_dpi_by_category(site)}

controller_data_results_dict[f"get_dpi_by_app ({site})"] = {"end_point": f"/api/s/{site}/stat/stadpi", "result": unifi_client.get_dpi_by_app(site)}

controller_data_results_dict[f"get_dpi_by_category ({site})"] = {"end_point": f"/api/s/{site}/stat/stadpi", "result": unifi_client.get_dpi_by_category(site)}

controller_data_results_dict[f"run_speed_test ({site})"] = {"end_point": f"/api/s/{site}/cmd/devmgr", "result": unifi_client.run_speed_test(site)}

controller_data_results_dict[f"status_speed_test ({site})"] = {"end_point": f"/api/s/{site}/cmd/devmgr", "result": unifi_client.status_speed_test(site)}

with open("../local/ever_result.json", "w+") as jf:
    json.dump(controller_data_results_dict, jf)

#print(json.dumps(controller_data_results_dict, indent=4))

# spd_run = unifi_client.run_speed_test("default")
# print(json.dumps(spd_run, indent=4))
# print(json.dumps(unifi_client.status_speed_test("default"), indent=4))

# print(json.dumps(unifi_client.get_site_dpi_by_app("default"), indent=4))

# Some examples of api calls

# print(json.dumps(unifi_client.get_sites(), indent=4))
# print(json.dumps(unifi_client.get_devices_for_default_site(), indent=4))
# print(json.dumps(unifi_client.get_5min_ap_all_stats("default", *unifi_client.one_hour_ago()), indent=4))

# Example of getting traffic stats and mapping the id value in the API results to human-readable
# app_stats = unifi_client.get_dpi_by_app("default")
# print(json.dumps(app_stats, indent=4))

