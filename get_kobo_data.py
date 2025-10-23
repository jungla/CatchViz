import requests
import pandas as pd
import io
#import pickle
#import blosc2

import urllib
import gc
import numpy as np


filenames = ['CATCH_kobo_data.xlsx', 'SHARKS_kobo_data.xlsx']
filenames = ['SHARKS_kobo_data.xlsx']
#filenames = ['CATCH_kobo_data.xlsx']

API_TOKEN = "d2001d49f190d5cd625776dc1b08d13093cf8607" 

headers = {
    "Authorization": f"Token {API_TOKEN}"
}

def load_data_from_kobo(filename): # Explicitly load 'catch_catch' sheet

 # catch

 if filename == 'CATCH_kobo_data.xlsx':
  api_url = f'https://kf.kobotoolbox.org/api/v2/assets/a7bZivgzH5Y6kxP2nhG98w/export-settings/esjTWoCt9kxhddoXpbEbbMT/data.xlsx'

  try:
    response = requests.get(api_url, headers=headers)
    with open('CATCH_kobo_data_latest.xlsx', "wb") as f:
     f.write(response.content)

    #response = requests.get(api_url, headers=headers)
    #response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    #excel_file = io.BytesIO(response.content)
    #catch = pd.read_excel(excel_file, engine='openpyxl', sheet_name=1)
    #trips = pd.read_excel(excel_file, engine='openpyxl', sheet_name=0)

  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")

  trips = pd.read_excel('CATCH_kobo_data_latest.xlsx', sheet_name=0, engine='openpyxl')
  catch = pd.read_excel('CATCH_kobo_data_latest.xlsx', sheet_name=1, engine='openpyxl')

  catch = trips.merge(catch, left_on = '_uuid', right_on='_submission__uuid', how='left')

  del trips, excel_file, response
 
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

  ids = [2,4,5,7,8,10,12,13,14,15,16,17,18,19,20,21,22,210,211,212,213,214,215,217,288,289,338,339,340,341,342,343,378,379,380,381]
  catch = catch.iloc[:, ids]

 # sharks

 elif filename == 'SHARKS_kobo_data.xlsx':
  api_url = f'https://kf.kobotoolbox.org/api/v2/assets/aaknL3DQQgkgZ8iay89X5P/export-settings/esMLtZ3eoopRhBPVBrG5EU6/data.xlsx'
  
  try:
    # simpler approach donwloading the file
    response = requests.get(api_url, headers=headers)
    with open('SHARKS_kobo_data_latest.xlsx', "wb") as f:
     f.write(response.content)

    #response = requests.get(api_url, headers=headers)
    #response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
    #excel_file = io.BytesIO(response.content)


  except requests.exceptions.RequestException as e:
    print(f"Error fetching data: {e}")

  #trip = trip.drop(['start', 'end'], axis=1)
  trip = pd.read_excel('SHARKS_kobo_data_latest.xlsx', sheet_name='SHARC', engine='openpyxl')
  catch = pd.read_excel('SHARKS_kobo_data_latest.xlsx', sheet_name='catch_details', engine='openpyxl')
  
  catch = trip.merge(catch, left_on='_uuid', right_on='_submission__uuid', how='left')

  catch['Landing site'] = catch['Landing site'].str.lower()
  catch = catch.rename(columns={'Landing site': 'landing_site'})

  #del trip, excel_file, response
  
  catch['Scientific_name'] = catch['Species']
  catch.loc[catch['Type of catch'] == 'Shark-like ray','Type of catch'] = 'Shark-like Ray'

  catch.loc[catch['Data collector\'s name'] == 'old data from Collect', 'Scientific_name'] = catch[catch['Data collector\'s name'] == 'old data from Collect']['Genus']+' '+catch[catch['Data collector\'s name'] == 'old data from Collect']['Species']
  
  catch['Scientific_name'] = catch['Scientific_name'].str.replace('  ',' ')
  catch['Scientific_name'] = catch['Scientific_name'].str.capitalize()

  catch.loc[catch['_GPS_longitude'] == '',:] = np.nan  
  catch.loc[catch['_GPS_latitude'] == '',:] = np.nan  
  catch['_GPS_latitude'] = catch['_GPS_latitude'].astype('float')
  catch['_GPS_longitude'] = catch['_GPS_longitude'].astype('float')

  #catch['today'] = pd.to_datetime(catch['today'],format='mixed')
  #catch['Index'] = pd.to_datetime(catch['today'],format='mixed')
  #catch = catch.set_index('Index')

  # drop useless fields
  ids = [0,1,2,4,5,7,8,10,12,13,14,15,16,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,57,58,59,60,61,62,63,64,65,66,67,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128,129,130,131,132,133,134,135,136,137,138,139,140,141,142,143,144,146,162,48]
  catch = catch.iloc[:,ids]

 return catch

for i in range(len(filenames)):
 print(filenames[i])
 data = load_data_from_kobo(filename=filenames[i])
 data.to_csv(filenames[i][:-5]+'.csv')
