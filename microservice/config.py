import os
from urllib.parse import quote_plus

class Config:
    DEBUG = False
    TESTING = False
    
    password = quote_plus('12')
    DATABASE_URI = f"postgresql://emos:{password}@localhost:5432/claim?sslmode=disable"
    
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}