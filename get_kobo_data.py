import requests
import pandas as pd
import io
#import pickle
#import blosc2

import os
import psutil

print(os.getcwd())

def log_mem(step_description):
    # Get the ID of the current Python process
    pid = os.getpid()
    python_process = psutil.Process(pid)
    
    # Get memory usage in MB (RSS = Resident Set Size, the real physical memory)
    memoryUse = python_process.memory_info().rss / 1024 / 1024
    
    print(f"==== [{step_description}] Total Script Memory: {memoryUse:.2f} MB ====")


import urllib
import gc
import numpy as np
import datetime

from memory_profiler import profile


datasets = ['CATCH', 'SHARK']
#datasets = ['SHARK']
#datasets = ['CATCH']

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
  columns_trip = ['today','deviceid','survey_real','survey_type','_gps_latitude','_gps_longitude','data_collector','landing_site','landings','trip_info','boat_type','other_boat','engine_yn','engine','gear_type','gear_type_other','fishing_ground_name','fishing_location','fishing_ground_type','fishing_ground_depth','fishing_duration','people','boats_landed','_id','_uuid','_submission_time','_tags','_index']
  columns_catch = ['group_catch','species_catch','weight_catch','nb_buckets_catch','wgt_buckets_catch','nb_ind_catch','wgt_ind_catch','_submission__uuid']

  try:
   with requests.get(api_url, headers=headers, stream=True) as r:
    r.raise_for_status()
    with open('CATCH_kobo_data_latest.xlsx', "wb") as f:
     for chunk in r.iter_content(chunk_size=8192): 
      f.write(chunk)


  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")

  #log_mem('Pre read')

  trips = pd.read_excel('CATCH_kobo_data_latest.xlsx', sheet_name=0, engine='openpyxl', usecols=columns_trip)
  catch = pd.read_excel('CATCH_kobo_data_latest.xlsx', sheet_name=1, engine='openpyxl', usecols=columns_catch)

  #log_mem('Post read')

  catch = trips.merge(catch, left_on = '_uuid', right_on='_submission__uuid', how='left')

  #log_mem('Post merge')

  del trips
  gc.collect()
 
  log_mem('Post GC')

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

  #log_mem('EOF')

 # sharks

 elif dataset == 'SHARK':
  columns_trip = ['start','end','today','deviceid','survey_type','date_entry','gps','_gps_latitude','_gps_longitude','_gps_altitude','_gps_precision','country','district','survey','landing_site','market','surveyor','consent','catch_info','boat_type','other_boat','engine','fishing_location','fishing_start','fishing_end','targeted','last_catch_shark_ray','release_shark_ray','nb_sharks_unsampled','nb_rays_unsampled','nb_shark_like_rays_unsampled','market_info','shark_ray_vendors_nb','_id','_uuid','_submission_time','_index']

  columns_catch = ['type','genus','species','local_name','sex','weight','disc_width','disc_length','total_length','fork_length','precaudal_length','gear_type','gear_type/basket_traps','gear_type/hook_line','gear_type/spear_gun','gear_type/beach_seines','gear_type/ring_nets','gear_type/gill_nets_3','gear_type/gill_nets_6','gear_type/longline','gear_type/reef_seine_set_net','gear_type/drift_net','gear_type/other','gear_type_other','price_sold_for','price_sold_usd','_index','_parent_index','_submission__uuid']
  
  try:
   with requests.get(api_url, headers=headers, stream=True) as r:
    r.raise_for_status()
    with open('SHARK_kobo_data_latest.xlsx', "wb") as f:
     for chunk in r.iter_content(chunk_size=8192): 
      f.write(chunk)

  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")


  trip = pd.read_excel('SHARK_kobo_data_latest.xlsx', sheet_name='SHARC', engine='openpyxl', usecols=columns_trip)
  catch = pd.read_excel('SHARK_kobo_data_latest.xlsx', sheet_name='catch_details', engine='openpyxl', usecols=columns_catch)

  catch = trip.merge(catch, left_on='_uuid', right_on='_submission__uuid', how='left')

  del trip
  gc.collect()
 

  catch['landing_site'] = catch['landing_site'].str.lower()
  
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

 return catch


for dataset in datasets:
 print(dataset)
 download_url = create_export_setting(ASSET_UID[dataset])
 print(download_url)
 data = load_data_from_kobo(dataset, download_url)
 data.to_csv(dataset+'_kobo_data.csv')
