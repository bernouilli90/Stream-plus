# Stream Testing Implementation - TODO

## Objetivo
Añadir funcionalidad para testear streams antes de ordenarlos, obteniendo stats de video/audio mediante perfil ffmpeg.

## Investigación Realizada

### Endpoints Probados
- ❌ `POST /api/channels/streams/{id}/test/` - No encontrado
- ❌ `POST /api/channels/streams/{id}/analyze/` - No encontrado  
- ✅ `GET /api/channels/streams/{id}/stats/` - Existe pero devuelve vacío (200 sin contenido)
- ❌ `POST /api/channels/streams/{id}/probe/` - No encontrado

### Observaciones
- Los streams tienen un campo `stream_stats` que contiene:
  - `video_codec`
  - `video_bitrate`
  - `video_resolution`
  - `audio_codec`
  - `video_fps`
  - etc.
- Según el usuario: **Los stats se obtienen cuando el stream se reproduce con perfil ffmpeg (no proxy)**
- Actualmente ningún stream en la base de datos tiene stats

## Preguntas Pendientes

1. **¿Cómo se fuerza el análisis de un stream en Dispatcharr?**
   - ¿Existe un endpoint específico?
   - ¿Hay que iniciar el stream con un perfil particular?
   
2. **¿Cuál es el flujo correcto?**
   - Opción A: Llamar a un endpoint `/test` o `/analyze`
   - Opción B: Iniciar stream con perfil ffmpeg, esperar, detener, y los stats quedan guardados
   - Opción C: Otro método

3. **¿Los stats se persisten?**
   - Una vez obtenidos los stats, ¿quedan guardados en la BD de Dispatcharr?
   - ¿Hay que refrescarlos periódicamente?

## Cambios Implementados (Pendiente de completar)

### ✅ Modelo de Datos
- Añadido campo `test_streams_before_sorting: bool` a `SortingRule`

### ⏳ API Client (Placeholder)
- Añadida función `test_stream(stream_id)` en `dispatcharr_client.py`
- **NECESITA**: Endpoint correcto de Dispatcharr

### ⏳ Lógica de Ordenación
- **PENDIENTE**: Implementar testeo de streams antes de ordenar
- **PENDIENTE**: Manejo de timeouts (testear puede tardar)
- **PENDIENTE**: Manejo de errores (stream offline, etc.)

### ⏳ UI
- **PENDIENTE**: Checkbox en formulario de regla
- **PENDIENTE**: Indicador de progreso durante testeo
- **PENDIENTE**: Mostrar resultados de testeo

## Próximos Pasos

1. **URGENTE**: Confirmar endpoint/método correcto para testear streams
2. Implementar `test_stream()` en `DispatcharrClient`
3. Modificar `execute_sorting_rule()` para testear streams si `test_streams_before_sorting=True`
4. Añadir checkbox en UI de Stream Sorter
5. Añadir manejo de progreso (puede tardar varios segundos por stream)
6. Testear con streams reales

## Ejemplo de Uso Esperado

```python
# En app.py - execute_sorting_rule()
if rule.test_streams_before_sorting:
    for stream in streams:
        try:
            # Testear stream para obtener stats
            dispatcharr_client.test_stream(stream['id'])
        except:
            pass  # Continuar si falla el testeo
    
    # Recargar streams para obtener stats actualizados
    streams = dispatcharr_client.get_channel_streams(channel_id)

# Ordenar con stats disponibles
sorted_streams = StreamSorter.sort_streams(rule, streams)
```
