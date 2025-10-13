from models import StreamMatcher

# Test different resolutions
test_resolutions = ['640x480', '720x576', '1280x720', '1920x1080', '3840x2160']
for res in test_resolutions:
    normalized = StreamMatcher._normalize_resolution(res)
    print(f'{res} -> {normalized}')