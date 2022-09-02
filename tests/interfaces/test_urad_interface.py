# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-01
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-02
# @Description:
"""

"""

import rad


def test_urad_start_stop():
    radar = rad.interfaces.URadRadar()
    try:
        radar.start()
    finally:
        radar.stop()


def test_urad_get_detections():
    radar = rad.interfaces.URadRadar(verbose=True)
    try:
        radar.start()
        n_objs = []
        for _ in range(10):
            objects, exit_code = radar()
            assert exit_code in [0, 1]
            n_objs.append(len(objects))
        assert sum(n_objs) > 0
    finally:
        radar.stop()