import os
import time
import json
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS

from scripts.sensor import AQM
import logging
from logging.handlers import RotatingFileHandler


HOMEDIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = '/home/richard/influx.secret'
os.environ['BLINKA_FT232H']='1'

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
    token = open(TOKEN_FILE,'r').read().strip()

    def openInflux():
        logger.info("Opening influx session")
        client =  InfluxDBClient(url='https://127.0.0.1:8086', verify_ssl=False, token = token, org='orgname')
        writer = client.write_api(write_options=SYNCHRONOUS)
        return client, writer
    influx_client, influx_writer = openInflux()

    try:
        writeRetries = 0
        while True:
            sample = aqm.sample()
            if sample is not None:
                sample[0]['fields']['temperature'] =  float(sample[0]['fields']['temperature'] * 9.0/5.0) + 32.0
                try:
                    influx_writer.write('aqm', 'orgname', sample)
                    writeRetries = 0
                except Exception:
                    logger.exception("Got exception")
                    writeRetries += 1
                if writeRetries == 5:
                    logger.error("Couldn't write to influxdb")
                    influx.close()
                    influx_client, influx_writer = openInflux()
                time.sleep(5)
    
    except Exception as e:
        logger.exception('Encountered exception in AQM')
        raise

    finally:
        influx_client.close()

if __name__ == '__main__':
    main()
