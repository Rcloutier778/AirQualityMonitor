import os

import sys
import time
import os
import json

TEMPERATURE_OFFSET = 0.0
HUMIDITY_OFFSET = 0.0
ALTITUDE = 0.0

class AQM():

    def __init__(self):
        from .bme680 import BME680
        self.sensor = BME680()

    def sample(self):
        return self.apply_offsets(self.sensor.get_readings())


    def apply_offsets(self, measurements):
        if not measurements:
            return None
        # Apply any offsets to the measurements before storing them in the database
        measurements[0]['fields']['temperature'] = measurements[0]['fields']['temperature'] + TEMPERATURE_OFFSET
        measurements[0]['fields']['humidity'] = measurements[0]['fields']['humidity'] + HUMIDITY_OFFSET
        # if there's an altitude set (in meters), then apply a barometric pressure offset
        measurements[0]['fields']['pressure'] = measurements[0]['fields']['pressure'] * (1-((0.0065 * ALTITUDE) / (measurements[0]['fields']['temperature'] + (0.0065 * ALTITUDE) + 273.15))) ** -5.257

        return measurements


