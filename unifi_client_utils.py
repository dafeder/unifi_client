import urllib.parse

import arrow


def url_username_password_from_uri(uri_to_parse):
    """
    Splits out user name, user password and URL from a URI.
    Input "https://someuser:somepassword@1.2.3.4:8443" would return "https://1.2.3.4:8443", "someusername", "somepassword"

    :param uri_to_parse: The URI to parse
    :return: url, user name, password
    """
    split_uri = urllib.parse.urlsplit(uri_to_parse)

    controller_url = split_uri.scheme + "://" + str(split_uri.hostname) + (
        "" if split_uri.port is None else ":" + str(split_uri.port))
    username = split_uri.username
    password = urllib.parse.unquote(str(split_uri.password))

    return controller_url, username, password


def thirty_min_ago():
    return int(arrow.utcnow().shift(minutes=-30).timestamp()) * 1000, int(arrow.utcnow().timestamp()) * 1000


def one_hour_ago():
    return int(arrow.utcnow().shift(hours=-1).timestamp()) * 1000, int(arrow.utcnow().timestamp()) * 1000
