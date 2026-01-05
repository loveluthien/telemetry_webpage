import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
from pycountry_convert import country_alpha2_to_country_name
import configparser

configParser = configparser.ConfigParser()
configParser.read('config')
users_csv_dir = configParser.get('PATH', 'users_csv_dir')
dumped_file_dir = configParser.get('PATH', 'dumped_file_dir')

today = datetime.today().date()
# today = date(2025, 2, 28)
init_date = date(2021, 12, 1)

#### load data ####
# Load CSV data
users_df = pd.read_csv(f"{dumped_file_dir}/users_with_date.csv")
sessions_df = pd.read_csv(f"{dumped_file_dir}/sessions.csv")
entries_df = pd.read_csv(f"{dumped_file_dir}/entries.csv")
files_df = pd.read_csv(f"{dumped_file_dir}/file_details.csv")
spectral_df = pd.read_csv(f"{dumped_file_dir}/spectralProfileGeneration.csv")

# process date information 
users_df['datetime'] = pd.to_datetime(users_df.date, format='mixed')
sessions_df['datetime'] = pd.to_datetime(sessions_df.startTime, unit='ms')
entries_df['datetime'] = pd.to_datetime(entries_df.timestamp, unit='ms')
files_df['datetime'] = pd.to_datetime(files_df.timestamp, unit='ms')
spectral_df['datetime'] = pd.to_datetime(spectral_df.timestamp, unit='ms')

users_df.drop(columns=['date'], inplace=True)
sessions_df.drop(columns=['startTime'], inplace=True)
entries_df.drop(columns=['timestamp'], inplace=True)
files_df.drop(columns=['timestamp'], inplace=True)
spectral_df.drop(columns=['timestamp'], inplace=True)

# process file type
r_width = files_df['details.width'] > 1
r_height = files_df['details.height'] > 1
r_depth = files_df['details.depth'] > 1
r_stokes = files_df['details.stokes'] > 1

stokes_4d = r_width & r_height & r_depth & r_stokes
stokes_3d = r_width & r_height & r_stokes & ~stokes_4d
three_dim = r_width & r_height & r_depth & ~stokes_4d  & ~stokes_3d
two_dim = r_width & r_height & ~stokes_4d  & ~stokes_3d & ~three_dim

files_df.loc[two_dim ,'file_type'] = '2D'
files_df.loc[three_dim ,'file_type'] = '3D'
files_df.loc[stokes_3d ,'file_type'] = '2D+Stokes'
files_df.loc[stokes_4d ,'file_type'] = '3D+Stokes'

files_df['fileSize'] = files_df['details.width'] * files_df['details.height'] * files_df['details.depth'] * files_df['details.stokes'] * 4 / 1024**2 # in MB

size_range = [0, 1, 10, 100, 1024, 10240, 102400, 1024**2, 1024**2*10] # in MB
size_label = ["<1MB", "1MB-10MB", "10MB-100MB", "100MB-1GB", "1GB-10GB", "10GB-100GB", "100GB-1TB", "1TB-10TB"] # in MB

for i in range(len(size_range)-1):
    r = (files_df['fileSize'] > size_range[i]) & (files_df['fileSize'] <= size_range[i+1])
    files_df.loc[r, 'size_label'] = size_label[i]


# process OS version
OS_version_array = []
OS_array = []
for i in range(sessions_df.__len__()):
    OS_version = sessions_df['backendPlatformInfo.version'].iloc[i]

    if sessions_df['backendPlatform'].iloc[i] == 'macOS':
        OS_version_array.append(OS_version.split('.')[0])
        OS_array.append(sessions_df['backendPlatform'].iloc[i])
    else:
        OS_version_array.append(OS_version)
        OS = str(sessions_df['backendPlatformInfo.distro'].iloc[i])
        OS_array.append(OS.split(' ')[0])

OS_array = np.array(OS_array)
r = np.where(OS_array == 'Debian')[0]
OS_array[r] = 'Debian GNU'
r = np.where((OS_array == 'Red') | (OS_array == 'RHEL'))[0]
OS_array[r] = 'Red Hat'
r = np.where(OS_array == 'Trisquel')[0]
OS_array[r] = 'Trisquel GNU'
r = np.where(OS_array == 'Linux')[0]
OS_array[r] = 'Linux Mint'

sessions_df['OS_version'] = OS_version_array
sessions_df['OS'] = OS_array

sessions_df.drop(columns=['backendPlatformInfo.version', 'backendPlatformInfo.distro', 'backendPlatformInfo.variant'], inplace=True)


# process country information
users_df['country'] = users_df[~users_df.countryCode.isnull()].countryCode.apply(lambda x: country_alpha2_to_country_name(x))
users_df.loc[users_df.countryCode == 'TW' ,'country'] = 'Taiwan'
# users_df.drop(columns=['countryCode'], inplace=True)

temp = entries_df[['sessionId', 'countryCode']].drop_duplicates(subset=['sessionId'])
sessions_df = sessions_df.merge(temp, left_on='id', right_on='sessionId', how='left')
sessions_df['country'] = sessions_df[~sessions_df.countryCode.isnull()].countryCode.apply(lambda x: country_alpha2_to_country_name(x))
sessions_df.loc[sessions_df.countryCode == 'TW' ,'country'] = 'Taiwan'
# sessions_df.drop(columns=['countryCode'], inplace=True)


## to find the missing data dates 
def extract_missing_data_dates():

    selected_index = (entries_df['datetime'] > init_date.strftime('%Y-%m-%d')) & (entries_df['datetime'] <= today.strftime('%Y-%m-%d'))
    resample_dates = entries_df[selected_index].resample('d', on='datetime')
    date_counts = resample_dates.apply(lambda x: x.ipHash.unique().size)

    ## modify here ##
    xmas_newyear_holidays = ['12-24', '12-25', '12-26', '12-27', '12-28', '12-29', '12-30', '12-31', '01-01', '01-02', '01-03', '01-04', '01-05']
    unusual_threshold = {'2021': {'workday': 0, 'holiday': 0}, 
                        '2022': {'workday': 0, 'holiday': 0}, 
                        '2023': {'workday': 60, 'holiday': 20}, 
                        '2024': {'workday': 80, 'holiday': 30}, 
                        '2025': {'workday': 100, 'holiday': 40}}
    # if year is not listed, use the last year threshold
    for year in range(2026, today.year + 1):
        unusual_threshold[f'{year}'] = unusual_threshold[f'{year-1}']
    ## modify here ##

    missing_data = []
    for i in range((today - init_date).days):
        current_date = init_date + timedelta(days=i)
        formatted_date = f"{current_date.year}-{current_date.month:02d}-{current_date.day:02d}"

        if not formatted_date in date_counts.keys():
            continue

        if (f"{current_date.month:02d}-{current_date.day:02d}" in xmas_newyear_holidays) | (current_date.weekday() in [5, 6]):
            if date_counts[formatted_date] < unusual_threshold[f'{current_date.year}']['holiday']:
                missing_data.append(formatted_date)
        else:
            if date_counts[formatted_date] < unusual_threshold[f'{current_date.year}']['workday']:
                missing_data.append(formatted_date)

    return pd.DataFrame(pd.to_datetime(missing_data, format='%Y-%m-%d'), columns=['datetime'])


missing_data_dates = extract_missing_data_dates()
missing_data_dates['datetime'] = pd.to_datetime(missing_data_dates.datetime)


# save processed data
processed_file_dir = configParser.get('PATH', 'df_dir')

missing_data_dates.to_csv(f"{processed_file_dir}/missing_data_dates.csv", index=False)
files_df.to_csv(f"{processed_file_dir}/processed_files.csv", index=False)
spectral_df.to_csv(f"{processed_file_dir}/processed_spectral.csv", index=False)
users_df.to_csv(f"{processed_file_dir}/processed_users.csv", index=False)
sessions_df.to_csv(f"{processed_file_dir}/processed_sessions.csv", index=False)
entries_df.to_csv(f"{processed_file_dir}/processed_entries.csv", index=False)