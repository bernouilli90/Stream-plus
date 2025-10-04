#!/usr/bin/env python
"""Check if stream statistics were saved in Dispatcharr after testing."""

from api.dispatcharr_client import DispatcharrClient
import json

def main():
    client = DispatcharrClient(
        base_url="http://192.168.10.10:9192",
        username="jose",
        password="rotring1010"
    )
    
    # Get channel 614 (DAZN LA LIGA)
    channel = client.get_channel(614)
    
    print(f"\nChannel: {channel.get('name', 'Unknown')}")
    print(f"Channel ID: {channel.get('id')}")
    print(f"Number of streams: {len(channel.get('streams', []))}\n")
    
    # Check our tested streams (776, 720, 531)
    tested_stream_ids = [776, 720, 531]
    stream_ids = channel.get('streams', [])
    
    print("=" * 80)
    print("STREAM STATISTICS CHECK")
    print("=" * 80)
    print(f"\nStreams in channel: {stream_ids}")
    print(f"Type of streams: {type(stream_ids)}")
    if len(stream_ids) > 0:
        print(f"Type of first stream: {type(stream_ids[0])}")
        
    # The streams are just IDs in the channel, need to fetch full stream data
    print("\nFetching full stream data from Dispatcharr...")
    for stream_id in stream_ids:
        if stream_id in tested_stream_ids:
            try:
                # Get full stream data
                stream_data = client._make_request('GET', f'/api/streams/streams/{stream_id}/')
                
                has_stats = 'stream_stats' in stream_data and stream_data['stream_stats'] is not None
                print(f"\nStream ID: {stream_id}")
                print(f"Name: {stream_data.get('name', 'Unknown')}")
                print(f"Has stream_stats: {has_stats}")
                
                if has_stats:
                    stats = stream_data['stream_stats']
                    print(f"  - Codec: {stats.get('codec_name', 'N/A')}")
                    print(f"  - Resolution: {stats.get('width')}x{stats.get('height')}")
                    print(f"  - Bitrate: {stats.get('bit_rate', 'N/A')}")
                    print(f"  - Frame rate: {stats.get('avg_frame_rate', 'N/A')}")
                else:
                    print("  - NO STATISTICS AVAILABLE")
            except Exception as e:
                print(f"\nError fetching stream {stream_id}: {str(e)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
