#!/bin/bash

sh daily_mongodb_dump.sh
sh extract_users.sh

source ./venv/bin/activate
python preprocess_df.py
python add_date_for_users.py
deactivate

docker cp ./processed_data carta_telemetry_container:processed_data