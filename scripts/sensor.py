import os

import sys
import time
import os
import json

class AQM():

    def __init__(self):
        self.sensors = []

        from .bme680 import BME680
        self.sensors.append( BME680() )

        from .pm25 import PM25
        self.sensors.append( PM25() )

    def sample(self):
        res = []
        for sensor in self.sensors:
            meas = sensor.get_readings()
            if meas:
                res.append(meas)

        return res
