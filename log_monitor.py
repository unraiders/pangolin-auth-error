import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict
import aiofiles
import telebot
import pytz
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DEBUG, TZ, LANGUAGE, VERSION
from utils import setup_logger, generate_trace_id, load_error_types, build_error_patterns, match_auth_error, get_translated_error

VERSION = "0.0.4"

logger = setup_logger(__name__)


def load_translations(language: str = 'ES') -> Dict[str, str]:
    """Carga las traducciones desde el archivo JSON correspondiente"""
    try:
        locale_file = Path(__file__).parent / 'locale' / f'{language.lower()}.json'
        
        # Si el idioma solicitado no existe, usar español por defecto
        if not locale_file.exists():
            logger.warning(f"Archivo de idioma no encontrado: {locale_file}, usando español por defecto")
            locale_file = Path(__file__).parent / 'locale' / 'es.json'
            language = 'ES'  # Actualizar el idioma para el log
        
        with open(locale_file, 'r', encoding='utf-8') as f:
            translations = json.load(f)
        
        logger.info(f"Traducciones cargadas para idioma: {language}")
        return translations
        
    except Exception as e:
        logger.error(f"Error cargando traducciones: {e}")
        # Si hay error incluso con el archivo español, cargar desde el archivo es.json directamente
        try:
            es_file = Path(__file__).parent / 'locale' / 'es.json'
            with open(es_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as es_error:
            logger.error(f"Error crítico: No se pudo cargar el archivo es.json: {es_error}")
            raise

translations = load_translations(LANGUAGE)
class TelegramNotifier:
    """Clase para enviar notificaciones a Telegram"""
    
    def __init__(self, bot_token: str, chat_id: int):
        self.bot = telebot.TeleBot(bot_token)
        self.chat_id = chat_id
        
    async def send_message(self, message: str) -> bool:
        """Envía un mensaje a Telegram"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    parse_mode='HTML'
                )
            )
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")
            return False


class LogMonitor:
    """Monitor de archivos de log"""
    
    def __init__(self, log_file_path: str, notifier: TelegramNotifier):
        self.log_file_path = Path(log_file_path)
        self.notifier = notifier
        self.last_position = 0
        
        # Cargar configuración de tipos de error
        self.error_types = load_error_types()
        self.error_patterns = build_error_patterns(self.error_types)
        
        logger.info(f"Cargados {len(self.error_patterns)} tipos de error: {', '.join(self.error_types.keys())}")
        
    async def check_log_file(self) -> None:
        """Revisa el archivo de log en busca de nuevas entradas"""
        if not self.log_file_path.exists():
            logger.warning(f"Archivo de log no encontrado: {self.log_file_path}")
            return
            
        try:
            # Obtener el tamaño actual del archivo
            current_size = self.log_file_path.stat().st_size
            
            # Si el archivo es más pequeño que la última posición, ha sido rotado
            if current_size < self.last_position:
                logger.info("Archivo de log rotado, reiniciando posición")
                self.last_position = 0
                
            # Si no hay contenido nuevo, salir
            if current_size <= self.last_position:
                return
                
            # Leer solo el contenido nuevo
            async with aiofiles.open(self.log_file_path, 'r', encoding='utf-8') as file:
                await file.seek(self.last_position)
                new_content = await file.read()
                self.last_position = current_size
                
            # Procesar las nuevas líneas
            if new_content:
                await self.process_log_content(new_content)
                
        except Exception as e:
            logger.error(f"Error leyendo archivo de log: {e}")
            
    async def process_log_content(self, content: str) -> None:
        """Procesa el contenido del log buscando errores de autenticación"""
        lines = content.strip().split('\n')
        
        for line in lines:
            if line.strip():
                await self.check_auth_error(line)
                
    async def check_auth_error(self, line: str) -> None:
        """Verifica si una línea contiene un error de autenticación"""
        result = match_auth_error(line, self.error_patterns)
        
        if result:
            error_type, error_data = result
            error_config = self.error_types[error_type]
            await self.send_auth_error_notification(error_type, error_data, error_config)
            
    async def send_auth_error_notification(self, error_type: str, error_data: Dict[str, str], error_config: Dict) -> None:
        """Envía notificación de error de autenticación"""
        try:
            # Convertir la fecha y hora de UTC a la zona horaria configurada
            dt_str = error_data['datetime']
            dt_utc = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            
            # Convertir de UTC a la zona horaria local configurada
            utc_zone = pytz.UTC
            local_zone = pytz.timezone(TZ)
            dt_local = dt_utc.replace(tzinfo=utc_zone).astimezone(local_zone)
            formatted_datetime = dt_local.strftime('%d/%m/%Y %H:%M:%S %Z')
            
            # Determinar el tipo de recurso y valor
            notification_key = error_config['notification_key']
            resource_type = error_config['resource_type']
            resource_value = error_data.get(notification_key, 'N/A')
            
            # Traducir el tipo de error
            translated_error = get_translated_error(error_type, translations)
            
            # Seleccionar etiqueta según el tipo de recurso
            if resource_type == 'email':
                resource_label = translations['tg_email']
                resource_icon = "📧"
            else:
                resource_label = translations['tg_recurso']
                resource_icon = "🔑"
            
            # Crear mensaje usando traducciones
            message = (
                f"🚨 <b>{translations['tg_intento']}</b>\n\n"
                f"📅 <b>{translations['tg_fecha_hora']}:</b> {formatted_datetime}\n"
                f"❌ <b>{translations['tg_motivo']}:</b> {translated_error}\n"
                f"{resource_icon} <b>{resource_label}:</b> {resource_value}\n"
                f"🌐 <b>{translations['tg_ip']}:</b> {error_data['ip']}"
            )
            
            # Log detallado antes de enviar el mensaje
            logger.info(f"Detectado intento fallido: {translated_error} - {resource_value} desde {error_data['ip']} a las {formatted_datetime}")
            
            # Enviar mensaje a Telegram
            success = await self.notifier.send_message(message)
            
            # Log confirmando el envío del mensaje a Telegram
            if success:
                logger.info(f"Mensaje enviado a Telegram - Fecha/Hora: {formatted_datetime}, Motivo: {translated_error}, {resource_label}: {resource_value}, IP: {error_data['ip']}")
            else:
                logger.error(f"Error enviando mensaje a Telegram - Fecha/Hora: {formatted_datetime}, {resource_label}: {resource_value}, IP: {error_data['ip']}")
            
        except Exception as e:
            logger.error(f"Error procesando notificación: {e}")
    
    def reload_error_types(self) -> bool:
        """Recarga los tipos de error desde el archivo JSON"""
        try:
            new_error_types = load_error_types()
            new_patterns = build_error_patterns(new_error_types)
            
            if new_patterns:
                self.error_types = new_error_types
                self.error_patterns = new_patterns
                logger.info(f"Tipos de error recargados exitosamente: {', '.join(self.error_types.keys())}")
                return True
            else:
                logger.error("No se pudieron cargar los nuevos tipos de error")
                return False
                
        except Exception as e:
            logger.error(f"Error recargando tipos de error: {e}")
            return False
            
    async def start_monitoring(self, check_interval: int = 5) -> None:
        """Inicia el monitoreo del archivo de log"""
        logger.info(f"Iniciando monitoreo del archivo: {self.log_file_path}")
        logger.info(f"Intervalo de verificación: {check_interval} segundos")
        
        # Establecer posición inicial al final del archivo si existe
        if self.log_file_path.exists():
            self.last_position = self.log_file_path.stat().st_size
            logger.info(f"Posición inicial: {self.last_position}")
            
        while True:
            try:
                await self.check_log_file()
                await asyncio.sleep(check_interval)
            except KeyboardInterrupt:
                logger.info("Monitoreo detenido por el usuario")
                break
            except Exception as e:
                logger.error(f"Error en el bucle de monitoreo: {e}")
                await asyncio.sleep(check_interval)


async def main():
    """Función principal"""
    generate_trace_id()
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Variables de entorno TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID son requeridas")
        return
        
    if DEBUG:
        logger.debug("Modo debug activado")
    
    # Ruta fija del archivo de log (enlace simbólico)
    log_path = "/log/pangolin.log"
    
    logger.info("Iniciando monitor de logs de Pangolin")
    logger.info(f"Versión: v{VERSION}")
    logger.info(f"Archivo de log: {log_path}")
    logger.info(f"Zona horaria configurada: {TZ}")
    logger.info(f"Idioma configurado: {LANGUAGE}")
    
    # Crear notificador y monitor
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
    monitor = LogMonitor(log_path, notifier)
    
    # Enviar mensaje de inicio con zona horaria local usando traducciones
    local_zone = pytz.timezone(TZ)
    now_local = datetime.now(local_zone)
    await notifier.send_message(
        f"✅ <b>{translations['tg_monitor']}</b> <i>v{VERSION}</i>\n\n"
        f"📁 {translations['tg_monitoreando']}\n"
        f"🕐 {translations['tg_iniciado']}: {now_local.strftime('%d/%m/%Y %H:%M:%S %Z')}\n"
        f"🌍 {translations['tg_zona_horaria']}: {TZ}"
    )
    
    # Iniciar monitoreo
    await monitor.start_monitoring()


if __name__ == "__main__":
    asyncio.run(main())
