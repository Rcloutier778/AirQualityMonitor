import subprocess
import json
import threading
import io
import multiprocessing as mp
import time
import os

import board
import adafruit_bme680

#NOTE:
# I lost whatever C magic I got from BOSCH when my raspberry pi died, and don't care
#   to go through re-implementing that, so I'm just going to go with the library 
#   Adafruit provides. Personally I think the python for microcontrollers / SBCs they
#   push is really stupid and would rather have had it implemented in C but hey
#   it's free and I'm not running this on a raspberry pi anymore so whatever. 


# Weights on air quality score
GAS_WEIGHT = 0.75
HUM_WEIGHT = 0.25

HUM_REF = 40
GAS_REF = 2500

GAS_UPPER_LIMIT = 300000
GAS_LOWER_LIMIT = 10000

SEA_LEVEL_PRESSURE = 1013.25

TEMPERATURE_OFFSET = 0.0
HUMIDITY_OFFSET = 0.0
ALTITUDE = 0.0

class BME680(object):
    i2c = None
    bme = None
    gas_reference = GAS_REF
    pipe = None

    data = None


    def __init__(self, threadit=True):
        self.threadit = threadit
        if threadit:
            self.capture_thread = threading.Thread(target=self.capturewrap, daemon=True)
            self.capture_thread.start()

    def calibrate(self):
        numReadings = 10
        for _ in range(numReadings):
            self.gas_reference += self.bme.gas
            time.sleep(0.0015)
        self.gas_reference = self.gas_reference / numReadings

    def calc_IAQ(self, humid):

        # Calculate humidity contribution to IAQ Index
        if humid >= 38 and humid <= 42:
            # +/- 5% around optimum
            hum_score = 25.0
        else:
            # sub optimal
            if humid < 38:
                hum_score = HUM_WEIGHT / HUM_REF * humid * 100
            else:
                hum_score = ((-HUM_WEIGHT/(100-HUM_REF)*humid)+0.416666)*100

        # Calculate gas contribution to IAQ
        if self.gas_reference > GAS_UPPER_LIMIT:
            self.gas_reference = GAS_UPPER_LIMIT
        if self.gas_reference < GAS_LOWER_LIMIT:
            self.gas_reference = GAS_LOWER_LIMIT
        gas_score = (GAS_WEIGHT/(GAS_UPPER_LIMIT-GAS_LOWER_LIMIT)*self.gas_reference -(GAS_LOWER_LIMIT*(GAS_WEIGHT/(GAS_UPPER_LIMIT-GAS_LOWER_LIMIT))))*100.0;
        score = (100 - (hum_score + gas_score)) * 5
        return score, hum_score, gas_score

    def capture(self):
        self.i2c = board.I2C()
        self.bme = adafruit_bme680.Adafruit_BME680_I2C(self.i2c)
        self.bme.sea_level_pressure = SEA_LEVEL_PRESSURE
        self.calibrate()

        numReadings = 5
        while True:
            temp, humid, pressure = 0, 0,  0
            for _ in range(numReadings):
                temp += self.bme.temperature
                humid += self.bme.humidity
                self.gas_reference += self.bme.gas
                pressure += self.bme.pressure
                time.sleep(1)
            self.gas_reference /= numReadings
            temp /= numReadings
            humid /= numReadings
            pressure /= numReadings
            iaq, hum_score, gas_score = self.calc_IAQ(humid)

            temp += TEMPERATURE_OFFSET
            pressure = pressure * (1-((0.0065 *   ALTITUDE) / (temp + (0.0065 * ALTITUDE) + 273.15))) ** -5.257
            # Convert to F after pressure adjustment
            temp = (temp * 9.0/5.0) + 32.0

            humid += HUMIDITY_OFFSET

            result = {
                    'temperature': temp,
                    'pressure': pressure,
                    'iaq': iaq,
                    'humidity': humid,
                    'bvoce_ppm': self.gas_reference,
                    'hum_score': hum_score,
                    'gas_score': gas_score,
                    }
            self.data = result
            if not self.threadit:
                print(result)

    def capturewrap(self):
        while True:
            try:
                self.capture()
                print(self.data)
            except BaseException as e:
                print('{!r}; restarting capture thread'.format(e))
            else:
                print('Capture thread exited; restarting')
            time.sleep(5)

    def get_readings(self):
        if self.data:
            return {
                    'measurement': 'BME680',
                    'fields': {
                        'temperature': float(self.data['temperature']),
                        'pressure': float(self.data['pressure']),
                        'humidity': float(self.data['humidity']),
                        'air_quality_score': float(self.data['iaq']),
                        #'air_quality_score_accuracy': int(self.data['iaq_accuracy']),
                        #'eco2_ppm': float(self.data['eco2_ppm']),
                        'bvoce_ppm': float(self.data['bvoce_ppm']),
                        'hum_score': float(self.data['hum_score']),
                        'gas_score': float(self.data['gas_score']),
                    }
                }
        else:
            return None


if __name__ == "__main__":
    bme = BME680(False)
    bme.capture()
    while True:
        print( bme.get_readings() )
        time.sleep(5)

