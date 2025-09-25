import contextvars
import json
import logging
import random
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

from colorama import Fore, Style, init

from config import DEBUG

# Inicializar colorama
# Asegura que los códigos ANSI no se eliminen en macOS.
init(strip=False)

COLORS = {
    logging.DEBUG: Fore.GREEN,
    logging.INFO: Fore.WHITE,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT,
}

trace_id_var = contextvars.ContextVar("trace_id")
class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = trace_id_var.get("----")
        return True
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Aplicar color según el nivel del log
        color = COLORS.get(record.levelno, Fore.WHITE)
        record.msg = f"{color}{record.msg}{Style.RESET_ALL}"
        return super().format(record)

def setup_logger(name: str):
    logger = logging.getLogger(name)

    if DEBUG == 0:
        logger.setLevel(logging.INFO)
    else:  # DEBUG 1 o 2
        logger.setLevel(logging.DEBUG)

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = ColoredFormatter("[%(asctime)s] [%(trace_id)s] [%(levelname)s] %(message)s", datefmt="%d-%m-%Y %H:%M:%S")
        handler.setFormatter(formatter)
        handler.addFilter(TraceIdFilter())
        logger.addHandler(handler)

    # Control exhaustivo de librerías de terceros
    third_party_loggers = [
        'urllib3',
        'requests',
        'urllib3.connectionpool',
    ]

    for lib in third_party_loggers:
        lib_logger = logging.getLogger(lib)
        lib_logger.setLevel(logging.WARNING)
        lib_logger.propagate = False
        for handler in lib_logger.handlers[:]:
            lib_logger.removeHandler(handler)

    return logger

def generate_trace_id():
    trace_id_var.set(random.randint(1000, 9999))


def load_error_types(file_path: str = "tipos_error.json") -> Dict:
    """Carga los tipos de error desde el archivo JSON"""
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Archivo de tipos de error no encontrado: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error cargando tipos de error: {e}")
        return {}


def build_error_patterns(error_types: Dict) -> Dict[str, re.Pattern]:
    """Construye los patrones regex para cada tipo de error"""
    patterns = {}
    
    base_datetime_pattern = r'(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z).*?'
    
    for error_type, config in error_types.items():
        full_pattern = base_datetime_pattern + config['pattern']
        try:
            patterns[error_type] = re.compile(full_pattern)
        except re.error as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error compilando patrón regex para '{error_type}': {e}")
            
    return patterns


def match_auth_error(line: str, error_patterns: Dict[str, re.Pattern]) -> Optional[Tuple[str, Dict[str, str]]]:
    """
    Verifica si una línea coincide con algún patrón de error de autenticación
    
    Returns:
        Tuple[error_type, match_data] si encuentra coincidencia, None en caso contrario
    """
    for error_type, pattern in error_patterns.items():
        match = pattern.search(line)
        if match:
            return error_type, match.groupdict()
    
    return None


def get_translated_error(error_type: str, translations: Dict) -> str:
    """
    Obtiene la traducción de un tipo de error
    
    Args:
        error_type: El tipo de error en inglés
        translations: Diccionario de traducciones cargado
    
    Returns:
        El error traducido o el original si no hay traducción
    """
    error_translations = translations.get('error_translations', {})
    return error_translations.get(error_type, error_type)

