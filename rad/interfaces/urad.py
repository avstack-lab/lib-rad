# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-01
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-09
# @Description:
"""

"""

import itertools
import os, sys
import serial
import struct
import numpy as np
from time import time, sleep
from rad import detections
from .base import Radar


class URadRadar(Radar):
    id_iter = itertools.count()

    def __init__(self, config_port_name='/dev/ttyUSB0', data_port_name='/dev/ttyUSB1',
            config_file='chirp_config.cfg', snr_floor=8, verbose=False):
        self.config_port_name = config_port_name
        self.data_port_name = data_port_name
        self.config_file = os.path.join(os.path.dirname(__file__), 'config', config_file)
        self.config_port = None
        self.data_port = None
        self.verbose = verbose
        self.started = False
        self.packet_header = bytearray([])

        self.noise_razel = [1e-3, 1*np.pi/180, 1*np.pi/180]
        self.noise_xyz = [1e-3, 1e-3, 1e-3]  # an approximation
        self.snr_floor = snr_floor
        self.ID = next(self.id_iter)

        self.tlv_header_len = 8
        self.header_len = 40
        self.sync_pattern = 0x708050603040102

    def __call__(self):
        """
        Returns an exit code based on what happened
        0 - detected some objects
        1 - saw payload but no objects registered
        2 - sync pattern not correct
        """
        time_packet = time()
        self.packet_header += self.data_port.read(self.header_len - len(self.packet_header))
        sync, version, total_packet_len, platform, \
            frame_number, time_cpu_cycles, num_detected_objs, \
            num_tlvs, sub_frame_number = struct.unpack('Q8I', self.packet_header[:self.header_len])

        if sync == self.sync_pattern:
            self.packet_header = bytearray([])
            packet_payload = self.data_port.read(total_packet_len - self.header_len)
            objects = np.zeros((num_detected_objs, 6))
            for i in range(num_tlvs):
                tlv_type, tlv_length = struct.unpack('2I', packet_payload[:self.tlv_header_len])
                if tlv_type > 20 or tlv_length > 10000:
                    packet_header = bytearray([])
                    break
                packet_payload = packet_payload[self.tlv_header_len:]
                if tlv_type == 1:
                    for j in range(num_detected_objs):
                        x, y, z, v = struct.unpack('4f', packet_payload[:16])
                        objects[j, 0] = x
                        objects[j, 1] = y
                        objects[j, 2] = z
                        objects[j, 3] = v
                        packet_payload = packet_payload[16:]
                elif tlv_type == 7:
                    for j in range(num_detected_objs):
                        snr, noise = struct.unpack('2H', packet_payload[:4])
                        objects[j, 4] = snr
                        objects[j, 5] = noise
                        packet_payload = packet_payload[4:]
            if num_detected_objs > 0:
                exit_code = 0
            else:
                exit_code = 1
        else:
            exit_code = 2
            objects = np.zeros((0,6))
            self.packet_header = self.packet_header[1:]

        converted_objects = []
        for i in range(objects.shape[0]):
            if objects[i,4] > self.snr_floor:
                converted_objects.append(detections.RadarDetection3D_XYZ(
                    self.ID, time_packet, objects[i,0], objects[i,1],
                    objects[i,2], objects[i,3], self.noise_xyz, objects[i,4]))

        return converted_objects, exit_code

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

    def stop(self, sleep_time=3):
        print('Closing ports...', end='', flush=True)
        if self.config_port is not None:
            self.config_port.close()
        if self.data_port is not None:
            self.data_port.close()
        self.started = False
        sleep(sleep_time)
        print('done')