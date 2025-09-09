import requests
import pandas as pd
#import pickle
#import blosc2

api_token = "d2001d49f190d5cd625776dc1b08d13093cf8607" 

header = {"Authorization" : f"Token {api_token}"}

urls = [
'https://kf.kobotoolbox.org/api/v2/assets/a7bZivgzH5Y6kxP2nhG98w/export-settings/esjTWoCt9kxhddoXpbEbbMT/data.xlsx',
'https://kf.kobotoolbox.org/api/v2/assets/aaknL3DQQgkgZ8iay89X5P/export-settings/esMLtZ3eoopRhBPVBrG5EU6/data.xlsx'
]

filenames = ['CATCH_kobo_data.xlsx', 'SHARKS_kobo_data.xlsx']


def load_data_from_excel_file(filename): # Explicitly load 'catch_catch' sheet

 # catch

 if filename == 'CATCH_kobo_data.xlsx':
  catch = pd.read_excel(filename, engine = 'openpyxl', sheet_name=1)
  trips = pd.read_excel(filename, engine = 'openpyxl', sheet_name=0)
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

 # sharks

 elif filename == 'SHARKS_kobo_data.xlsx':
  trip = pd.read_excel(filename,na_values='NaN', keep_default_na=False, sheet_name='SHARC', engine='openpyxl')
  catch = pd.read_excel(filename,na_values='NaN', keep_default_na=False, sheet_name='catch_details', engine='openpyxl')

  region = pd.DataFrame({'Survey site' : ['Bububu/Malindi', 'Malindi', 'Chole', 'Kukuu', 'Mazizini', 'Mkoani', 'Msuka', 'Mtwara', 'Rufiji', 'Somanga', 'Wete','Kilwa', 'Shanghani','Nungwi','Moa','Kizimkazi dimbani','Mkokotoni','Mafia','Tanga','Sumbauranga','bwawani'], 'Region' : ['Unguja','Unguja','Pemba','Pemba','Unguja','Pemba','Pemba','Mainland','Mainland','Mainland','Pemba','Mainland','Unguja','Unguja','Mainland','Unguja','Unguja','Mainland','Mainland','Mainland','Unguja']})
  
  trip = trip.drop(['start', 'end'], axis=1)
  
  catch = pd.merge(trip, catch, left_on='_index', right_on='_parent_index')
  catch = pd.merge(catch, region, left_on='Landing site', right_on='Survey site')
  
  catch['Scientific_name'] = catch['Species']
  catch.loc[catch['Data collector\'s name'] == 'old data from Collect', 'Scientific_name'] = catch[catch['Data collector\'s name'] == 'old data from Collect']['Genus']+' '+catch[catch['Data collector\'s name'] == 'old data from Collect']['Species']
  
  catch['Scientific_name'] = catch['Scientific_name'].str.replace('  ',' ')
  catch['Scientific_name'] = catch['Scientific_name'].str.capitalize()
  
  catch['today'] = pd.to_datetime(catch['today'],format='mixed')
  catch['Index'] = pd.to_datetime(catch['today'],format='mixed')
  catch = catch.set_index('Index')

 return catch

for i in range(2):
 data = load_data_from_excel_file(filename=filenames[i])
 data.to_parquet(filenames[i][:-5]+'.parquet', compression='snappy')

