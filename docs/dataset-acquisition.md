# Phase 1 — Dataset Acquisition

## Approved Window

2024-01-01 through 2024-03-31.

## Sources

### NYC TLC

Source:

https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Dataset:

NYC Yellow Taxi Trip Records

Format:

Parquet

Files:

- yellow_tripdata_2024-01.parquet
- yellow_tripdata_2024-02.parquet
- yellow_tripdata_2024-03.parquet

Purpose:

- batch ingestion
- monthly partitioning
- incremental processing
- schema validation
- data quality
- performance testing

Raw path:

data/raw/tlc/yellow/

---

### NOAA

Source:

https://www.ncei.noaa.gov/access/search/datasets/global-hourly/

Dataset:

NOAA NCEI Global Hourly

Stations:

- 72505394728 — New York Central Park
- 72503014732 — LaGuardia Airport
- 74486094789 — JFK International Airport

Window:

2024-01-01 through 2024-03-31

Raw path:

data/raw/noaa/global_hourly/

---

### OpenAQ

Source:

https://docs.openaq.org/

API:

https://api.openaq.org/v3

Geographic scope:

NYC bounding box.

Window:

2024-01-01 through 2024-03-31

Parameters:

- PM2.5
- PM10
- NO2
- O3
- CO

Authentication:

OPENAQ_API_KEY environment variable.

Pagination:

API pages are retrieved until the final page is reached.

Raw path:

data/raw/openaq/

---

### NYC Taxi Zones

Source:

https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

Lookup:

https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv

Geometry:

https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip

Raw path:

data/raw/taxi_zones/

---

## Raw Data Policy

Raw datasets are never committed to Git.

Only acquisition configuration, acquisition code, validation code and retrieval metadata are committed.

## Validation

Phase 1 validation verifies:

- file existence
- non-zero file size
- SHA-256 checksum
- TLC Parquet schema
- TLC representative records
- NOAA CSV schema
- NOAA representative records
- OpenAQ API response structure
- OpenAQ pagination metadata
- OpenAQ representative records
- taxi-zone lookup schema
- taxi-zone geometry archive
- source metadata