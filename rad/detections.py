# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-02
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-09
# @Description:
"""

"""

import numpy as np


class _RadarDetection():
    def __eq__(self, other):
        return (self._hash == other._hash) and (isinstance(type(self), type(other)))

    def close_to(self, other):
        for k, v in self.__dict__.items():
            if k == '_hash':
                continue
            if v is not None:
                if not np.allclose(v, other.__dict__[k]):
                    return False
        else:
            return True


class RadarDetection3D_XYZ(_RadarDetection):
    """Radar detection class for detections in cartesian coordinates"""

    def __init__(self, source_ID, t, x, y, z, rrt, noise, snr=None):
        """
        r - noise

        Coordinate frame is:
            - x: forward
            - y: left
            - z: up
        """
        self.source_ID = source_ID
        self.t = t
        self.x = x
        self.y = y
        self.z = z
        self.rrt = rrt
        self.noise = noise
        self.snr = snr
        self._hash = hash(f'{self.source_ID} {self.t} {self.x} {self.y} {self.z} {self.rrt} {self.noise} {self.snr}')

    def convert_to(self, format_as='razel', noise=None):
        """Converts the format of detections"""
        if format_as == 'estimators':
            raise NotImplementedError('estimators library is not yet integrated')
            # import estimators
            # new_detection = estimators.measurements.PositionMeasurement_3D_XYZ(
            #     self.source_ID, self.t, r=self.noise, x=self.x, y=self.y, z=self.z)
        elif format_as == 'razel':
            razel = cartesian_to_spherical(np.array([self.x, self.y, self.z]))
            new_detection = RadarDetection3D_RAZEL(self.source_ID, self.t,
                razel[0], razel[1], razel[2], self.rrt, noise, self.snr)
        else:
            raise NotImplementedError(format_as)
        return new_detection


class RadarDetection3D_RAZEL(_RadarDetection):
    """Radar detection class for detections in spherical coordinates"""
    def __init__(self, source_ID, t, rng, az, el, rrt, noise, snr=None):
        self.source_ID = source_ID
        self.t = t
        self.rng = rng
        self.az = az
        self.el = el
        self.rrt = rrt
        self.noise = noise
        self.snr = snr
        self._hash = hash(f'{self.source_ID} {self.t} {self.rng} {self.az} {self.el} {self.rrt} {self.noise} {self.snr}')

    def convert_to(self, format_as, noise=None):
        """Convert the format to some other"""
        if format_as == 'estimators':
            raise NotImplementedError('estimators library is not yet integrated')
            # import estimators
            # new_detection = estimators.measurements.PositionMeasurement_3D_RAZEL(
            #     self.source_ID, self.t, self.noise, rng=self.rng, az=self.az, el=self.el)
        elif format_as == 'cartesian':
            xyz = spherical_to_cartesian(np.array([self.rng, self.az, self.el]))
            new_detection = RadarDetection3D_XYZ(self.source_ID, self.t,
                xyz[0], xyz[1], xyz[2], self.rrt, noise, self.snr)
        else:
            raise NotImplementedError(format_as)
        return new_detection


def spherical_to_cartesian(razel):
    x = razel[0] * np.cos(razel[1]) * np.cos(razel[2])
    y = razel[0] * np.sin(razel[1]) * np.cos(razel[2])
    z = razel[0] * np.sin(razel[2])
    return np.round(np.array([x,y,z]), 6)


def cartesian_to_spherical(v):
    rng = np.linalg.norm(v)
    az = np.arctan2(v[1], v[0])
    el = np.arcsin(v[2]/ rng)
    return np.round(np.array([rng, az, el]), 6)