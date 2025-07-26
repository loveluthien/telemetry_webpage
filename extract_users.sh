#!/bin/bash

# this script is used to extract the users collection from the mongo backup files
# and export it to a csv file

# Define backup directory
mongo_backup_dir="/var/www/telemetry" ## on server
# mongo_backup_dir="../" ## in local
dumped_dbfiles_dir="./users_csv"

# Get latest database backup files
dbfile=($(cd "$mongo_backup_dir" && ls -1t *.tar.gz))

# Get latest dumped CSV files and extract date patterns
dumped_dbfiles=($(cd ${dumped_dbfiles_dir} && ls -1t *.csv))
dumped_dates=()
for csv in "${dumped_dbfiles[@]}"; do
    date_pattern=$(echo "$csv" | grep -oE '[0-9]{4}_[0-9]{2}_[0-9]{2}')
    if [[ -n "$date_pattern" ]]; then
        dumped_dates+=("$date_pattern")
    fi
done

# Iterate over backup files
for file in "${dbfile[@]}"
do
    # Extract the date pattern from the filename
    date_pattern=$(echo "$file" | grep -oE '[0-9]{4}_[0-9]{2}_[0-9]{2}')

    # Skip if no date is found
    if [[ -z "$date_pattern" ]]; then
        echo "No date pattern found in $file, skipping..."
        continue
    fi

    # Skip if this date already exists in dumped CSV files
    if [[ " ${dumped_dates[*]} " =~ " ${date_pattern} " ]]; then
        # echo "Backup for date $date_pattern already processed. Skipping..."
        continue
    fi

    echo "Processing backup for date: $date_pattern"

    # Restore MongoDB backup
    mongorestore --db=carta-telemetry --collection=users --host=localhost --port=27017 --gzip --drop --archive="${mongo_backup_dir}/mongo_backup_${date_pattern}.tar.gz"

    # Export users collection to CSV
    mongoexport --db=carta-telemetry --collection=users --type=csv --fields=_id,uuid,countryCode,optOut,regionCode --out="${dumped_dbfiles_dir}/users_${date_pattern}.csv"
done