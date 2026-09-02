import requests
from pathlib import Path
from github import Auth, Github, GithubException
import base64
import pandas as pd
import io
import os
import urllib
import gc
import numpy as np
import datetime
import glob

datasets = ['CATCH', 'SHARK', 'RESTORATION']
#datasets = ['RESTORATION']
#datasets = ['CATCH']

API_TOKEN = os.environ['KOBO_TOKEN'] 

headers = { "Authorization": f"Token {API_TOKEN}" }

ASSET_UID = {'SHARK':'aaknL3DQQgkgZ8iay89X5P', 'CATCH':'a7bZivgzH5Y6kxP2nhG98w', 'RESTORATION':'aCCZTXLPwc4am5GfuAa7qV'}

BASE_URL = 'https://kf.kobotoolbox.org/api/v2/assets'

# I download data in batches of 5k rows
# I only downdload data that I don't have yet, based on filename
# I merge the parts into one file

def find_total_records(ASSET):
 print("Checking total record count...")
 headers = {'Authorization': f'Token {API_TOKEN}'}
 DATA_ENDPOINT = f"https://kf.kobotoolbox.org/api/v2/assets/{ASSET}/data/?limit=1"

 # print(DATA_ENDPOINT) 

 count_response = requests.get(DATA_ENDPOINT, headers=headers)
 count_response.raise_for_status()
 total_count = count_response.json()["count"]
 return total_count

def find_start_end_ids(ASSET, start, end):
 headers = {'Authorization': f'Token {API_TOKEN}'}
 
 DATA_ENDPOINT = f"https://kf.kobotoolbox.org/api/v2/assets/{ASSET}/data/"
 
 # 4. Target the specific record index to find its database _id
 id_response = requests.get(f"{DATA_ENDPOINT}?limit=1&start={start}", headers=headers)
 id_response.raise_for_status()
 id_start = id_response.json().get("results", [ ])[0]['_id']

 id_response = requests.get(f"{DATA_ENDPOINT}?limit=1&start={end}", headers=headers)
 id_response.raise_for_status()
 id_end = id_response.json().get("results", [ ])[0]['_id']
     
 return id_start, id_end


def create_export_setting(ASSET, start, end):
 headers = {'Authorization': f'Token {API_TOKEN}'}
 
 payload_partial = {
     "name": str(datetime.datetime.now()),  # This was the first error
     "source": f"{BASE_URL}/{ASSET}/",
     "type": "xls",
     "export_settings": {
         "lang": "_xml",
         "fields_from_all_versions": False,
         "group_sep": "/",
         "hierarchy_in_labels": False,
         "multiple_select": "both",
         "type": "xls",
	"query": {
      		"_id": {
        	"$gte": start,
        	"$lte": end,
      		}
    	}
     }
 }
 
 response = requests.post(f"{BASE_URL}/{ASSET}/export-settings/", headers=headers, json=payload_partial)
 download_url = response.json().get('url')
 return download_url

def download_data(dataset, download_url, fname_out): 
 api_url = download_url+'data.xlsx'
 # print(api_url)

 try:
  with requests.get(api_url, headers=headers, stream=True) as r:
   r.raise_for_status()
   with open(fname_out, "wb") as f:
    for chunk in r.iter_content(chunk_size=8192): 
     f.write(chunk)

 except requests.exceptions.RequestException as e:
   print(f"Error fetching data: {e}")

 return


def merge_files(dataset):
 files = glob.glob(dataset+"*xlsx")
 return

def process_data(dataset, fname): # Explicitly load 'catch_catch' sheet

 if dataset == 'CATCH':
  columns_trip = ['today','deviceid','survey_real','survey_type','_gps_latitude','_gps_longitude','data_collector','landing_site','landings','trip_info','boat_type','other_boat','engine_yn','engine','gear_type','gear_type_other','fishing_ground_name','fishing_location','fishing_ground_type','fishing_ground_depth','fishing_duration','people','boats_landed','_id','_uuid','_submission_time','_tags','_index']
  columns_catch = ['group_catch','species_catch','weight_catch','nb_buckets_catch','wgt_buckets_catch','nb_ind_catch','wgt_ind_catch','_submission__uuid']

  trips = pd.read_excel(fname, sheet_name=0, engine='openpyxl', usecols=columns_trip)
  catch = pd.read_excel(fname, sheet_name=1, engine='openpyxl', usecols=columns_catch)

  catch = trips.merge(catch, left_on = '_uuid', right_on='_submission__uuid', how='left')

  del trips
  gc.collect()
 
  #log_mem('Post GC')

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

  output = catch
  #log_mem('EOF')

 # sharks

 elif dataset == 'SHARK':
  columns_trip = ['start','end','today','survey_type','_gps_latitude','_gps_longitude','survey','landing_site','market','surveyor','catch_info','boat_type','other_boat','engine','fishing_location','fishing_start','fishing_end','targeted','last_catch_shark_ray','release_shark_ray','nb_sharks_unsampled','nb_rays_unsampled','nb_shark_like_rays_unsampled','market_info','shark_ray_vendors_nb','_uuid']

  columns_catch = ['type','genus','species','local_name','sex','weight','disc_width','disc_length','total_length','fork_length','precaudal_length','gear_type','gear_type/basket_traps','gear_type/hook_line','gear_type/spear_gun','gear_type/beach_seines','gear_type/ring_nets','gear_type/gill_nets_3','gear_type/gill_nets_6','gear_type/longline','gear_type/reef_seine_set_net','gear_type/drift_net','gear_type/other','gear_type_other','price_sold_for','price_sold_usd','_submission__uuid']
  
  trip = pd.read_excel(fname, sheet_name='SHARC', engine='openpyxl', usecols=columns_trip)
  catch = pd.read_excel(fname, sheet_name='catch_details', engine='openpyxl', usecols=columns_catch)

  catch = trip.merge(catch, left_on='_uuid', right_on='_submission__uuid', how='left')

  del trip
  gc.collect()

  catch['landing_site'] = catch['landing_site'].str.lower()
  
  catch['Scientific_name'] = catch['species']
  catch.loc[catch['type'] == 'Shark-like ray','type'] = 'Shark-like Ray'
  catch['type'] = catch['type'].str.capitalize()

  catch.loc[catch['surveyor'] == 'old data from Collect', 'Scientific_name'] = catch[catch['surveyor'] == 'old data from Collect']['genus']+' '+catch[catch['surveyor'] == 'old data from Collect']['species']
  
  catch['Scientific_name'] = catch['Scientific_name'].str.replace('  ',' ')
  catch['Scientific_name'] = catch['Scientific_name'].str.capitalize()

  catch.loc[catch['_gps_longitude'] == '',:] = np.nan  
  catch.loc[catch['_gps_latitude'] == '',:] = np.nan  
  catch['_gps_latitude'] = catch['_gps_latitude'].astype('float')
  catch['_gps_longitude'] = catch['_gps_longitude'].astype('float')

  output = catch

 elif dataset == 'RESTORATION':
  gc.collect()

  restoration = pd.read_excel(fname, engine='openpyxl')

  output = restoration
 return output

def upload_to_github(file_path, repo_name, token):

    auth = Auth.Token(token)

    try:
        print("Connecting to GitHub...")
        g = Github(auth=auth)
        repo = g.get_repo(repo_name) # e.g., "yourusername/catch-data"

        # Read the file
        print("Reading file...")
        with open(file_path, "rb") as file:
         content = file.read()

        # Path in the repo where you want to save it

        # Check if file exists to update it, or create new
         try:
          contents = repo.get_contents(file_path)
          print("File exists. Updating with new one.")
          repo.update_file(contents.path, "Daily Data Update", content, contents.sha)
         except GithubException as e:
          if e.status == 404:
           print("File does not exist. Creating new.")
           repo.create_file(file_path, "Initial Data Upload", content)
          else:
           raise
 
         print("Upload to GitHub successful!")

    except Exception as e:
        print(f"GitHub Upload Failed: {e}")


# Main script,
# 1. for each dataset
# 2. deletes recent data
# 3. count total number of records
# 4. splits download over multiple files (only new files)
# 5. merges the files (old and new) into a new CSV
# 6. uploads the CSV to github


for dataset in datasets:
 print(dataset)

 # 2. delete recent downloads that are not complete for this dataset

 all_kobo_files = glob.glob(dataset+"*kobo_data.xlsx")
 files_to_delete = [f for f in all_kobo_files if not f.endswith("999_kobo_data.xlsx")]

 for file in files_to_delete:
    try:
        os.remove(file)
        print(f"Deleted: {file}")
    except FileNotFoundError:
        print(f"File not found: {file}") 

 # 3. counts total number of records and split the download

 trec = find_total_records(ASSET_UID[dataset])

 print('total number of records: '+str(trec))

 if trec >= 5000:

  for i in range(int(trec / 5000)):
   start_rec = i * 5000
   end_rec = (i+1) * 5000 - 1
   fname_out = dataset+'_'+str(start_rec)+'_'+str(end_rec)+'_kobo_data.xlsx'
 
   file_path = Path(fname_out)
 
   if not file_path.is_file():
    print('downloading file chunk: '+fname_out)
    start_id, end_id = find_start_end_ids(ASSET_UID[dataset], start_rec, end_rec)
    #print(start_id)
    #print(end_id)
    download_url = create_export_setting(ASSET_UID[dataset], start_id, end_id)
    download_data(dataset, download_url, fname_out)
 
  start_rec = (i+1) * 5000
  end_rec = (i+1) * 5000 + trec % 5000 
  fname_out = dataset+'_'+str(start_rec)+'_'+str(end_rec)+'_kobo_data.xlsx'
  print('downloading last file: '+fname_out)
 
  start_id, end_id = find_start_end_ids(ASSET_UID[dataset], start_rec, end_rec-1)
  #print(start_id)
  #print(end_id)
  download_url = create_export_setting(ASSET_UID[dataset], start_id, end_id)
  download_data(dataset, download_url, fname_out)

 else:
  start_rec = 0
  end_rec = trec -1
  fname_out = dataset+'_'+str(start_rec)+'_'+str(end_rec)+'_kobo_data.xlsx'

  file_path = Path(fname_out)

  if not file_path.is_file():
   print('downloading short file: '+fname_out)
   print(fname_out)
   start_id, end_id = find_start_end_ids(ASSET_UID[dataset], start_rec, end_rec)
   #print(start_id)
   #print(end_id)
   download_url = create_export_setting(ASSET_UID[dataset], start_id, end_id)
   download_data(dataset, download_url, fname_out)

 # 5. process data from each xlsx into one csv file

 data_out = pd.DataFrame()

 files = glob.glob(dataset+"*xlsx")
 print("processing xlsxs in csv")

 for file in files:
  print(file)
  data = process_data(dataset, file)
  data_out = pd.concat([data_out, data], ignore_index=True) 

 data_out.to_csv(dataset+'_kobo_data.csv')

 # 6. upload to github
 upload_to_github(dataset+'_kobo_data.csv', 'jungla/CatchViz', os.environ['GIT_TOKEN'])
