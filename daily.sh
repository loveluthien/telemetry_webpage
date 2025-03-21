#!/bin/bash

working_dir=/home/acdc/telemetry_webpage
cd ${working_dir}

sh daily_mongodb_dump.sh
sh extract_users.sh

source ./venv/bin/activate
python preprocess_df.py
python add_date_for_users.py
deactivate

docker cp ./processed_data carta_telemetry_container:/