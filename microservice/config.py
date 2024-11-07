import os
from urllib.parse import quote_plus  # Add this for password encoding

class Config:
    # Base configuration
    DEBUG = False
    TESTING = False
    
    # Database configuration with properly escaped password
    password = quote_plus('12')  # Escape the password
    DATABASE_URI = f"postgresql://emos:{password}@localhost:5432/claim?sslmode=disable"
    
    # Service configuration
    PORT = int(os.environ.get('PORT', 5000))
    HOST = os.environ.get('HOST', '0.0.0.0')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

# Map environment to config
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}