# Urban Mobility & Environmental Intelligence Platform

Enterprise-grade data platform for urban mobility and environmental intelligence.

## Approved Data Sources

- NYC TLC trip records
- NYC-area NOAA weather observations
- NYC-area OpenAQ measurements
- NYC taxi-zone/geospatial reference data

## Technology Scope

- Python
- SQL
- PySpark
- AWS S3
- Apache Iceberg
- Apache Airflow
- dbt
- Snowflake
- Docker
- Git/GitHub
- GitHub Actions
- Data Quality
- Testing
- Terraform
- AWS IAM
- Selective Kafka / Spark Structured Streaming

## Repository Structure

```text
.github/workflows/   CI workflows
configs/             Configuration
data/                Local data directories; raw/generated data is gitignored
docs/                Engineering documentation
infrastructure/      Infrastructure as Code
scripts/             Operational and validation scripts
src/urban_mobility/  Application source code
tests/               Automated tests
