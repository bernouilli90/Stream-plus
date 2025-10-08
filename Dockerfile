# Usar Alpine Linux como base (imagen ligera)
FROM python:3.11-alpine

# Metadatos
LABEL maintainer="Stream Plus"
LABEL description="Stream Plus - Gestión y ordenación de streams para Dispatcharr"

# Variables de entorno por defecto
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Argumentos para UID/GID (se pueden personalizar al construir)
ARG USER_UID=1000
ARG USER_GID=1000

# Instalar dependencias del sistema (ffmpeg y ffprobe)
RUN apk add --no-cache \
    ffmpeg \
    ffmpeg-libs \
    su-exec \
    && rm -rf /var/cache/apk/*

# Crear usuario no root con UID/GID personalizables
RUN addgroup -g ${USER_GID} streamplus && \
    adduser -D -u ${USER_UID} -G streamplus streamplus

# Crear directorios necesarios
RUN mkdir -p /app /app/rules /app/tools && \
    chown -R streamplus:streamplus /app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero (para aprovechar cache de Docker)
COPY --chown=streamplus:streamplus requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY --chown=streamplus:streamplus app.py start.py models.py stream_sorter_models.py execute_rules.py ./
COPY --chown=streamplus:streamplus api/ ./api/
COPY --chown=streamplus:streamplus static/ ./static/
COPY --chown=streamplus:streamplus templates/ ./templates/

# Copiar scripts auxiliares (si existen)
COPY --chown=streamplus:streamplus check_*.py find_*.py show_*.py clean_*.py debug_*.py ./ 2>/dev/null || true

# Crear archivo para ffprobe path
RUN mkdir -p /app/tools && \
    echo "/usr/bin/ffprobe" > /app/tools/ffprobe_path.txt && \
    chown -R streamplus:streamplus /app/tools

# Volumen para reglas (persistencia)
VOLUME ["/app/rules"]

# Exponer puerto de Flask (configurable via variable de entorno)
EXPOSE 5000

# Script de entrada personalizado
COPY --chown=streamplus:streamplus docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Cambiar a usuario no root
USER streamplus

# Healthcheck para verificar que la aplicación está funcionando
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:5000/ || exit 1

# Punto de entrada
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Comando por defecto (iniciar la aplicación)
CMD ["python", "start.py"]
