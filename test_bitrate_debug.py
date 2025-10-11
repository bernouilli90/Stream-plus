"""
Debug script to test bitrate calculation in a stream
"""
import requests

# Use the Flask endpoint instead of Dispatcharr directly
print("=" * 80)
print("Testing stream 628: CUATRO FHD --> NEW ERA FHD")
print("=" * 80)

# Call the test endpoint of the Flask API
response = requests.post('http://127.0.0.1:5000/api/test-stream/628')
result = response.json()

print("\n" + "=" * 80)
print("TEST RESULT:")
print("=" * 80)
print(f"Success: {result.get('success')}")
print(f"Message: {result.get('message')}")

if result.get('statistics'):
    print("\nStatistics:")
    for key, value in result['statistics'].items():
        print(f"  {key}: {value}")
else:
    print("\nNo statistics returned!")

if result.get('save_error'):
    print(f"\nSave error: {result['save_error']}")

print("\n" + "=" * 80)
