import requests
import pandas as pd
import io
#import pickle
#import blosc2

import urllib
import gc
import numpy as np
import datetime

from memory_profiler import profile


datasets = ['CATCH', 'SHARK']
#datasets = ['SHARK']

API_TOKEN = "d2001d49f190d5cd625776dc1b08d13093cf8607" 

headers = {
    "Authorization": f"Token {API_TOKEN}"
}

ASSET_UID = {'SHARK':'aaknL3DQQgkgZ8iay89X5P', 'CATCH':'a7bZivgzH5Y6kxP2nhG98w'}
BASE_URL = 'https://kf.kobotoolbox.org/api/v2/assets'

def create_export_setting(ASSET):
 headers = {'Authorization': f'Token {API_TOKEN}'}
 
 payload = {
     "name": str(datetime.datetime.now()),  # This was the first error
     "source": f"{BASE_URL}/{ASSET}/",
     "type": "xls",
     "export_settings": {
         "lang": "_xml",
         "fields_from_all_versions": False,
         "group_sep": "/",
         "hierarchy_in_labels": False,
         "multiple_select": "both",
         "type": "xls"
     }
 }
 
 response = requests.post(f"{BASE_URL}/{ASSET}/export-settings/", headers=headers, json=payload)
 download_url = response.json().get('url')
 return download_url

def load_data_from_kobo(dataset, download_url): # Explicitly load 'catch_catch' sheet
 api_url = download_url+'data.xlsx'

 print(api_url)
 # catch

 if dataset == 'CATCH':

  try:
   with requests.get(api_url, headers=headers, stream=True) as r:
    r.raise_for_status()
    with open('CATCH_kobo_data_latest.xlsx', "wb") as f:
        for chunk in r.iter_content(chunk_size=8192): 
            f.write(chunk)

   # response = requests.get(api_url, headers=headers)
   # with open('CATCH_kobo_data_latest.xlsx', "wb") as f:
   #  f.write(response.content)

  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")

  trips = pd.read_excel('CATCH_kobo_data_latest.xlsx', sheet_name=0, engine='calamine')
  catch = pd.read_excel('CATCH_kobo_data_latest.xlsx', sheet_name=1, engine='calamine')

  catch = trips.merge(catch, left_on = '_uuid', right_on='_submission__uuid', how='left')

  del trips
 
  catch = catch[catch['survey_real'] == 'real']
  catch = catch[catch['survey_type'] == 'catch']
  
  catch.loc[catch['gear_type_other'] == 'Handline', 'gear_type/pole_line'] = 1
  catch.loc[catch['gear_type_other'] == 'Handline', 'gear_type'] = 'hand_line'
  catch.loc[catch['gear_type'] == 'pole_line', 'gear_type'] = 'hand_line'
  catch = catch.rename(columns={'gear_type/pole_line': 'gear_type/hand_line'})
  
  catch['fishing_duration'] = catch['fishing_duration'].replace({'>3': 4})
  
  catch.loc[catch['fishing_duration'] == '>3', 'fishing_duration'] = 4
  catch.loc[catch['fishing_duration'] != catch['fishing_duration'], 'fishing_duration'] = 1
  
  catch['people'] = catch['people'].astype('float')

  #ids = [2,4,5,7,8,10,12,13,14,15,16,17,18,19,20,21,22,210,211,212,213,214,215,217,288,289,338,339,340,341,342,343,378,379,380,381]
  #catch = catch.iloc[:, ids]

 # sharks

 elif dataset == 'SHARK':
  
  try:
   with requests.get(api_url, headers=headers, stream=True) as r:
    r.raise_for_status()
    with open('SHARK_kobo_data_latest.xlsx', "wb") as f:
        for chunk in r.iter_content(chunk_size=8192): 
            f.write(chunk)

#    response = requests.get(api_url, headers=headers)
#    with open('SHARK_kobo_data_latest.xlsx', "wb") as f:
#     f.write(response.content)

  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")

  #trip = trip.drop(['start', 'end'], axis=1)
  trip = pd.read_excel('SHARK_kobo_data_latest.xlsx', sheet_name='SHARC', engine='calamine')
  catch = pd.read_excel('SHARK_kobo_data_latest.xlsx', sheet_name='catch_details', engine='calamine')

  del trip
  
  catch = trip.merge(catch, left_on='_uuid', right_on='_submission__uuid', how='left')

  catch['landing_site'] = catch['landing_site'].str.lower()

  #del trip, excel_file, response
  
  catch['Scientific_name'] = catch['species']
  catch.loc[catch['type'] == 'Shark-like ray','Type of catch'] = 'Shark-like Ray'

  catch.loc[catch['surveyor'] == 'old data from Collect', 'Scientific_name'] = catch[catch['surveyor'] == 'old data from Collect']['genus']+' '+catch[catch['surveyor'] == 'old data from Collect']['species']
  
  catch['Scientific_name'] = catch['Scientific_name'].str.replace('  ',' ')
  catch['Scientific_name'] = catch['Scientific_name'].str.capitalize()

  catch.loc[catch['_gps_longitude'] == '',:] = np.nan  
  catch.loc[catch['_gps_latitude'] == '',:] = np.nan  
  catch['_gps_latitude'] = catch['_gps_latitude'].astype('float')
  catch['_gps_longitude'] = catch['_gps_longitude'].astype('float')

  #catch['today'] = pd.to_datetime(catch['today'],format='mixed')
  #catch['Index'] = pd.to_datetime(catch['today'],format='mixed')
  #catch = catch.set_index('Index')

  # drop useless fields
  #ids = [0,1,2,4,5,7,8,10,12,13,14,15,16,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,57,58,59,60,61,62,63,64,65,66,67,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,146,162,48]
  #catch = catch.iloc[:,ids]

 return catch


for dataset in datasets:
 print(dataset)
 download_url = create_export_setting(ASSET_UID[dataset])
 print(download_url)
 data = load_data_from_kobo(dataset, download_url)
 data.to_csv(dataset+'_kobo_data.csv')
