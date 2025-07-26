#!/bin/bash

# daily dump the entries and sessions collections from the mongo backup files and export it to a csv file

# mongo_backup_dir=$(awk -F ":" '/mongo_backup_dir/ {print $2}' config)
# dumped_dir=$(awk -F ":" '/dumped_file_dir/ {print $2}' config)

mongo_backup_dir=/var/www/telemetry ## on server
dumped_dir=/home/acdc/telemetry_webpage/dumped_csv ## on server

today=`date +"%Y_%m_%d"`

# Restore MongoDB backup
mongorestore --host=localhost --port=27017 --gzip --drop --archive="${mongo_backup_dir}/mongo_backup_${today}.tar.gz"

mongoexport --db=carta-telemetry --collection=entries --type=csv --fields=timestamp,sessionId,action,countryCode,ipHash  --out="${dumped_dir}/entries.csv"
mongoexport --db=carta-telemetry --collection=sessions --type=csv --fields=id,userId,version,startTime,endTime,duration,backendPlatform,backendPlatformInfo.distro,backendPlatformInfo.variant,backendPlatformInfo.version  --out="${dumped_dir}/sessions.csv"
mongoexport --db=carta-telemetry --collection=entries --query='{ "action" : "fileOpen"}' --fields=timestamp,countryCode,details.width,details.height,details.depth,details.stokes  --type=csv --out="${dumped_dir}/file_details.csv"
mongoexport --db=carta-telemetry  --collection=entries --query='{ "action" : "spectralProfileGeneration"}' --fields=timestamp,countryCode,details.profileLength,details.regionId,details.width,details.height,details.depth --type=csv  --out="${dumped_dir}/spectralProfileGeneration.csv"