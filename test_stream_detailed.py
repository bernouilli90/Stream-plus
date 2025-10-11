from api.dispatcharr_client import DispatcharrClient
import os
import subprocess
import json as json_lib
from datetime import datetime, timezone

# Usar las credenciales del archivo .env
client = DispatcharrClient(
    base_url='http://192.168.10.10:9192',
    username='jose',
    password='rotring1010'
)

# Obtener un stream que no tenga estadísticas
stream_id = 986  # Este no tenía estadísticas antes
print(f'Probando stream {stream_id}...')

try:
    # Get the stream object
    stream_obj = client.get_stream(stream_id)
    stream_url = stream_obj.get('url')

    if not stream_url:
        print('Error: Stream no tiene URL')
        exit(1)

    print(f'URL del stream: {stream_url}')

    # Find ffprobe executable
    ffprobe_executable = 'ffprobe'

    # Check for local installations
    import os as os_module
    local_ffprobe = os_module.path.join(
        os_module.path.dirname(os_module.path.dirname(os_module.path.abspath(__file__))),
        'tools', 'ffmpeg', 'ffmpeg-7.1-essentials_build', 'bin', 'ffprobe.exe'
    )

    if os_module.path.exists(local_ffprobe):
        ffprobe_executable = local_ffprobe
        print(f'Usando ffprobe local: {ffprobe_executable}')
    else:
        print('Usando ffprobe del sistema')

    # Test ffprobe directly
    print('Ejecutando ffprobe...')
    ffprobe_cmd = [
        ffprobe_executable,
        '-analyzeduration', '10000000',  # 10 seconds
        '-probesize', '50000000',  # 50MB
        '-v', 'error',
        '-print_format', 'json',
        '-show_format',
        '-show_streams',
        stream_url
    ]

    print(f'Comando: {" ".join(ffprobe_cmd)}')

    result = subprocess.run(
        ffprobe_cmd,
        capture_output=True,
        text=True,
        timeout=30
    )

    print(f'Return code: {result.returncode}')

    if result.returncode != 0:
        print(f'Error en ffprobe: {result.stderr}')
        exit(1)

    # Parse probe data
    probe_data = json_lib.loads(result.stdout)
    print('Datos de ffprobe obtenidos correctamente')

    # Extract video and audio streams
    video_stream = None
    audio_stream = None

    for stream in probe_data.get('streams', []):
        if stream.get('codec_type') == 'video' and not video_stream:
            video_stream = stream
        elif stream.get('codec_type') == 'audio' and not audio_stream:
            audio_stream = stream

    print(f'Video stream encontrado: {video_stream is not None}')
    print(f'Audio stream encontrado: {audio_stream is not None}')

    # Build stats object
    stats = {}

    if video_stream:
        width = video_stream.get('width')
        height = video_stream.get('height')
        if width and height:
            stats['resolution'] = f"{width}x{height}"

        stats['video_codec'] = video_stream.get('codec_name')
        stats['pixel_format'] = video_stream.get('pix_fmt')

    if audio_stream:
        stats['audio_codec'] = audio_stream.get('codec_name')
        sample_rate = audio_stream.get('sample_rate')
        if sample_rate:
            stats['sample_rate'] = int(sample_rate)

        audio_bitrate_bps = audio_stream.get('bit_rate')
        if audio_bitrate_bps:
            stats['audio_bitrate'] = float(audio_bitrate_bps) / 1000.0

        channels = audio_stream.get('channels')
        if channels:
            stats['audio_channels'] = 'stereo' if int(channels) == 2 else 'mono'

    # Mock bitrate calculation (since we don't have ffmpeg in this test)
    stats['output_bitrate'] = 3500.0  # Mock value
    stats['ffmpeg_output_bitrate'] = 3500.0

    format_name = probe_data.get('format', {}).get('format_name')
    if format_name:
        stats['stream_type'] = format_name

    print(f'Estadísticas construidas: {stats}')

    # Update stream object
    stream_obj['stream_stats'] = stats
    stream_obj['stream_stats_updated_at'] = datetime.now(timezone.utc).isoformat()

    print('Actualizando stream en Dispatcharr...')
    updated_stream = client.update_stream(stream_id, stream_obj)

    print('Stream actualizado exitosamente!')
    print(f'Estadísticas guardadas: {updated_stream.get("stream_stats", {})}')

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()