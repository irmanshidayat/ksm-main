import os
from datetime import timedelta

class JWTConfig:
    # JWT Secret Key - dalam production harus menggunakan environment variable
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'KSM-jwt-secret-key-2024-super-secure'
    
    # JWT Token Expiration
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # 15 menit
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)     # 7 hari
    
    # JWT Algorithm
    JWT_ALGORITHM = 'HS256'
    
    # JWT Token Location
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # JWT Error Messages
    JWT_ERROR_MESSAGE_KEY = 'error'
    
    # JWT Additional Claims
    JWT_ACCESS_CSRF_HEADER_NAME = 'X-CSRF-TOKEN'
    
    # JWT Cookie Settings (untuk future use)
    JWT_COOKIE_SECURE = False  # Set True in production with HTTPS
    JWT_COOKIE_CSRF_PROTECT = False
    JWT_COOKIE_SAMESITE = 'Lax'
    
    # JWT Blacklist Settings - DISABLED untuk debugging
    JWT_BLACKLIST_ENABLED = False
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    @classmethod
    def init_app(cls, app):
        """Initialize JWT configuration with Flask app"""
        app.config['JWT_SECRET_KEY'] = cls.JWT_SECRET_KEY
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = cls.JWT_ACCESS_TOKEN_EXPIRES
        app.config['JWT_REFRESH_TOKEN_EXPIRES'] = cls.JWT_REFRESH_TOKEN_EXPIRES
        app.config['JWT_ALGORITHM'] = cls.JWT_ALGORITHM
        app.config['JWT_TOKEN_LOCATION'] = cls.JWT_TOKEN_LOCATION
        app.config['JWT_HEADER_NAME'] = cls.JWT_HEADER_NAME
        app.config['JWT_HEADER_TYPE'] = cls.JWT_HEADER_TYPE
        app.config['JWT_ERROR_MESSAGE_KEY'] = cls.JWT_ERROR_MESSAGE_KEY
        app.config['JWT_ACCESS_CSRF_HEADER_NAME'] = cls.JWT_ACCESS_CSRF_HEADER_NAME
        app.config['JWT_COOKIE_SECURE'] = cls.JWT_COOKIE_SECURE
        app.config['JWT_COOKIE_CSRF_PROTECT'] = cls.JWT_COOKIE_CSRF_PROTECT
        app.config['JWT_COOKIE_SAMESITE'] = cls.JWT_COOKIE_SAMESITE
        app.config['JWT_BLACKLIST_ENABLED'] = cls.JWT_BLACKLIST_ENABLED
        app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = cls.JWT_BLACKLIST_TOKEN_CHECKS
