# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-02
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-02
# @Description:
"""

"""

import rad


def test_init_gui():
    disp = rad.display.SimpleRadarGui()
    disp.close()


def test_show_gui():
    disp = rad.display.SimpleRadarGui()
    radar = rad.interfaces.URadRadar()
    try:
        radar.start()
        n_objs = []
        for i in range(20):
            objects, exit_code = radar()
            n_objs.append(len(objects))
            disp.update(objects)
        assert sum(n_objs) > 0
    finally:
        radar.stop()
        disp.close()