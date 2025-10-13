from models import generate_channel_name_regex
print('Testing regex generation:')
print('DAZN LALIGA ->', repr(generate_channel_name_regex('DAZN LALIGA')))
print('ESPN PLUS ->', repr(generate_channel_name_regex('ESPN PLUS')))
print('Single word ->', repr(generate_channel_name_regex('MOVISTAR')))