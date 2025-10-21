#!/usr/bin/env python3
"""
Example output of the improved stream testing logging
"""

def show_example_logging():
    """Show example of the improved logging structure"""

    print("=== Improved Stream Testing Logging Example ===\n")

    print("🔍 Testing Stream: ESPN HD")
    print("   URL: http://example.com/stream/123\n")

    print("📊 FFprobe Analysis:")
    print("   Command: ffprobe -user_agent \"Mozilla/5.0 ...\" -v error -skip_frame nokey -print_format json -show_streams http://example.com/stream/123")
    print("   ✅ FFprobe SUCCESS:")
    print("      Video: 1920x1080 @ 30/1fps (h264)")
    print("      Audio: 2ch @ 44100Hz (aac)")
    print("      Format: hls\n")

    print("🎬 FFmpeg Bitrate Analysis:")
    print("   Command: ffmpeg -user_agent \"Mozilla/5.0 ...\" -t 10 -i http://example.com/stream/123 -c copy -f null -")
    print("   ✅ FFmpeg SUCCESS:")
    print("      Calculated bitrate: 4500.0 kbps\n")

    print("📊 Final Statistics Collected:")
    print("   resolution: 1920x1080")
    print("   source_fps: 30.0")
    print("   video_codec: h264")
    print("   pixel_format: yuv420p")
    print("   audio_codec: aac")
    print("   sample_rate: 44100")
    print("   audio_bitrate: 128.0")
    print("   audio_channels: stereo")
    print("   stream_type: hls")
    print("   output_bitrate: 4500.0")
    print("   ffmpeg_output_bitrate: 4500.0\n")

    print("Successfully saved statistics to Dispatcharr for stream 123\n")

    print("--- Example of FFprobe Failure ---\n")

    print("🔍 Testing Stream: Broken Stream")
    print("   URL: http://broken.example.com/stream/456\n")

    print("📊 FFprobe Analysis:")
    print("   Command: ffprobe -user_agent \"Mozilla/5.0 ...\" -v error -skip_frame nokey -print_format json -show_streams http://broken.example.com/stream/456")
    print("   ❌ FFprobe FAILED:")
    print("      Return code: 1")
    print("      Error: http://broken.example.com/stream/456: Connection timed out\n")

    print("--- Example of FFmpeg Failure ---\n")

    print("🔍 Testing Stream: Geo-blocked Stream")
    print("   URL: http://geo-blocked.example.com/stream/789\n")

    print("📊 FFprobe Analysis:")
    print("   Command: ffprobe -user_agent \"Mozilla/5.0 ...\" -v error -skip_frame nokey -print_format json -show_streams http://geo-blocked.example.com/stream/789")
    print("   ✅ FFprobe SUCCESS:")
    print("      Video: 1280x720 @ 25/1fps (h264)")
    print("      Audio: 2ch @ 48000Hz (aac)")
    print("      Format: hls\n")

    print("🎬 FFmpeg Bitrate Analysis:")
    print("   Command: ffmpeg -user_agent \"Mozilla/5.0 ...\" -t 10 -i http://geo-blocked.example.com/stream/789 -c copy -f null -")
    print("   ❌ FFmpeg FAILED:")
    print("      Return code: 1")
    print("      Error: http://geo-blocked.example.com/stream/789: Forbidden")
    print("   ⚠️  Using ffprobe data only (no bitrate calculation)\n")

    print("📊 Final Statistics Collected:")
    print("   resolution: 1280x720")
    print("   source_fps: 25.0")
    print("   video_codec: h264")
    print("   audio_codec: aac")
    print("   sample_rate: 48000")
    print("   audio_channels: stereo")
    print("   stream_type: hls")

if __name__ == '__main__':
    show_example_logging()