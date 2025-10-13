import requests

# Probar con body vacío
url = 'http://localhost:5000/api/sorting-rules/execute-all'
headers = {'Content-Type': 'application/json'}

print("Testing POST request with empty body...")
try:
    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    
except Exception as e:
    print(f"Exception: {e}")

print("\nTesting POST request with invalid JSON...")
try:
    response = requests.post(url, headers=headers, data="invalid json")
    print(f"Status Code: {response.status_code}")
    print(f"Response Text: {response.text}")
    
except Exception as e:
    print(f"Exception: {e}")