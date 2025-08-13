import requests
import json

# Your KoboToolbox API endpoint and token
url = 'https://kf.kobotoolbox.org/api/v2/assets/a7bZivgzH5Y6kxP2nhG98w/data.json'
token = 'd2001d49f190d5cd625776dc1b08d13093cf8607'

# Set up the headers with your authorization token
headers = {
    'Authorization': f'Token {token}'
}

try:
    # Make the GET request to the KoboToolbox API
    response = requests.get(url, headers=headers)

    # Raise an exception for bad status codes (4xx or 5xx)
    response.raise_for_status()

    # Get the JSON data from the response
    data = response.json()

    # Print the data in a human-readable format
    print(json.dumps(data, indent=4))

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
