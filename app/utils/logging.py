import logging
import logging.config
from app.core.config import settings

# Membaca level log dari variabel lingkungan
log_level = settings.log_level

# Mengonversi level log yang dibaca menjadi level yang valid dari modul logging
LOGGING_LEVEL = getattr(logging, log_level, logging.INFO)  # Default ke INFO jika tidak ditemukan

FMT = "[{levelname:^7}] {name}: {message}"
FORMATS = {
    logging.DEBUG: FMT,
    logging.INFO: f"\33[36m{FMT}\33[0m",
    logging.WARNING: f"\33[33m{FMT}\33[0m",
    logging.ERROR: f"\33[31m{FMT}\33[0m",
    logging.CRITICAL: f"\33[1m\33[31m{FMT}\33[0m",
}

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_fmt = FORMATS[record.levelno]
        formatter = logging.Formatter(log_fmt, style="{")
        return formatter.format(record)

# Membuat StreamHandler dengan formatter kustom
handler = logging.StreamHandler()
handler.setFormatter(CustomFormatter())
# Konfigurasi logging global
logging.basicConfig(
    level=LOGGING_LEVEL,
    handlers=[handler]
)

log = logging.getLogger("uvicorn")
log.setLevel(LOGGING_LEVEL)
log.handlers = [handler]