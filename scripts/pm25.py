import json
import threading
import time
import serial
from adafruit_pm25.uart import PM25_UART

#ppm
PM25_CONC_RANGES  = [(0.0, 12.0), (12.0, 35.4), (35.4, 55.4), (55.4, 150.4), (150.5, 250.4), (250.4, 500.4)]
PM100_CONC_RANGES = [(0, 54), (54, 154), (154, 254), (254, 354), (354, 424), (425, 604)]

AQI_RANGES = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 300), (300, 500)]

class PM25(object):
    def __init__(self, threadit=True):
        self.data = None
        if threadit:
            self.capture_thread = threading.Thread(target=self.capturewrap, daemon=True)
            self.capture_thread.start()
    
    def _calcAQI(self, pm, pmRange):
        #https://forum.airnowtech.org/t/the-aqi-equation/169
        for idx, (conc_low, conc_high) in enumerate(pmRange):
            if conc_low <= pm <= conc_high:
                break
        else:
            # Above max
            conc_low, conc_high = pmRange[-1]
            idx = len(pmRange) - 1
        aqi_low, aqi_high = AQI_RANGES[idx]

        return aqi_low + (((aqi_high - aqi_low) * (pm - conc_low)) / (conc_high - conc_low))

    def calcAQI(self, pm10, pm25, pm100):
        aqi25 = self._calcAQI(pm25, PM25_CONC_RANGES)
        aqi100 = self._calcAQI(pm10, PM100_CONC_RANGES)

        aqi = (aqi25 + aqi100) / 2.0
        return aqi, aqi25, aqi100



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
                    'measurement': 'PM25',
                    'fields': {
                        'air_quality_score': float(self.data['aqi']),
                        #'air_quality_score_pm10': float(self.data['aqi10']),
                        'air_quality_score_pm25': float(self.data['aqi25']),
                        'air_quality_score_pm100': float(self.data['aqi100']),
                        'pm10': float(self.data['pm10 standard']),
                        'pm25': float(self.data['pm25 standard']),
                        'pm100': float(self.data['pm100 standard']),
                        # Number of particles > X micro meters per 0.1 L of air. 
                        'particles_03um' : int(self.data['particles 03um']),
                        'particles_05um' : int(self.data['particles 05um']),
                        'particles_10um' : int(self.data['particles 10um']),
                        'particles_25um' : int(self.data['particles 25um']),
                        'particles_50um' : int(self.data['particles 50um']),
                        'particles_100um' : int(self.data['particles 100um']),


                    }
                }
        else:
            return None

    def capture(self):
        #NOTE might need to manually remove digitalio imports 
        uart = serial.Serial("/dev/ttyUSB1", baudrate=9600, timeout=0.25)
        pm25 = PM25_UART(uart)

        while True:
            try:
               data = pm25.read()
            except RuntimeError as e:
                print("Got runtime error, retrying without restart")
                print(e)
                continue

            aqi, aqi25, aqi100 = self.calcAQI(float(data["pm10 standard"]), float(data["pm25 standard"]), float(data["pm100 standard"]))
            data['aqi'] = aqi
            data['aqi25'] = aqi25
            data['aqi100'] = aqi100

            self.data = data
            print(data)
            time.sleep(1)

if __name__ == "__main__":
    pm25 = PM25(False)
    pm25.capture()
    while True:
        print(pm25.get_readings())
        time.sleep(1)
