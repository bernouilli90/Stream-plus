#!/usr/bin/env python
"""Find the M3U stream URL for a channel in Dispatcharr."""

from api.dispatcharr_client import DispatcharrClient
import json

def main():
    client = DispatcharrClient(
        base_url="http://192.168.10.10:9192",
        username="jose",
        password="rotring1010"
    )
    
    # Get channel 614
    channel = client.get_channel(614)
    
    print("="*80)
    print("CHANNEL 614 DATA STRUCTURE")
    print("="*80)
    print(json.dumps(channel, indent=2, default=str))
    
    print("\n" + "="*80)
    print("STREAM URLS")
    print("="*80)
    
    # Based on what we know works:
    channel_id = channel['id']
    channel_num = channel.get('channel_number', channel_id)
    
    # The URL that works for HTTP streaming:
    stream_url = f"http://192.168.10.10:9192/proxy/ts/stream/{channel_id}"
    print(f"\nWorking HTTP Stream URL:")
    print(f"  {stream_url}")
    
    # M3U8 format would be:
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel['name']}" tvg-logo="" group-title="Dispatcharr",{channel['name']}
{stream_url}
"""
    
    print(f"\nM3U8 Entry:")
    print(m3u_content)
    
    # Save to file
    with open("channel_614.m3u8", "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"Saved to channel_614.m3u8")

if __name__ == "__main__":
    main()
