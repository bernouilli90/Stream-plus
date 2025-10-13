import requests
import json

# Probar la petición POST al endpoint execute-all
url = 'http://localhost:5000/api/sorting-rules/execute-all'
headers = {'Content-Type': 'application/json'}
data = {'stream': True}

print("Testing POST request to execute-all endpoint...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print(f"Data: {data}")

try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Text: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success Response: {result}")
    else:
        print(f"Error Response: {response.text}")
        
except Exception as e:
    print(f"Exception: {e}")