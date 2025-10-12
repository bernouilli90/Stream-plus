import sys
sys.stdout = open('test_output.log', 'w')
sys.stderr = open('test_error.log', 'w')

from api.dispatcharr_client import DispatcharrClient
import os

print('Environment variables:')
print('DISPATCHARR_API_URL:', repr(os.getenv('DISPATCHARR_API_URL')))
print('DISPATCHARR_API_USER:', repr(os.getenv('DISPATCHARR_API_USER')))
print('DISPATCHARR_API_PASSWORD:', repr(os.getenv('DISPATCHARR_API_PASSWORD')))

try:
    client = DispatcharrClient(
        base_url=os.getenv('DISPATCHARR_API_URL', 'http://localhost:8080'),
        username=os.getenv('DISPATCHARR_API_USER'),
        password=os.getenv('DISPATCHARR_API_PASSWORD')
    )
    print('Client created successfully:', type(client))
    print('Client has get_channel_groups method:', hasattr(client, 'get_channel_groups'))
except Exception as e:
    print('Error creating client:', e)
    import traceback
    traceback.print_exc()