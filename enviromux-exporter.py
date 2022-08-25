#!/usr/bin/env python

import requests
import time
import re
import os
from prometheus_client import start_http_server
from prometheus_client.core import GaugeMetricFamily, REGISTRY

"""
Enviromux sensor ID status code definitions

0    STATUS_NOTCONNECTED       6    STATUS_DISCONNECTED       
1    STATUS_NORMAL             7    STATUS_TAMPER_ALERT      
2    STATUS_WARNING            8    STATUS_PREDIZZY
3    STATUS_ALERT              9    STATUS_DIZZY
4    STATUS_ACKNOWLEDGED       10   STATUS_IN_USE            
5    STATUS_DISMISSED          11   STATUS_NOT_USED             
"""
http_server_port=int(os.environ.get('ENVIROMUX_LISTENING_PORT'))

class EnviromuxMetrics(object):
    def __init__(self, enviromux_timeout=30):

        self.enviromux_login_url = os.environ.get('ENVIROMUX_LOGIN_URL')
        self.enviromux_json_url = os.environ.get('ENVIROMUX_JSON_URL')
        self.enviromux_ip = os.environ.get('ENVIROMUX_IP')
        self.enviromux_user = os.environ.get('ENVIROMUX_USER')
        self.enviromux_pswd = os.environ.get('ENVIROMUX_PSWD')
        self.enviromux_timeout = enviromux_timeout

    def collect(self):
        login_data = {
            'username': self.enviromux_user,
            'password': self.enviromux_pswd
        }
        login_request = requests.post(
            url=self.enviromux_login_url,
            data=login_data,
            timeout=self.enviromux_timeout
        )
        
        login_request_json = login_request.json()
        login_session_cookie = login_request_json['cookie']

        headers = {
            'Host': self.enviromux_ip,
            'Cookie': login_session_cookie
        }

        fetch_data_request = requests.get(
            url=self.enviromux_json_url,
            headers=headers,
            timeout=self.enviromux_timeout
        )

        response_json = fetch_data_request.json()

        hw_info_metrics = GaugeMetricFamily(
            'enviromux_hw_info',
            'Enviromux hardware info, static output of 1.',
            labels=['model', 'uptime', 'firmware', 'ipaddr']
        )

        model = response_json['data']['all'][0]['device']['model']
        uptime = response_json['data']['all'][0]['device']['uptime']
        firmware = response_json['data']['all'][0]['device']['firmware']
        ipaddr = response_json['data']['all'][0]['network']['addr']
        hw_info_metrics.add_metric([model, uptime, firmware, ipaddr], '1')

        yield hw_info_metrics

        isens_value_metrics = GaugeMetricFamily(
            'enviromux_isens_value_metrics',
            'Enviromux internal sensor metrics output value.',
            labels=['instance', 'unit', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['isens']:
                instance = k['desc']
                if 'TEMP' in instance:
                    unit = 'C'
                elif 'HUMIDITY' in instance:
                    unit = '%'
                elif 'VOLT' in instance:
                    unit = 'V'
                else:
                    unit = ''
                metric_type = 'value'
                val = k['val']
                val_numeric = re.sub('[^\.0-9]', '', val)
                isens_value_metrics.add_metric([instance, unit, metric_type], val_numeric)

        yield isens_value_metrics

        isens_status_metrics = GaugeMetricFamily(
            'enviromux_isens_status_metrics',
            'Enviromux internal sensor metrics status code.',
            labels=['instance', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['isens']:
                instance = k['desc']
                metric_type = 'status'
                status = str(k['status'])
                isens_status_metrics.add_metric([instance, metric_type], status)

        yield isens_status_metrics

        esens_value_metrics = GaugeMetricFamily(
            'enviromux_esens_value_metrics',
            'Enviromux external sensor metrics output value.',
            labels=['instance', 'unit', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['esens']:
                instance = k['desc']
                if 'TEMP' in instance:
                    unit = 'C'
                elif 'HUMIDITY' in instance:
                    unit = '%'
                elif 'VOLT' in instance:
                    unit = 'V'
                else:
                    unit = 'unknown'
                metric_type = 'value'
                val = k['val']
                val_numeric = re.sub('[^\.0-9]', '', val)
                esens_value_metrics.add_metric([instance, unit, metric_type], val_numeric)

        yield esens_value_metrics

        esens_status_metrics = GaugeMetricFamily(
            'enviromux_esens_status_metrics',
            'Enviromux external sensor metrics status code.',
            labels=['instance', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['esens']:
                instance = k['desc']
                metric_type = 'status'
                status = str(k['status'])
                esens_status_metrics.add_metric([instance, metric_type], status)

        yield esens_status_metrics

        diginp_value_metrics = GaugeMetricFamily(
            'enviromux_diginp_value_metrics',
            'Enviromux digital input value sensor metrics. (0 = Closed, 1 = Open).',
            labels=['instance', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['diginp']:
                instance = k['desc']
                metric_type = 'value'
                val = k['val']
                if 'Open' in val:
                    val = '1'
                else:
                    val = '0'
                diginp_value_metrics.add_metric([instance, metric_type], val)

        yield diginp_value_metrics

        diginp_status_metrics = GaugeMetricFamily(
            'enviromux_diginp_status_metrics',
            'Enviromux digital input sensor metrics status code.',
            labels=['instance', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['diginp']:
                instance = k['desc']
                metric_type = 'status'
                status = str(k['status'])
                diginp_status_metrics.add_metric([instance, metric_type], status)

        yield diginp_status_metrics

        power_status_metrics = GaugeMetricFamily(
            'enviromux_power_status_metrics',
            'Enviromux power supply status code',
            labels=['id', 'instance', 'output', 'metric_type']
        )

        for i in response_json['data']['all']:
            for k in i['power']:
                id = str(k['idx'])
                instance = k['desc']
                output = k['val']
                metric_type = 'status'
                status = str(k['status'])
                power_status_metrics.add_metric([id, instance, output, metric_type], status)

        yield power_status_metrics

if __name__ == '__main__':
    REGISTRY.register(EnviromuxMetrics())
    start_http_server(http_server_port)
    while True: time.sleep(1)
