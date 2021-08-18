import subprocess
import json
import threading
import io
import multiprocessing
import time

class BME680(object):
    data = None

    def __init__(self, readfrom):
        if readfrom == 'bme680secondary':
            self.command = ['/usr/src/app/bsec_bme680_linux/bsec_bme680', 'secondary']
        else:
            self.command = ['/usr/src/app/bsec_bme680_linux/bsec_bme680']

        self.capture_thread = threading.Thread(target=self.capturewrap)
        self.capture_thread.start()

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

    def capture(self):
        # Start the process and commence capture and parsing of the output
        process = subprocess.Popen(self.command, stdout=subprocess.PIPE)

        for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
            self.data = json.loads(line.strip())

        rc = process.poll()
        time.sleep(2)
        print('captured')
        return rc

    def get_readings(self, sensor):
        if self.data:
            return [
                {
                    'measurement': 'BME680',
                    'fields': {
                        'temperature': float(self.data['temperature']),
                        'pressure': float(self.data['pressure']),
                        'humidity': float(self.data['humidity']),
                        'air_quality_score': float(self.data['iaq']),
                        'air_quality_score_accuracy': int(self.data['iaq_accuracy']),
                        'eco2_ppm': float(self.data['eco2_ppm']),
                        'bvoce_ppm': float(self.data['bvoce_ppm'])
                    }
                }
            ]
        else:
            return None
