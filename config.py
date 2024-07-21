import os
from datetime import timedelta

class BaseConfig:
    DATE_FORMAT = "%d/%m/%Y"
    PREFERRED_URL_SCHEME = "https"
    BACKEND_VERSION = os.environ.get('VERSION', None)
    JSON_SORT_KEYS = False
    DATA_VERSIONING_SUPPORTED_COLLECTIONS = ['transaction']

    # Flask Admin
    SECRET_KEY = os.environ.get('SECRET_KEY', 'a4f170dfa18c005e4a5ab155b1a9ec83ae1d155d05d41067')
    FLASK_ADMIN_FLUID_LAYOUT = os.environ.get('FLASK_ADMIN_FLUID_LAYOUT', True)

    # GOOGLE
    GOOGLE_WEBCLIENT_ID = os.environ.get('GOOGLE_WEBCLIENT_ID', None)

    # JWT
    JWT_SECRETS = os.environ.get('JWT_SECRETS', 'unravel_so_SECURE')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_DELTA = timedelta(hours=1)
    JWT_EXPIRATION = 3600 * 3  # 3 hours
    JWT_EXPIRATION_LONG = 86400 * 30  # 30 days
    INVITATION_TOKEN_EXPIRE_DAYS = 7  # 7 days
    # Mongo engine
    MONGODB_HOST = os.environ.get('MONGODB_HOST', 'mongodb://localhost:27017/nomura?serverSelectionTimeoutMs=500')

    # CORS
    # CORS_ORIGINS = os.environ.get('CORS_ORIGINS', [r'.*localhost:3000$'])