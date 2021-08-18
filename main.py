import os
import time
import json
from influxdb import InfluxDBClient
from scripts.sensor import AQM
import logging
from logging.handlers import RotatingFileHandler


HOMEDIR = os.path.dirname(os.path.abspath(__file__))
PW_FILE = os.path.join(HOMEDIR,'influx.secret')

def main():
    logfile = os.path.join(HOMEDIR, 'log.log')
    logging.basicConfig(
        filename=logfile,
        filemode='a',
        format='%(asctime)s %(name)s %(levelname)s %(message)s',
        level=logging.INFO)
    logger = logging.getLogger('aqm')
    logger.addHandler(RotatingFileHandler(logfile, maxBytes=1024*1024*5, delay=0, mode='a'))
    logger.info('Starting AQM')

    aqm = AQM()
    password = open(PW_FILE,'r').read().strip()

    def openInflux():
        return InfluxDBClient(database='aqm', host='127.0.0.1', port=8086, username='admin', password = password)
    influx = openInflux()

    try:
        writeRetries = 0
        while True:
            sample = aqm.sample()
            if sample is not None:
                sample[0]['fields']['temperature'] =  float(sample[0]['fields']['temperature'] * 9.0/5.0) + 32.0
                try:
                    influx.write_points(sample)
                    writeRetries = 0
                except Exception:
                    writeRetries += 1
                if writeRetries == 5:
                    logger.error("Couldn't write to influxdb")
                    influx.close()
                    influx = openInflux()
                time.sleep(5)
    
    except Exception as e:
        logger.exception('Encountered exception in AQM')
        raise

    finally:
        influx.close()

if __name__ == '__main__':
    main()
