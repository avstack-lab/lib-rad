# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-02
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-02
# @Description:
"""

"""

import numpy as np
import pyqtgraph as pg


class SimpleRadarGui():
    def __init__(self):
        pg.setConfigOption('background', 'w')
        self.MyWindow = pg.GraphicsWindow()
        # self.MyWindow = pg.GraphicsLayoutWidget()
        self.Plot_2D = self.MyWindow.addPlot(title="2D Data")
        self.Plot_2D.setMouseEnabled(x=False, y=False)
        self.Plot_2D.setMenuEnabled(False)
        self.Plot_2D.hideButtons()
        self.Plot_2D.setXRange(-2, 2, padding=0)
        self.Plot_2D.setYRange(0, 5, padding=0)
        self.Plot_2D.setLabel('bottom', 'X (m)')
        self.Plot_2D.setLabel('left', 'Y (m)')
        self.Plot_2D.setAspectLocked()
        self.Plot_2D.showGrid(x=True, y=True)

    def clear(self):
        self.Plot_2D.clear()

    def update(self, objects):
        self.clear()
        if len(objects) > 0:
            x = objects[:, 0]
            y = objects[:, 1]
            snr = objects[:, 4]
            self.Plot_2D.plot(x, y, pen=(0,0,0,0), symbolBrush=(0,0,0,255), symbolSize=np.round((snr-100)/5))
        pg.QtGui.QApplication.processEvents()

    def close(self):
        print('closing dipslay')
        if self.MyWindow is not None:
            self.MyWindow.close()