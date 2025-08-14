import requests

api_token = "d2001d49f190d5cd625776dc1b08d13093cf8607" 

header = {"Authorization" : f"Token {api_token}"}

urls = [
'https://kf.kobotoolbox.org/api/v2/assets/a7bZivgzH5Y6kxP2nhG98w/export-settings/esjTWoCt9kxhddoXpbEbbMT/data.xlsx',
'https://kf.kobotoolbox.org/api/v2/assets/aaknL3DQQgkgZ8iay89X5P/export-settings/esMLtZ3eoopRhBPVBrG5EU6/data.xlsx'
]

filenames = ['CATCH_kobo_data.xlsx', 'SHARKS_kobo_data.xlsx']

for i in range(2):
 response = requests.get(urls[i], headers=header ) 
 response.raise_for_status()  
 
 with open(filenames[i], "wb") as f:
  for chunk in response.iter_content(chunk_size=8192):
   f.write(chunk)
