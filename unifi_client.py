import os
import urllib.parse
import logging
import sys
import json
import re
import hashlib

import requests
import arrow
import jsbeautifier
import yaml


class UnifiAPIClientException(Exception):
    pass

class UnifiAPIClient:

    _controller_url = None
    _controller_requests_session = None
    _logger = None

    all_stat_attributes = ['bytes', 'wan-tx_bytes', 'wan-rx_bytes', 'wlan_bytes', 'num_sta',
                           'lan-num_sta', 'wlan-num_sta', 'time', 'rx_bytes', 'tx_bytes']

    network_traffic_category_map = None
    network_traffic_category_map_hash = None
    network_traffic_application_map = None
    network_traffic_application_map_hash = None

    def __init__(self,
                 controller_url,
                 authentication_username,
                 authentication_password,
                 api_client_logger=logging.getLogger(),
                 verify=None,
                 try_to_get_category_and_app_map=True):

        self._logger = api_client_logger
        self._controller_url = controller_url
        self._controller_requests_session = requests.Session()

        if verify is not None:
            self._controller_requests_session.verify = verify

        # Login to the controller
        url_login = unifi_controller_url + "/api/login"
        self._logger .debug(f"{self} logging in to controller")
        credentials = {"username": authentication_username, "password": authentication_password}
        login_response = self._controller_requests_session.post(url_login,
                                                       headers={"content-type": "application/json"},
                                                       data=json.dumps(credentials))

        if login_response.status_code != 200:
            err_msg = f"{self} Login failed. HTTP request to {url_login} returned status code {login_response.status_code}. Expected 200."
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger .debug(f"{self} logged in to controller OK")

        if try_to_get_category_and_app_map:
            try:
                self.network_traffic_category_map, self.network_traffic_application_map = self.get_category_and_application_map()

                self.network_traffic_category_map_hash = str(hashlib.sha256(bytes(json.dumps(self.network_traffic_category_map), 'utf-8')).hexdigest())
                self.network_traffic_application_map_hash = str(hashlib.sha256(bytes(json.dumps(self.network_traffic_application_map), 'utf-8')).hexdigest())

            except UnifiAPIClientException:
                self._logger.info(f"{self} could not get the category and application map. See log for details")


    def get_sites(self):

        url_sites = unifi_controller_url + "/api/self/sites"
        self._logger.debug(f"Getting sites from {url_sites}")
        sites_response = self._controller_requests_session.get(url_sites,
                                                      headers={"content-type": "application/json"})
        if sites_response.status_code != 200:
            err_msg = f"{self} request to sites endpoint {url_sites} returned status code {sites_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got sites from {url_sites} OK")

        # TODO Write sites response JSON schema
        # TODO Check sites response against JSON schema
        return sites_response.json()


    def get_devices_for_site(self, site):

        url_devices = unifi_controller_url+"/api/s/"+site+"/stat/device"
        self._logger.debug(f"Getting devices for site {site} from {url_devices}")
        site_devices_response = self._controller_requests_session.get(url_devices,
                                                               headers={"content-type": "application/json"})
        if site_devices_response.status_code != 200:
            err_msg = f"{self} request to site devicess endpoint {url_devices} returned status code {site_devices_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site devices from {url_devices} OK")

        # TODO Write sites response JSON schema
        # TODO Check sites response against JSON schema
        return site_devices_response.json()

    def get_devices_for_default_site(self):
        return self.get_devices_for_site("default")

    def get_stats_for_site(self, site, interval, element_type,
                           stat_attributes,
                           start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None,
                           filter_mac_list=None):

        supported_intervals = ['5minutes', 'hourly', 'daily']
        supported_element_types = ['site', 'user', 'ap']

        if interval not in supported_intervals:
            raise ValueError(f"{self} invalid interval value {interval}. Must be one of {supported_intervals}")
        if element_type not in supported_element_types:
            raise ValueError(f"{self} invalid element type value {element_type}. Must be one of {supported_element_types}")
        for stat_attribute in stat_attributes:
            if stat_attribute not in self.all_stat_attributes:
                raise ValueError(f"{self} unsupported stat attribute type value {stat_attribute}. Must be among types {self.all_stat_attributes}")

        url_stat = unifi_controller_url + "/api/s/"+site+"/stat/report/"+interval+"."+element_type
        self._logger.debug(f"{self} getting stats for site {site} for interval {interval} of element type {element_type} from {url_stat}")

        stat_request_parameters = {
            'attrs': stat_attributes
        }
        if start_epoch_timestamp_ms is not None:
            stat_request_parameters['start'] = start_epoch_timestamp_ms
        if end_epoch_timestamp_ms is not None:
            stat_request_parameters['end'] = end_epoch_timestamp_ms
        if filter_mac_list is not None and len(filter_mac_list) > 0:
            stat_request_parameters["macs"] = filter_mac_list

        print(stat_request_parameters)

        stat_device_response = self._controller_requests_session.post(url_stat,
                                                                      headers={"content-type": "application/json"},
                                                                      data=json.dumps(stat_request_parameters))

        if stat_device_response.status_code != 200:
            err_msg = f"{self} request to site stat endpoint {url_stat} returned status code {stat_device_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        # TODO write site stats json schema
        # TODO check stat_device_response json against site stats json schema
        return stat_device_response.json()

    def get_5min_site_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "5minutes", "site",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_5min_ap_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "5minutes", "ap",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_5min_user_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "5minutes", "user",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_hourly_site_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "hourly", "site",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_hourly_ap_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "hourly", "ap",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_hourly_user_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "hourly", "user",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_monthly_site_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "monthly", "site",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_monthly_ap_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "monthly", "ap",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_monthly_user_all_stats(self, site, start_epoch_timestamp_ms=None, end_epoch_timestamp_ms=None):
        return self.get_stats_for_site(site, "monthly", "user",
                                       self.all_stat_attributes,
                                       start_epoch_timestamp_ms, end_epoch_timestamp_ms)

    def get_active_clients(self, site):

        url_active_clients = unifi_controller_url + "/api/s/"+site+"/stat/sta"
        self._logger.debug(f"Getting active clients for site {site} from {url_active_clients}")
        site_active_clients_response = self._controller_requests_session.get(url_active_clients,
                                                               headers={"content-type": "application/json"})
        if site_active_clients_response.status_code != 200:
            err_msg = f"{self} request to site active clients endpoint {url_active_clients} returned status code {site_active_clients_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site active clients from {url_active_clients} OK")

        # TODO Write sites active clients response JSON schema
        # TODO Check sites active clients response against JSON schema
        return site_active_clients_response.json()


    def get_known_clients(self, site):

        url_known_clients = unifi_controller_url + "/api/s/"+site+"/rest/user"
        self._logger.debug(f"Getting known clients for site {site} from {url_known_clients}")
        site_known_clients_response = self._controller_requests_session.get(url_known_clients,
                                                               headers={"content-type": "application/json"})
        if site_known_clients_response.status_code != 200:
            err_msg = f"{self} request to site known clients endpoint {url_known_clients} returned status code {site_known_clients_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site known clients from {url_known_clients} OK")

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return site_known_clients_response.json()

    def DOES_NOT_WORK_get_spectrum_scan(self, site, filter_mac_list=None):

        # TODO spectrum scan does not work - returns 404
        url_spectrum_scan = unifi_controller_url + "/api/s/"+site+"/stat/spectrumscan"
        self._logger.debug(f"Getting spectrum for site {site} from {url_spectrum_scan}")
        site_spectrum_scan_response = self._controller_requests_session.get(url_spectrum_scan,
                                                               headers={"content-type": "application/json"})
        if site_spectrum_scan_response.status_code != 200:
            err_msg = f"{self} request to site spectrum scan endpoint {url_spectrum_scan} returned status code {site_spectrum_scan_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site known clients from {url_spectrum_scan} OK")

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return site_spectrum_scan_response.json()

    def get_ddns_information(self, site):

        url_ddns_info = unifi_controller_url + "/api/s/"+site+"/stat/dynamicdns"
        self._logger.debug(f"Getting dynamic dns info for site {site} from {url_ddns_info}")
        site_ddns_response = self._controller_requests_session.get(url_ddns_info,
                                                                   headers={"content-type": "application/json"})
        if site_ddns_response.status_code != 200:
            err_msg = f"{self} request to site ddns info endpoint {url_ddns_info} returned status code {site_ddns_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site ddns info from {site_ddns_response} OK")

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return site_ddns_response.json()


    def get_site_dpi_by_app(self, site, filter_category_list=None):

        url_site_dpi =  unifi_controller_url + "/api/s/"+site+"/stat/sitedpi"

        self._logger.debug(f"Getting site dpi by app for site {site} from {url_site_dpi}")

        parameters = {"type": "by_app"}
        if filter_category_list is not None and len(filter_category_list) > 0:
            parameters["cats"] = filter_category_list

        site_dpi_app_response = self._controller_requests_session.post(url_site_dpi,
                                                                        headers={"content-type": "application/json"},
                                                                        data=json.dumps(parameters))
        if site_dpi_app_response.status_code != 200:
            err_msg = f"{self} request to site dpi by app info endpoint {url_site_dpi} returned status code {site_dpi_app_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site dpi by app from {url_site_dpi} OK")

        response_site_app_stats = site_dpi_app_response.json()

        if len(response_site_app_stats["data"]) > 0 and self.network_traffic_application_map is not None and self.network_traffic_category_map is not None:
            self._logger.debug("Going to attempt to map stat application and category ids to human readable text")

            for stat in response_site_app_stats["data"][0].get("by_app", []):
                # the app human name is from the app id + the cat id sifted two bytes
                app_cat_id = (stat["cat"] << 16) + stat["app"]

                stat["x_cat"] = self.network_traffic_category_map[stat["cat"]]["name"]
                stat["x_app"] = self.network_traffic_application_map.get(app_cat_id, {"name": "__unlisted__"})["name"]
                stat["x_cat_app_id"] = self.network_traffic_category_map_hash+":"+self.network_traffic_application_map_hash


        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return response_site_app_stats


    def get_site_dpi_by_category(self, site):

        url_site_dpi =  unifi_controller_url + "/api/s/"+site+"/stat/sitedpi"

        self._logger.debug(f"Getting site dpi by cat for site {site} from {url_site_dpi}")

        parameters = {"type": "by_cat"}

        site_site_dpi_cat_response = self._controller_requests_session.post(url_site_dpi,
                                                                        headers={"content-type": "application/json"},
                                                                        data=json.dumps(parameters))
        if site_site_dpi_cat_response.status_code != 200:
            err_msg = f"{self} request to site dpi by category info endpoint {url_site_dpi} returned status code {site_site_dpi_cat_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site ddns info from {url_site_dpi} OK")

        # TODO Write sites dpi by cat response JSON schema
        # TODO Check sites dpi by cat response against JSON schema
        return site_site_dpi_cat_response.json()

    def get_dpi_by_app(self, site, filter_mac_list=None, filter_category_list=None):

        url_dpi = unifi_controller_url + "/api/s/" + site + "/stat/stadpi"

        self._logger.debug(f"Getting dpi by app for site {site} from {url_dpi}")

        parameters = {"type": "by_app"}
        if filter_mac_list is not None and len(filter_mac_list) > 0:
            parameters["macs"] = filter_mac_list
        if filter_category_list is not None and len(filter_category_list) > 0:
            parameters["cats"] = filter_category_list
            # TODO look at dpi by app category filter, doesn't seem to work. all cats are returned

        site_dpi_app_response = self._controller_requests_session.post(url_dpi,
                                                                        headers={"content-type": "application/json"},
                                                                        data=json.dumps(parameters))
        if site_dpi_app_response.status_code != 200:
            err_msg = f"{self} request to site dpi by app info endpoint {url_dpi} returned status code {site_dpi_app_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site dpi by app from {url_dpi} OK")

        response_app_stats = site_dpi_app_response.json()

        if self.network_traffic_application_map is not None and self.network_traffic_category_map is not None:
            self._logger.debug("Going to attempt to map stat application and category ids to human readable text")

            for device in response_app_stats["data"]:
                for stat in device["by_app"]:
                    # the app human name is from the app id + the cat id sifted two bytes
                    app_cat_id = (stat["cat"] << 16) + stat["app"]

                    stat["x_cat"] = self.network_traffic_category_map[stat["cat"]]["name"]
                    stat["x_app"] = self.network_traffic_application_map.get(app_cat_id, {"name": "__unlisted__"})["name"]
                    stat["x_cat_app_id"] = self.network_traffic_category_map_hash+":"+self.network_traffic_application_map_hash

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return response_app_stats

    def get_dpi_by_category(self, site, filter_mac_list=None):

        url_dpi = unifi_controller_url + "/api/s/" + site + "/stat/stadpi"

        self._logger.debug(f"Getting dpi by cat for site {site} from {url_dpi}")

        parameters = {"type": "by_cat"}
        if filter_mac_list is not None and len(filter_mac_list) > 0:
            parameters["macs"] = filter_mac_list

        site_dpi_cat_response = self._controller_requests_session.post(url_dpi,
                                                                        headers={"content-type": "application/json"},
                                                                        data=json.dumps(parameters))
        if site_dpi_cat_response.status_code != 200:
            err_msg = f"{self} request to site dpi by category info endpoint {url_dpi} returned status code {site_dpi_cat_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Got site ddns info from {url_dpi} OK")

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return site_dpi_cat_response.json()

    def run_speed_test(self, site):

        url_devmgr = unifi_controller_url + "/api/s/"+site+"/cmd/devmgr"
        parameters = {"cmd": "speedtest"}

        speed_test_response = self._controller_requests_session.post(url_devmgr,
                                                                     headers={"content-type": "application/json"},
                                                                     data=json.dumps(parameters)
                                                                     )

        if speed_test_response.status_code != 200:
            err_msg = f"{self} request to site start speed test endpoint {url_devmgr} returned status code {speed_test_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Send speed test command {url_devmgr} OK")

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return speed_test_response.json()

    def status_speed_test(self, site):

        url_devmgr = unifi_controller_url + "/api/s/" + site + "/cmd/devmgr"
        parameters = {"cmd": "speedtest-status"}

        speed_test_response = self._controller_requests_session.post(url_devmgr,
                                                                     headers={"content-type": "application/json"},
                                                                     data=json.dumps(parameters)
                                                                     )

        if speed_test_response.status_code != 200:
            err_msg = f"{self} request to site start speed test endpoint {url_devmgr} returned status code {speed_test_response.status_code}. Expected 200"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        self._logger.debug(f"Send speed test command {url_devmgr} OK")

        # TODO Write sites known clients response JSON schema
        # TODO Check sites known clients response against JSON schema
        return speed_test_response.json()

    def __str__(self):
        return f"UnifiAPIClient to {self._controller_url}"


    @staticmethod
    def uri_to_parts(unifi_uri):
        split_unifi_uri = urllib.parse.urlsplit(unifi_uri)

        controller_url = split_unifi_uri.scheme + "://" + str(split_unifi_uri.hostname) + ("" if split_unifi_uri.port is None else ":" + str(split_unifi_uri.port))
        username = split_unifi_uri.username
        password = urllib.parse.unquote(str(split_unifi_uri.password))

        return  controller_url, username, password


    @staticmethod
    def thirty_min_ago():
        return int(arrow.utcnow().shift(minutes=-30).timestamp())*1000, int(arrow.utcnow().timestamp())*1000


    @staticmethod
    def one_hour_ago():
        return int(arrow.utcnow().shift(hours=-1).timestamp())*1000, int(arrow.utcnow().timestamp())*1000


    def get_category_and_application_map(self, angular_build_str_list=None):

        if angular_build_str_list is None or len(angular_build_str_list) < 1:
            # Try to figure out the angular 'build' string
            login_page_url =  self._controller_url + "/manage/account/login"
            login_page_response = self._controller_requests_session.get(login_page_url)
            if login_page_response.status_code != 200:
                err_msg = f"{self} request to get login page at {login_page_url} to determine angular build string failed. Returned status code {login_page_response.status_code}. Expected 200"
                self._logger.error(err_msg)
                raise UnifiAPIClientException(err_msg)
            build_stings_in_text = re.findall(r'angular/([a-zA-Z0-9.]*)/js/', login_page_response.text)

            if len(build_stings_in_text) < 1:
                err_msg = f"{self} could not determine angular build string from login page {login_page_url} to. Regex found no instances of angular/(build string))/js"
                self._logger.error(err_msg)
                raise UnifiAPIClientException(err_msg)
        else:
            # used the strings passed in
            build_stings_in_text = angular_build_str_list

        # Typically I've only found one build string on a page but in case there are multiples, loop
        beautified_dpi_js = None
        for angular_build in set(build_stings_in_text):
            dynamic_dpi_js = unifi_controller_url + "/manage/angular/" + angular_build + "/js/dynamic.dpi.js"

            self._logger.debug(f"Trying {dynamic_dpi_js} for category / app mapping javascript page")

            dpi_js_response = self._controller_requests_session.get(dynamic_dpi_js)
            if dpi_js_response.status_code == 200:
                self._logger.debug(f"Found {dynamic_dpi_js} for category / app mapping javascript page")
                beautified_dpi_js = jsbeautifier.beautify(dpi_js_response.text)
                break
            else:
                self._logger.debug(f"Miss {dynamic_dpi_js} for category / app mapping javascript page. Status code is {dpi_js_response.status_code}")
                # ignore 404s
                continue

        if beautified_dpi_js is None:
                err_msg = f"{self} Could not find category / app mapping javascript page"
                self._logger.error(err_msg)
                raise UnifiAPIClientException(err_msg)

        mg = re.match(".*categories: (.*),.*            applications:(.*)}\n    \}, \{\}\],\n    2\:", beautified_dpi_js, re.DOTALL).groups()

        if len(mg) != 2:
            err_msg = f"{self} could not parse dynamic dpi js lib {dynamic_dpi_js}. Regex expected two match groups got {len(mg)}"
            self._logger.error(err_msg)
            raise UnifiAPIClientException(err_msg)

        network_traffic_category_map = yaml.load(mg[0], Loader=yaml.FullLoader)
        network_traffic_application_map = yaml.load(mg[1], Loader=yaml.FullLoader)

        return network_traffic_category_map, network_traffic_application_map


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

unifi_controller_url, unifi_username, unifi_password = UnifiAPIClient.uri_to_parts(os.environ.get("UNIFI_URI"))

# create a client instance. this will log in with the credentials provided
unifi_client = UnifiAPIClient(unifi_controller_url, unifi_username, unifi_password, logger, verify=False)

#spd_run = unifi_client.run_speed_test("default")
#print(json.dumps(spd_run, indent=4))
#print(json.dumps(unifi_client.status_speed_test("default"), indent=4))

print(json.dumps(unifi_client.get_site_dpi_by_app("default"), indent=4))

# Some examples of api calls

#print(json.dumps(unifi_client.get_sites(), indent=4))
#print(json.dumps(unifi_client.get_devices_for_default_site(), indent=4))
#print(json.dumps(unifi_client.get_5min_ap_all_stats("default", *unifi_client.one_hour_ago()), indent=4))

# Example of getting traffic stats and mapping the id value in the API results to human-readable
#app_stats = unifi_client.get_dpi_by_app("default")
#print(json.dumps(app_stats, indent=4))