#!/bin/bash
set -e

# Create multiple databases
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create Airflow database
    CREATE DATABASE airflow;
    GRANT ALL PRIVILEGES ON DATABASE airflow TO $POSTGRES_USER;

    -- Create test database
    CREATE DATABASE test_medisafe;
    GRANT ALL PRIVILEGES ON DATABASE test_medisafe TO $POSTGRES_USER;
EOSQL

echo "Multiple databases created successfully"
