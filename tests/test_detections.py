# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-02
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-02
# @Description:
"""

"""

import rad


def test_xyz_to_razel():
    noise_cart = [1, 2, 3]
    d_xyz = rad.detections.RadarDetection3D_XYZ(1, 1.0, 2.3, -2.1, 3.0, 2.0, noise_cart, 22)
    d_razel = d_xyz.convert_to('razel', noise=[1, 1e-2, 2e-2])
    d_xyz_2 = d_razel.convert_to('cartesian', noise=noise_cart)
    assert d_xyz.close_to(d_xyz_2)