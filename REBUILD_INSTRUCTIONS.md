# Instrucciones para Reconstruir Docker sin Caché

Si después de hacer `git pull` los cambios no aparecen en el contenedor Docker, es porque Docker está usando capas cacheadas.

## Solución 1: Reconstruir sin caché (RECOMENDADO)

```bash
# Detener y eliminar el contenedor actual
docker-compose -f docker-compose.prod.yml down

# Reconstruir la imagen sin usar caché
docker-compose -f docker-compose.prod.yml build --no-cache

# Iniciar el contenedor
docker-compose -f docker-compose.prod.yml up -d
```

## Solución 2: Eliminar imagen y reconstruir

```bash
# Detener contenedor
docker-compose -f docker-compose.prod.yml down

# Eliminar la imagen
docker rmi stream-plus:latest

# Reconstruir
docker-compose -f docker-compose.prod.yml up -d --build
```

## Solución 3: Forzar reconstrucción de capas específicas

```bash
# Detener contenedor
docker-compose -f docker-compose.prod.yml down

# Reconstruir forzando actualización
docker-compose -f docker-compose.prod.yml build --pull --no-cache

# Iniciar
docker-compose -f docker-compose.prod.yml up -d
```

## Verificar que los cambios se aplicaron

Después de reconstruir, puedes verificar que los archivos dentro del contenedor son los correctos:

```bash
# Ver logs del contenedor
docker logs stream-plus

# Entrar al contenedor y verificar archivos
docker exec -it stream-plus /bin/bash
cat /app/templates/auto_assign.html | grep "multiple size"
```

## Nota sobre caché de navegador

Además del caché de Docker, tu **navegador también puede estar cacheando archivos estáticos** (HTML, JS, CSS).

### Soluciones:

1. **Ctrl + F5** (Windows/Linux) o **Cmd + Shift + R** (Mac) para forzar recarga
2. **Ctrl + Shift + Delete** para limpiar caché del navegador
3. **Modo incógnito** para probar sin caché
4. **DevTools > Network > Disable cache** (con DevTools abierto)

## Prevenir caché en el futuro

Puedes agregar cache busting a los archivos estáticos usando query strings con versión:

```html
<script src="{{ url_for('static', filename='js/auto_assign.js') }}?v=2024101101"></script>
```

O usar hashes de archivo en producción.
