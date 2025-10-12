import requests

try:
    response = requests.get('http://localhost:5000/api/channel-groups', timeout=10)
    print('Status:', response.status_code)
    if response.status_code == 200:
        groups = response.json()
        print('Groups loaded:', len(groups))
        for group in groups[:3]:
            print('  -', group['name'], '(ID:', group['id'], ') -', len(group.get('channel_ids', [])), 'channels')
    else:
        print('Error response:', response.text)
except Exception as e:
    print('Error:', e)