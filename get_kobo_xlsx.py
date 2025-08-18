import requests
import pandas as pd

api_token = "d2001d49f190d5cd625776dc1b08d13093cf8607" 

header = {"Authorization" : f"Token {api_token}"}

urls = [
'https://kf.kobotoolbox.org/api/v2/assets/a7bZivgzH5Y6kxP2nhG98w/export-settings/esjTWoCt9kxhddoXpbEbbMT/data.xlsx',
'https://kf.kobotoolbox.org/api/v2/assets/aaknL3DQQgkgZ8iay89X5P/export-settings/esMLtZ3eoopRhBPVBrG5EU6/data.xlsx'
]

filenames = ['CATCH_kobo_data.xlsx', 'SHARKS_kobo_data.xlsx']

#for i in range(2):
# response = requests.get(urls[i], headers=header ) 
# response.raise_for_status()  
# 
# with open(filenames[i], "wb") as f:
#  for chunk in response.iter_content(chunk_size=8192):
#   f.write(chunk)
#

#@st.cache_data(ttl=6000) # Cache the data for 10 minutes to avoid re-reading on every rerun
def load_data_from_excel_file(file_path="CATCH_kobo_data.xlsx"): # Explicitly load 'catch_catch' sheet

 catch = pd.read_excel(file_path, engine = 'openpyxl', sheet_name=1)


 trips = pd.read_excel(file_path, engine = 'openpyxl', sheet_name=0)
 catch = trips.merge(catch, left_on = '_uuid', right_on='_submission__uuid')

 catch = catch[catch['survey_real'] == 'real']
 catch = catch[catch['survey_type'] == 'catch']

 catch.loc[catch['Fishing_Trip/gear_type_other'] == 'Handline', 'Fishing_Trip/gear_type/pole_line'] = 1
 catch.loc[catch['Fishing_Trip/gear_type_other'] == 'Handline', 'Fishing_Trip/gear_type'] = 'hand_line'
 catch.loc[catch['Fishing_Trip/gear_type'] == 'pole_line', 'Fishing_Trip/gear_type'] = 'hand_line'
 catch = catch.rename(columns={'Fishing_Trip/gear_type/pole_line': 'Fishing_Trip/gear_type/hand_line'})

 catch['Fishing_Trip/fishing_duration'] = catch['Fishing_Trip/fishing_duration'].replace({'>3': 4})

 catch.loc[catch['Fishing_Trip/fishing_duration'] == '>3', 'Fishing_Trip/fishing_duration'] = 4
 catch.loc[catch['Fishing_Trip/fishing_duration'] != catch['Fishing_Trip/fishing_duration'], 'Fishing_Trip/fishing_duration'] = 1

 catch['people'] = catch['people'].astype('float')
 catch['boats_landed'] = catch['boats_landed'] + 1 # to include also the boat that was sampled
 catch['gear_type'] = catch['Fishing_Trip/gear_type']
 catch['boat_type'] = catch['Fishing_Trip/boat_type']
 catch['weight_catch'] = catch['Total_Catch_Survey/catch_catch/weight_catch']
 catch['group_catch'] = catch['Total_Catch_Survey/catch_catch/group_catch']
 # fishing effort per day [fishers/day]

 return catch


data = load_data_from_excel_file(file_path="CATCH_kobo_data.xlsx")

import pickle

with open('CATCH_kobo_data.pkl', 'wb') as f:
    pickle.dump(data, f)

