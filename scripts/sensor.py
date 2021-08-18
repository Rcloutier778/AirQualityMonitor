# This script detects for the presence of either a BME680 sensor on the I2C bus or a Sense HAT
# The BME680 includes sensors for temperature, humidity, pressure and gas content
# The Sense HAT does not have a gas sensor, and so air quality is approximated using temperature and humidity only.
import os

import sys
import time
import smbus
import os
import json


class AQM():
    readfrom = 'unset'
    bus = smbus.SMBus(1)

    def __init__(self):
        
        from .bme680 import BME680
        # Next, check to see if there is a BME680 on the I2C bus
        if self.readfrom == 'unset':
            try:
                self.bus.write_byte(0x76, 0)
            except IOError:
                print('BME680 not found on 0x76, trying 0x77')
            else:
                print('BME680 found on 0x76')

                self.readfrom = 'bme680primary'
                self.sensor = BME680(self.readfrom)

        # If we didn't find it on 0x76, look on 0x77
        if self.readfrom == 'unset':
            try:
                self.bus.write_byte(0x77, 0)
            except IOError:
                print('BME680 not found on 0x77')
            else:
                print('BME680 found on 0x77')
                self.readfrom = 'bme680secondary'
                self.sensor = BME680(self.readfrom)

        # If no BME680, is there a Sense HAT?
        if self.readfrom == 'unset':
            try:
                self.bus.write_byte(0x5F, 0)
            except:
                print('Sense HAT not found')
            else:
                self.readfrom = 'sense-hat'
                print('Using Sense HAT for readings (no gas measurements)')

                # Import the sense hat methods
                import sense_hat_air_quality
                from hts221 import HTS221
                self.sense_hat_reading = lambda: sense_hat_air_quality.get_readings(HTS221())


        # If this is still unset, no sensors were found; quit!
        if self.readfrom == 'unset':
            print('No suitable sensors found! Exiting.')
            sys.exit()

    def sample(self):
        if self.readfrom == 'sense-hat':
            return self.apply_offsets(self.sense_hat_reading())
        else:
            return self.apply_offsets(self.sensor.get_readings(self.sensor))


    def apply_offsets(self, measurements):
        # Apply any offsets to the measurements before storing them in the database
        if os.environ.get('BALENASENSE_TEMP_OFFSET') != None:
            measurements[0]['fields']['temperature'] = measurements[0]['fields']['temperature'] + float(os.environ['BALENASENSE_TEMP_OFFSET'])

        if os.environ.get('BALENASENSE_HUM_OFFSET') != None:
            measurements[0]['fields']['humidity'] = measurements[0]['fields']['humidity'] + float(os.environ['BALENASENSE_HUM_OFFSET'])

        if os.environ.get('BALENASENSE_ALTITUDE') != None:
            # if there's an altitude set (in meters), then apply a barometric pressure offset
            altitude = float(os.environ['BALENASENSE_ALTITUDE'])
            measurements[0]['fields']['pressure'] = measurements[0]['fields']['pressure'] * (1-((0.0065 * altitude) / (measurements[0]['fields']['temperature'] + (0.0065 * altitude) + 273.15))) ** -5.257

        return measurements


