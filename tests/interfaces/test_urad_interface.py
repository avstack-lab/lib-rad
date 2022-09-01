# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-01
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-01
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
