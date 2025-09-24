# ️ Pangolin Auth Error Monitor

Sistema de monitoreo en tiempo real para detectar intentos de login fallidos en Pangolin y enviar notificaciones instantáneas a Telegram.

---

## 🎯 Características

- ✅ **Detección Específica**: Monitoreo exclusivo del patrón `Username or password incorrect`
- ✅ **Extracción Automática**: Captura fecha/hora, email e IP de los logs
- ✅ **Notificaciones Instantáneas**: Alertas inmediatas vía Telegram
- ✅ **Zona Horaria Inteligente**: Conversión automática UTC → Hora Local

---

## 📋 Requisitos

### Mínimos

- **Bot de Telegram** configurado
- Acceso a los logs de **Pangolin**

---

### Configuración variables de entorno en fichero .env (renombrar el env-example a .env)

| TIPO | VARIABLE           | NECESARIA | VERSIÓN | VALOR                                                                                             |
| :--: | :----------------- | :-------: | :-----: | :------------------------------------------------------------------------------------------------ |
|  🤖  | TELEGRAM_BOT_TOKEN |    ✅     | v0.0.1  | Telegram Bot Token.                                                                               |
|  🤖  | TELEGRAM_CHAT_ID   |    ✅     | v0.0.1  | Telegram Chat ID.                                                                                 |
|  🐛  | DEBUG              |    ✅     | v0.0.1  | Habilita el modo Debug en el log. (0 = No / 1 = Si)                                               |
|  🌍  | TZ                 |    ✅     | v0.0.1  | Timezone (Por ejemplo: Europe/Madrid) Localizar zona horaria https://www.zeitverschiebung.net/es/ |

La VERSIÓN indica cuando se añadió esa variable o cuando sufrió alguna actualización. Consultar https://github.com/unraiders/pangolin-auth-error/releases

---

Te puedes descargar la imagen del icono desde aquí: https://github.com/unraiders/pangolin-auth-error/blob/main/images/pangolin-auth-error.png?raw=true

---

### Ejemplo docker-compose.yml (con variables incorporadas)

```yaml
services:
  pangolin-auth-error:
    image: unraiders/pangolin-auth-error
    container_name: pangolin-auth-error
    environment:
      - TELEGRAM_BOT_TOKEN=
      - TELEGRAM_CHAT_ID=
      - DEBUG=
      - TZ=
    volumes:
      - /ruta/real/log/pangolin:/log
    network_mode: bridge
    restart: unless-stopped
```

---

### Ejemplo docker-compose.yml (con fichero .env aparte)

```yaml
services:
  pangolin-auth-error:
    image: unraiders/pangolin-auth-error
    container_name: pangolin-auth-error
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
      - DEBUG=${DEBUG}
      - TZ=${TZ}
    volumes:
      - /ruta/real/log/pangolin:/log
    network_mode: bridge
    restart: unless-stopped
```

---

### Ejemplo .env

```yaml
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DEBUG=0
TZ=Europe/Madrid
```

---

## 🤖 Configurar el Bot de Telegram

#### Crear Bot:

1. Habla con [@BotFather](https://t.me/botfather) en Telegram
2. Ejecuta `/newbot` y sigue las instrucciones
3. Copia el **token** generado

#### Obtener Chat ID:

1. Envía un mensaje a tu bot
2. Visita: `https://api.telegram.org/bot<TOKEN>/getUpdates`
3. Copia el **chat_id** de la respuesta

---

### Mapeo de Logs

Edita el volumen en `docker-compose.yml`:

```yaml
volumes:
  # Cambia esta ruta por la real de tu instalación de Pangolin
  - /root/pangolin/config:/log:ro
```

---

---

## 📱 Notificaciones

### Formato del Mensaje

Cuando se detecte un intento fallido, recibirás:

```
🚨 Intento de login fallido detectado

📅 Fecha y hora: 23/09/2025 21:46:54 CEST
❌ Motivo: Username or password incorrect
📧 Email: tuhackerfavorito@thestupidland.com
🌐 IP: 192.168.1.100
```

---

## 🔧 Comandos Útiles

### Gestión de Contenedores

```bash
# Iniciar servicios
docker compose up -d

# Parar servicios
docker compose down

# Reiniciar servicios
docker compose restart

# Reconstruir imagen
docker compose build --no-cache
```

### Monitoreo y Debug

```bash
# Logs en tiempo real
docker logs -f pangolin-auth-error

# Logs de las últimas 50 líneas
docker logs --tail=50 pangolin-auth-error

# Entrar al contenedor
docker exec -it pangolin-auth-error sh

# Ver estadísticas de recursos
docker stats
```

---

## 📝 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

---

<div align="center">

**⭐ Si este proyecto te ha sido útil, ¡dale una estrella! ⭐**

_Hecho con ❤️ para la seguridad de servidores_

</div>
