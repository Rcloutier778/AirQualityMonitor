# AirQualityMonitor
Small air quality monitoring script.

Uses a BME680 sensor to detect temperature, humidity, pressure, CO2, and VOC (volitile organic compound) levels, 
to calculate an indoor air quality. Stores all data in an InfluxDB time series database and displays it on a Grafana dashboard.
![image](https://user-images.githubusercontent.com/20069910/131231440-80c1226a-7fd9-4650-baab-40c2b79e3116.png)
