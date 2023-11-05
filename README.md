# solarmeteo
It stores current meteorological and photovoltaic installation data, which can be further
used to analyze the correlation between weather conditions and power generation in private photovoltaic installation.

- Meteo data is taken from IMGW server.<br>
- Solar data is taken from SolarEdge™ server using their API.
  :bulb: To use this feature it's necessary to have SolarEdge™
  photovoltaic installation with site_id and generated key_id on https://monitoring.solaredge.com

SolarMeteo stores data for either meteo or solar in separate application calls.
<p align="center">
<img src="https://github.com/pa810p/solarmeteo/assets/46489402/02255b3a-5bfb-4e47-8041-19b9b4b41159"></p>

## Installation

### Prerequisites

#### Postgresql installation or access to database

#### Python libraries listed below:

- configparser
- backports-ssl-match-hostname
- sqlalchemy
- psycopg2
- requests
- sqlalchemy2
- mockito

### Create database schema using alembic

1. Copy alembic.ini.template to alembic.ini
````shell
$ cp alembic.ini.template alembic.ini
````
2. Edit **postgresql database** section:
````shell
$ vim alembic.ini
````
:bulb: **meteo_environment** is a property means the environment for which configuration is made.
It was intended to have few environments: dev (development), test (testing) and production (live service).
For example production database name is: **meteo**, development database name is **meteo_dev**, database used for
testing is named: **meteo_test**.

3. Initialize database schema and make upgrade to latest revision:
````shell
$ alembic -c alembic.ini upgrade head
````

### Configure solar meteo properties

1. Copy meteo.properties.template to meteo.properties
````shell
$ cp meteo.properties.template meteo.properties
````
2. Edit database properties like:
- host
- port
- user
- password
- environment
````shell
$ vim meteo.properties
````

## Testing

### Configure solar meteo test properties

1. Copy meteo.properties.template to meteo_test.properties
````shell
$ cp meteo.properties.template meteo_test.properties
````
2. Edit database properties like:
- host
- port
- user
- password
- environment = _test (:bulb: for testing use **_test**)
````shell
$ vim meteo.properties
````

### Run tests
Execute:
````shell
$ python3 -m unittest discover -p 'Test*.py' -v  ./test
````

## Usage
The best idea of storing data in meteo database is to launch solarmeteo from crontab:
````shell
$ crontab -e
````
and add following lines to it:
````shell
20 * * * * cd ~/solarmeteo; python3 solarmeteo.py -u imgw   >/dev/null 2>&1
*/15 * * * * cd ~/solarmeteo; python3 solarmeteo.py -u solar   >/dev/null 2>&1
````
:bulb: assumed that solarmeteo folder is in $HOME directory.
Above crontab configuration means that external services will be called:
- meteo: every full hour plus 20 minutes
- solar: every 15 minutes

## Reports

### Useful queries
#### Select 5 days with the best amount of generated power lifetime:
````sql
SELECT to_char(power, '00.000') || ' kWh' AS power, date FROM
(
  SELECT max(summary.power)::float/1000 AS power, summary.date AS date FROM 
  (
    SELECT sum(power)/4 AS power, datetime::date AS date
    FROM solar_data GROUP by date
  ) summary
  GROUP BY date 
) result
ORDER BY power DESC;
````
#### Select 5 days with the best amount of generated power lifetime limited only to 2022 year:
````sql
SELECT to_char(power, '00.000') || ' kWh' AS power, date FROM
(
  SELECT max(summary.power)::float/1000 AS power, summary.date AS date FROM 
  (
    SELECT sum(power)/4 AS power, datetime::date AS date
    FROM solar_data GROUP by date
  ) summary
  GROUP BY date 
) result  WHERE date BETWEEN '2022-01-01' AND '2023-01-01'
ORDER BY power DESC 
LIMIT 5;
````
#### Select last meteo conditions in given cities:
````sql
SELECT name AS city, to_char(datetime::time,'HH24:MI') as time, 
  to_char(temperature, '90.9') || '°C' AS temp,
  wind_speed || 'kt' || to_char(wind_speed * 0.5144444445610519, '0.0') || 'm/s' AS wind_speed,
  wind_direction || '°' AS dir, to_char(pressure, '0000.0') || ' hPa' AS pressure,
  to_char(humidity, '00.0') || '%' AS humid, precipitation AS prec
FROM station_data INNER JOIN station ON (station.id=station_data.station_id)
WHERE name IN ('Kraków', 'Warszawa', 'Kielce', 'Gdańsk', 'Wrocław', 'Szczecin', 'Poznań')
ORDER BY datetime DESC, temperature DESC, city LIMIT 7;
````
#### meteo conditions for last 12 hours for Kraków:
````sql
SELECT name AS city, to_char(datetime::time,'HH24:MI') as time, to_char(temperature, '90.9') || '°C' AS temp, 
  wind_speed || 'kt' || to_char(wind_speed * 0.5144444445610519, '0.0') || 'm/s' AS wind_speed, 
  to_char(wind_direction, '000') || '°' AS dir, to_char(pressure, '0000.0') || ' hPa' AS pressure, 
  to_char(humidity, '00.0') || '%' AS humid, precipitation AS prec 
FROM station_data INNER JOIN station ON (station.id=station_data.station_id) 
WHERE name IN ('Kraków') 
ORDER BY datetime DESC, wind_speed DESC, city LIMIT 12;
````

### Grafana (screenshots)
<p aligh="center">
<img src="https://github.com/pa810p/solarmeteo/assets/46489402/0b23ee81-c7a4-4dc0-81b0-f1126febb1cf" width="902">
<img src="https://github.com/pa810p/solarmeteo/assets/46489402/716d015d-0f81-4a56-b2e6-41a73630d28b" width="902">
</p>

## TODO

- remove orphaned -t option from code
- dockerize components
    - postgresql
    - solarmeteo
- dockerize environments
    - dev
    - test
    - production
    - run tests in crontab and report tests results
- add azimuth and height of a sun to database (:bulb: as separate method in relations to meteo and solar tables)
- add more documentation and examples of use solarmeteo
- fix daemonize mode
- long term feature:
    - adapt existing code to be able to receive data from another services
        - openweather?

