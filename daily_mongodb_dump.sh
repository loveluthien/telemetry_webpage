#!/bin/bash

# daily dump the entries and sessions collections from the mongo backup files and export it to a csv file

# mongo_backup_dir="/var/www/telemetry" ## on server
mongo_backup_dir="/Users/kchou/bz/telemetry" ## in local
dumped_dir="/Users/kchou/bz/telemetry/plot-telemetry-v2/dumped_csv"  ## in local
today=`date +"%Y_%m_%d"` 

# Restore MongoDB backup
# mongorestore --host=localhost --port=27017 --gzip --drop --archive="${mongo_backup_dir}/mongo_backup_${today}.tar.gz"
mongorestore --host=localhost --port=27017 --gzip --drop --archive="${mongo_backup_dir}/mongo_backup_2025_02_28.tar.gz"

mongoexport --db=carta-telemetry --collection=entries --type=csv --fields=timestamp,id,sessionId,version,action,countryCode,ipHash  --out="${dumped_dir}/entries.csv"
mongoexport --db=carta-telemetry --collection=sessions --type=csv --fields=id,userId,version,startTime,endTime,duration,backendPlatform,backendPlatformInfo.distro,backendPlatformInfo.variant,backendPlatformInfo.version  --out="${dumped_dir}/sessions.csv"
mongoexport --db=carta-telemetry --collection=entries --query='{ "action" : "fileOpen"}' --fields=timestamp,id,sessionId,countryCode,details.width,details.height,details.depth,details.stokes  --type=csv --out="${dumped_dir}/file_details.csv"
mongoexport --db=carta-telemetry  --collection=entries --query='{ "action" : "spectralProfileGeneration"}' --fields=timestamp,id,sessionId,countryCode,details.profileLength,details.regionId,details.width,details.height,details.depth --type=csv  --out="${dumped_dir}/spectralProfileGeneration.csv"