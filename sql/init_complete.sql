CREATE SEQUENCE seq_station start 1 increment 1;

CREATE TABLE tab_station (
    id INTEGER NOT NULL DEFAULT nextval('seq_station') PRIMARY KEY,
    name TEXT,
    imgw_id INTEGER NOT NULL UNIQUE,
    longitude REAL,
    latitude REAL
);

CREATE UNIQUE INDEX idx_tab_station_imgw_id ON tab_station(imgw_id);

CREATE SEQUENCE seq_station_data start 1 increment 1;

CREATE TABLE tab_station_data (
    id INTEGER NOT NULL DEFAULT nextval('seq_station_data') PRIMARY KEY,
    station_id INTEGER NOT NULL REFERENCES tab_station(id) ON DELETE CASCADE,
    datetime TIMESTAMP, 
    temperature REAL,
    wind_speed INTEGER,
    wind_direction INTEGER,
    humidity REAL,
    precipitation REAL,
    pressure REAL
);

-- not yet created on database
-- CREATE SEQUENCE summary_data_seq start 1 increment 1;

-- CREATE TABLE tab_summary_data (
-- );

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pablo;