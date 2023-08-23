#!/bin/sh
# Create service databases and users.
setup_service_db() {
  # args:
  # $1 - service name, used for DB and user name
  # $2 - password
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE USER $1 WITH PASSWORD '$2';
	CREATE DATABASE $1 OWNER $1;
EOSQL
}

setup_service_db 'auth' 'auth-top-secret'
setup_service_db 'task_tracker' 'task_tracker-top-secret'
setup_service_db 'accounting' 'accounting-top-secret'
setup_service_db 'analytics' 'analytics-top-secret'
