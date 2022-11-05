# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-01
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-11-05
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
from .base import _Radar, _DataStream


class _uRadRadar(_Radar):
    id_iter = itertools.count()

    def __init__(self, config_file, snr_floor=8, verbose=False):
        if not os.path.exists(config_file):
            config_file = os.path.join(os.path.dirname(__file__), 'config', config_file)
            if not os.path.exists(config_file):
                raise FileNotFoundError('Cannot find config file called {}'.format(config_file))
        self.config_file = config_file
        self.config_data = parse_ti_config(self.config_file)
        self.data_port = None
        self.verbose = verbose
        self.packet = bytearray([])
        self.noise_razel = [1e-3, 1*np.pi/180, 1*np.pi/180]
        self.noise_xyz = [1e-3, 1e-3, 1e-3]  # an approximation
        self.snr_floor = snr_floor
        self.ID = next(self.id_iter)
        self.tlv_header_len = 8
        self.header_len = 40
        self.sync_pattern = 0x708050603040102
        self.frame0 = None

    def read_data_port(self):
        """
        Returns an exit code based on what happened
        0 - detected some objects
        1 - saw payload but no objects registered
        2 - sync pattern not aligned
        3 - buffer has header but not object data

        Coordinates:
        - the default coordinates are
            - x: right
            - y: forward
            - z: up
        - convert to the following coordinates
            - x: forward
            - y: left
            - z: up

        TODO: separate the reading from the processing...
        """
        objects = []

        # -- try to read header
        while True:
            # -- read in header
            self.packet += self.data_port.read(self.header_len - len(self.packet)) 
            if len(self.packet) >= self.header_len:
                header = parse_ti_header(self.packet, self.header_len)
                if header['sync'] == self.sync_pattern:
                    self.packet = bytearray([])
                    break
                else:
                    self.packet = self.packet[1:]  # increment to try to find sync
        else:
            # -- we did not hit the break
            exit_code = 2
            return objects, exit_code

        # -- we did hit the break --> replace the packet buffer with payload (if data is dumped)
        if self.frame0 is None:
            self.frame0 = header['frame_number']
        t = self.config_data['frame_duration_s'] * (header['frame_number'] - self.frame0)
        self.packet += self.data_port.read(header['total_packet_len'] - self.header_len)
        if len(self.packet) >= header['total_packet_len']-self.header_len:
            payload = parse_ti_payload(self.packet, header, self.tlv_header_len)
            objects = convert_payload_to_objects(payload, self.snr_floor, self.ID, self.noise_xyz, timestamp=t)
            self.packet = bytearray([])
            exit_code = 1 if len(objects)==0 else 0
        else:
            exit_code = 3
        return objects, exit_code


class uRadRadarLive(_uRadRadar):
    def __init__(self, config_port_name='/dev/ttyUSB0', data_port_name='/dev/ttyUSB1',
            config_file='chirp_config.cfg', snr_floor=8, verbose=False):
        super().__init__(config_file, snr_floor, verbose)
        self.config_port_name = config_port_name
        self.data_port_name = data_port_name
        self.config_port = None
        self.started = False

    def __call__(self):
        return self.read_data_port()

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


class uRadRadarPlayback(_uRadRadar):
    """Object to manage replay of captured radar data
    
    Inherits from the base ti radar class
    """
    def __init__(self, data_file, config_file,  snr_floor=8, verbose=False):
        super().__init__(config_file, snr_floor, verbose)

        # -- for now, we open the file at class creation. In the future this should
        # be made something like a generator
        if not os.path.exists(data_file):
            raise FileNotFoundError('Cannot find playback file {}'.format(data_file))
        self.filename = data_file
        self.data_port = open(data_file, 'rb')

    def __call__(self):
        frame, exit_code = self.read_data_port()
        if exit_code == 3:
            raise StopIteration
        return frame, exit_code

    def __iter__(self):
        """Set up an iterator for playback simulation

        TODO: does this way to create generator work??
        """
        while True:
            frame, exit_code = self.read_data_port()
            if exit_code == 3:
                break
            else:
                yield frame, exit_code

    def start(self):
        pass

    def stop(self):
        pass


def parse_ti_config(config_file_name, numRxAnt=4, numTxAnt=2):
    config = {} 
    # Read the configuration file and send it to the board
    config_lines = []
    with open(config_file_name, 'r') as f:
        for line in f:
            config_lines.append(line.rstrip('\r\n'))

    for line in config_lines:
        # Split the line
        splitWords = line.split(" ")
        
        # Get the information about the profile configuration
        if '%' in splitWords[0]:
            if ('Frame' in splitWords[1]) and ('Duration(msec)' in splitWords[2]):
                frame_duration_msec = float(splitWords[2].split(':')[-1])
                frame_duration_s = frame_duration_msec/1000

        elif "profileCfg" in splitWords[0]:
            startFreq = int(float(splitWords[2]))
            idleTime = int(splitWords[3])
            rampEndTime = float(splitWords[5])
            freqSlopeConst = float(splitWords[8])
            numAdcSamples = int(splitWords[10])
            numAdcSamplesRoundTo2 = 1;
            
            while numAdcSamples > numAdcSamplesRoundTo2:
                numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2;
                
            digOutSampleRate = int(splitWords[11]);
            
        # Get the information about the frame configuration    
        elif "frameCfg" in splitWords[0]:
            chirpStartIdx = int(splitWords[1]);
            chirpEndIdx = int(splitWords[2]);
            numLoops = int(splitWords[3]);
            numFrames = int(splitWords[4]);
            framePeriodicity = int(splitWords[5]);

        else:
            pass  # we don't care, supposedly

    # Combine the read data to obtain the configuration parameters           
    numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
    config["frame_duration_msec"] = frame_duration_msec
    config["frame_duration_s"] = frame_duration_s
    config["num_doppler_bins"] = numChirpsPerFrame / numTxAnt
    config["num_range_bins"] = numAdcSamplesRoundTo2
    config["range_resolution_meters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * numAdcSamples)
    config["range_idx_to_meters"] = (3e8 * digOutSampleRate * 1e3) / (2 * freqSlopeConst * 1e12 * config["num_range_bins"])
    config["dopper_resolution_mps"] = 3e8 / (2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * config["num_doppler_bins"] * numTxAnt)
    config["max_range"] = (300 * 0.9 * digOutSampleRate)/(2 * freqSlopeConst * 1e3)
    config["max_velocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)
    return config


def parse_ti_header(packet, header_len):
    """Transform TI header into a dictionary"""
    sync, version, total_packet_len, platform, \
        frame_number, time_cpu_cycles, num_detected_objs, \
        num_tlvs, sub_frame_number = struct.unpack('Q8I', packet[:header_len])
    header = {'sync':sync, 'version':version, 'total_packet_len':total_packet_len,
        'platform':platform, 'frame_number':frame_number, 'time_cpu_cycles':time_cpu_cycles,
        'num_detected_objs':num_detected_objs, 'num_tlvs':num_tlvs, 
        'sub_frame_number':sub_frame_number}
    return header


def parse_ti_payload(packet, header, tlv_header_len):
    """Transform TI payload into objects"""
    objects = np.zeros((header['num_detected_objs'], 6))
    for i in range(header['num_tlvs']):
        tlv_type, tlv_length = struct.unpack('2I', packet[:tlv_header_len])
        if tlv_type > 20 or tlv_length > 10000:
            packet = bytearray([])
            break
        packet = packet[tlv_header_len:]

        if tlv_type == 1:
            for j in range(header['num_detected_objs']):
                x, y, z, v = struct.unpack('4f', packet[:16])
                objects[j, 0] = x
                objects[j, 1] = y
                objects[j, 2] = z
                objects[j, 3] = v
                packet = packet[16:]
        elif tlv_type == 2:
            pass  # unknown
        elif tlv_type == 6:
            pass  # processing time info
        elif tlv_type == 7:
            for j in range(header['num_detected_objs']):
                snr, noise = struct.unpack('2H', packet[:4])
                objects[j, 4] = snr
                objects[j, 5] = noise
                packet = packet[4:]
        elif tlv_type == 9:
            pass  # temperature data
        else:
            print('TLV not recognized: {}'.format(tlv_type))
    payload = {'objects':objects}
    return payload


def convert_payload_to_objects(payload, snr_floor, sensor_ID, noise_xyz, timestamp):
    """Transform payload into objects"""
    converted_objects = []
    objects = payload['objects']
    for i in range(objects.shape[0]):
        if objects[i,4] > snr_floor:
            converted_objects.append(detections.RadarDetection3D_XYZ(
                sensor_ID, timestamp, objects[i,1], -objects[i,0],
                objects[i,2], objects[i,3], noise_xyz, objects[i,4]))
    return converted_objects