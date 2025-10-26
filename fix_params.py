import re

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find all occurrences of the incorrect call
incorrect_calls = re.findall(r"dispatcharr_client\.update_channel_profile_status\(rule\.channel_id, profile\['id'\], False\)", content)
print(f"Found {len(incorrect_calls)} incorrect calls")

# Replace all occurrences of the incorrect parameter order
# From: dispatcharr_client.update_channel_profile_status(rule.channel_id, profile['id'], False)
# To:   dispatcharr_client.update_channel_profile_status(profile['id'], rule.channel_id, False)
corrected_content = content.replace(
    "dispatcharr_client.update_channel_profile_status(rule.channel_id, profile['id'], False)",
    "dispatcharr_client.update_channel_profile_status(profile['id'], rule.channel_id, False)"
)

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(corrected_content)

print('Fixed parameter order in all update_channel_profile_status calls')