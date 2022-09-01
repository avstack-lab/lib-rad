# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-01
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-01
# @Description:
"""

"""

import os, sys
import serial
from time import sleep
from .base import Radar

syncPattern = 0x708050603040102


class URadRadar(Radar):
    def __init__(self, config_port_name='/dev/ttyUSB0', data_port_name='/dev/ttyUSB1',
            config_file='chirp_config.cfg', verbose=False):
        self.config_port_name = config_port_name
        self.data_port_name = data_port_name
        self.config_file = os.path.join(os.path.dirname(__file__), 'config', config_file)
        self.config_port = None
        self.data_port = None
        self.verbose = verbose
        self.started = False

    def start(self):
        if self.started:
            print('Radar already started')
            return
        print('Opening ports...', end='', flush=True)
        baud_config = 115200
        baud_data = 921600
        config_port = serial.Serial(self.config_port_name, baud_config, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.3)
        data_port = serial.Serial(self.data_port_name, baud_data, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.3)
        data_port.reset_output_buffer()
        print('done')

        response = bytearray([])
        while config_port.in_waiting > 0:
            response += config_port.read(1)
        if self.verbose:
            print(response.decode())
            print('Reading configuration file')
        with open(self.config_file, 'r') as fp:
            cnt = 0
            commands = []
            for line in fp:
                if (len(line) > 1):
                    if (line[0] != '%'):
                        commands.append(line)
                        cnt += 1
        for i in range(cnt):
            config_port.write(bytearray(commands[i].encode()))
            sleep(20e-3)
            response = bytearray([])
            while config_port.in_waiting > 0:
                response += config_port.read(1)
            if self.verbose:
                print(response.decode())
        self.config_port = config_port
        self.data_port = data_port
        self.started = True

    def stop(self):
        print('Closing ports...', end='', flush=True)
        if self.config_port is not None:
            self.config_port.close()
        if self.data_port is not None:
            self.data_port.close()
        self.started = False
        print('done')