# -*- coding: utf-8 -*-

#  Copyright (c) 2020 Brian Towles
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#  SOFTWARE.

import os
import sys

import jwt
import requests
import yaml
from jwt.exceptions import InvalidTokenError

DEFAULT_CONFIG_LOCATION = './config_templates'
EVENT_PREFIX_DEFAULT = u'indigo_hassbridge'
HASS_DISCOVERY_PREFIX_DEFAULT = u'homeassistant'
HASS_URL_DEFAULT = u'http://localhost:8123'

TOPIC_ROOT = '{d[discovery_prefix]}/{d[hass_type]}/{d[mqtt_name]}'
MQTT_UNIQUE_ID_TEMPLATE = 'indigo_mqtt_{d[mqtt_name]}'



def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class Config(object):
    def __init__(self, pluginPrefs, logger):
        super(Config, self).__init__()
        self.logger = logger
        self.debug = pluginPrefs.get(u"showDebugInfo", False)
        self.mqtt_protocol = pluginPrefs.get(u"mqtt_protocol", u'tcp')
        self.mqtt_server = pluginPrefs.get(u"serverAddress", u'localhost')
        self.mqtt_port = int(pluginPrefs.get(u"serverPort", 1883))
        self.mqtt_username = pluginPrefs.get(u"serverUsername", u"")
        self.mqtt_password = pluginPrefs.get(u"serverPassword", u"")
        self.mqtt_use_encryption = pluginPrefs.get(
            u"mqtt_use_encryption",
            False)
        self.mqtt_allow_unvalidated = pluginPrefs.get(
            u"mqtt_allow_unvalidated",
            False)
        self.mqtt_set_client_id = pluginPrefs.get(u"mqtt_set_client_id", False)
        self.mqtt_client_id = pluginPrefs.get(u"mqtt_client_id", u"")
        if not self.mqtt_set_client_id:
            self.mqtt_client_id = u""

        self.hass_access_token = pluginPrefs.get(u'access_token', u'')
        try:
            jwt.decode(self.hass_access_token, verify=False)
        except InvalidTokenError:
            self.logger.warn(u'Access Token does not appear to be valid.')
        self.hass_session_headers = {
            'Authorization': 'Bearer {}'.format(self.hass_access_token)
        }
        self.hass_url = pluginPrefs.get(u'server_url', HASS_URL_DEFAULT)
        if self.hass_url.endswith('/'):
            self.hass_url = self.hass_url[:-1]

        self.hass_ssl_validate = pluginPrefs.get(u'https_validate_cert', True)
        self.hass_event_prefix = pluginPrefs.get(u'event_prefix',
            EVENT_PREFIX_DEFAULT)
        self.hass_discovery_prefix = pluginPrefs.get(u'discovery_prefix',
            HASS_DISCOVERY_PREFIX_DEFAULT)

        # Setup the events session
        self.hass_event_session = requests.Session()
        self.hass_event_session.headers = self.hass_session_headers

        self.customizations = {}
        self.use_customize_file = pluginPrefs.get(u"use_customization_file",
            False)
        self.customize_file_path = pluginPrefs.get(u"customization_file_path",
            u"")

        self.create_battery_sensors = pluginPrefs.get(u"create_battery_sensors",
            False)

        if self.use_customize_file:
            self.customizations = self.__read_customization_file()

    def __read_customization_file(self):
        try:
            if os.path.isfile(self.customize_file_path):
                stream = file(self.customize_file_path, 'r')
                return yaml.full_load(stream)
        except Exception:
            t, v, tb = sys.exc_info()
            self.__handle_exception(t, v, tb)
            raise

    def __handle_exception(self, exc_type, exc_value, exc_traceback):
        self.logger.error(u'Exception trapped:' + unicode(exc_value))


class RegisterableDevice(object):
    def register(self):
        pass

    def cleanup(self):
        pass

    def shutdown(self):
        pass


class UpdatableDevice(object):
    def update(self, orig_dev, new_dev):
        pass


class CommandProcessor(object):
    def process_command(self, cmd, config):
        """
        Handles converting a command into an event and payload to pass to
        an EventSender
        """
        return None, None


class TimedUpdateCheck(object):
    def check_for_update(self):
        pass


class MqttClient(object):
    # Here will be the instance stored.
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if MqttClient.__instance == None:
            MqttClient()
        return MqttClient.__instance

    def __init__(self):
        """ Virtually private constructor. """
        if MqttClient.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            MqttClient.__instance = self
        self.client = None