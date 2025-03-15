import pandas as pd
import glob
import re
import configparser


configParser = configparser.ConfigParser()
configParser.read('config')
users_csv_dir = configParser.get('PATH', 'users_csv_dir')
dumped_file_dir = configParser.get('PATH', 'dumped_file_dir')

users_csv_files = glob.glob(f'{users_csv_dir}/*.csv')
users_csv_files.sort()

users_with_date_file = glob.glob(f'{dumped_file_dir}/users_with_date.csv')

st_file_ind = 1
if len(users_with_date_file) == 0:
    date = re.search(r"\d{4}_\d{2}_\d{2}", users_csv_files[0]).group().replace('_', '-')
    df = pd.read_csv(users_csv_files[0])
    df['date'] = date
    df.to_csv(f'{dumped_file_dir}/users_with_date.csv', index=False)
    st_file_ind = 0


users_with_date = pd.read_csv(f'{dumped_file_dir}/users_with_date.csv')
the_last_date = users_with_date.date.iloc[-1].replace(" 00:00:00", "")

for file in users_csv_files[st_file_ind:]:
    date = re.search(r"\d{4}_\d{2}_\d{2}", file).group().replace('_', '-')

    if date > the_last_date:
        df = pd.read_csv(file)
        new_records = pd.concat([users_with_date,df]).drop_duplicates(keep=False, subset=['uuid'])
        new_records['date'] = date
        users_with_date = pd.concat([users_with_date,new_records])

users_with_date.to_csv(f'{dumped_file_dir}/users_with_date.csv', index=False)