import os
import secrets

# Configuration
LMS_DB_DIR = '/config'
EXPORT_DIR = '/exports'
PUID = os.environ.get('PUID')
PGID = os.environ.get('PGID')
SECRET_KEY = os.environ.get('SECRET_KEY', secrets.token_hex(32))
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 