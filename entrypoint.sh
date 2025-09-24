#!/bin/sh

echo "$(date +'%d-%m-%Y %H:%M:%S') - Arrancando PANGOLIN-AUTH-ERROR" 
echo "$(date +'%d-%m-%Y %H:%M:%S') - Versión: $VERSION" 
echo "$(date +'%d-%m-%Y %H:%M:%S') - Debug: $DEBUG"
echo "$(date +'%d-%m-%Y %H:%M:%S') - Zona horaria: $TZ" 

exec python3 /app/log_monitor.py