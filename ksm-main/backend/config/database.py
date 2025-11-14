#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Configuration untuk KSM Main Backend
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os

# Import models akan dilakukan setelah db diinisialisasi

# Inisialisasi SQLAlchemy
db = SQLAlchemy()
migrate = Migrate()

def init_database(app):
    """Initialize database dengan SQLAlchemy"""
    # Import config untuk mendapatkan environment detection
    from config.config import detect_environment, get_env_config
    
    # Detect environment
    env_mode = detect_environment()
    env_config = get_env_config()
    
    # Konfigurasi database MySQL (via ENV, fallback ke config)
    db_user = os.getenv('DB_USER', 'root')
    # Handle DB_PASSWORD: jika empty string atau None, gunakan default berdasarkan environment
    db_password_raw = os.getenv('DB_PASSWORD')
    if db_password_raw is None or db_password_raw.strip() == '':
        # Jika tidak ter-set atau empty, gunakan default dari env_config
        # Docker mode: default password adalah 'admin123'
        # Local/XAMPP mode: default password adalah '' (kosong)
        db_password = env_config.get('DB_PASSWORD', 'admin123' if env_mode == 'docker' else '')
        if env_mode == 'docker':
            print(f"ℹ️  DB_PASSWORD not set in .env, using default: 'admin123' for Docker mode")
            print("   To use custom password, set DB_PASSWORD in .env file")
    else:
        db_password = db_password_raw
    
    db_host = os.getenv('DB_HOST') or env_config.get('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT') or str(env_config.get('DB_PORT', 3306))
    db_name = os.getenv('DB_NAME', 'KSM_main')
    charset = 'utf8mb4'
    
    # Normalize host untuk menghindari Docker network gateway
    # Jika localhost atau 127.0.0.1, pastikan menggunakan 127.0.0.1 untuk menghindari routing issues
    if db_host in ['localhost', '127.0.0.1'] or env_mode == 'local':
        # Gunakan 127.0.0.1 untuk menghindari Docker network gateway (172.18.0.1)
        if db_host == 'localhost':
            db_host = '127.0.0.1'

    # Test MySQL connection dengan retry logic dan multiple fallback options
    # mysql_uri akan diupdate setelah koneksi berhasil
    import pymysql
    connection_success = False
    last_error = None
    
    # Define fallback options untuk XAMPP
    fallback_options = []
    
    # Jika bukan docker mode atau host bukan docker service, tambahkan XAMPP fallbacks
    if env_mode == 'local' or db_host in ['localhost', '127.0.0.1']:
        # XAMPP default options - gunakan 127.0.0.1 untuk menghindari Docker network gateway
        # Jika port bukan 3306, tambahkan opsi dengan port 3306 terlebih dahulu
        if db_port != '3306':
            fallback_options.append({'host': '127.0.0.1', 'port': 3306, 'password': ''})
        # Tambahkan opsi dengan password kosong (XAMPP default)
        if db_password:
            fallback_options.append({'host': '127.0.0.1', 'port': int(db_port), 'password': ''})
    
    # Jika docker mode tapi gagal, coba fallback ke XAMPP
    elif env_mode == 'docker' and db_host not in ['localhost', '127.0.0.1']:
        fallback_options = [
            {'host': '127.0.0.1', 'port': 3306, 'password': ''},
        ]
    
    # Try primary connection (from config)
    # Convert empty string password to None untuk pymysql (None = no password attempt)
    # Tapi untuk MySQL 8.0 di Docker, password harus ada
    password_for_connection = db_password if db_password else None
    
    connection_configs = [
        {'host': db_host, 'port': int(db_port), 'password': password_for_connection}
    ] + fallback_options
    
    for i, config in enumerate(connection_configs):
        try:
            # Handle None password (untuk XAMPP yang tidak pakai password)
            # Tapi untuk MySQL 8.0 di Docker, password harus ada
            password = config['password'] if config['password'] is not None else ''
            
            connection = pymysql.connect(
                host=config['host'],
                port=config['port'],
                user=db_user,
                password=password,
                database=db_name,
                charset=charset,
                connect_timeout=5
            )
            connection.close()
            connection_success = True
            
            # Update config dengan connection yang berhasil
            db_host = config['host']
            db_port = str(config['port'])
            # Handle None password untuk mysql_uri (None = no password)
            db_password_for_uri = config['password'] if config['password'] is not None else ''
            mysql_uri = f"mysql+pymysql://{db_user}:{db_password_for_uri}@{db_host}:{db_port}/{db_name}?charset={charset}"
            
            if i > 0:  # Jika bukan primary connection
                print(f"✓ MySQL connection successful (fallback): {db_user}@{db_host}:{db_port}/{db_name} (mode: {env_mode})")
            else:
                print(f"✓ MySQL connection successful: {db_user}@{db_host}:{db_port}/{db_name} (mode: {env_mode})")
            break
        except Exception as e:
            last_error = e
            if i == 0:
                print(f"⚠ Primary MySQL connection failed ({config['host']}:{config['port']}): {e}")
            else:
                print(f"⚠ Fallback {i} failed ({config['host']}:{config['port']}): {e}")
            continue
    
    if not connection_success:
        error_msg = f"Database connection failed: {last_error}"
        print(f"✗ {error_msg}")
        print("Please ensure:")
        print("  - For XAMPP: MySQL is running on localhost:3306")
        print("  - For Docker: MySQL container is running and accessible")
        print("  - Database 'KSM_main' exists")
        print("  - Check DB_HOST, DB_PORT, DB_USER, DB_PASSWORD in .env file")
        if env_mode == 'docker':
            print("")
            print("⚠️ DOCKER MODE DETECTED:")
            print("  - DB_PASSWORD must be set in .env file")
            print("  - DB_PASSWORD must match MYSQL_ROOT_PASSWORD in mysql-prod container")
            print("  - Current DB_PASSWORD value:", "NOT SET" if not db_password else f"'{db_password[:3]}...' (length: {len(db_password)})")
            print("  - Check your .env file and ensure DB_PASSWORD is not empty")
        raise Exception(error_msg)
    
    # Set SQLAlchemy configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 10,
            'charset': charset
        }
    }
    print(f"✓ Using MySQL database: {db_name}")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inisialisasi SQLAlchemy dan Migrate
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import models setelah db diinisialisasi untuk menghindari circular import
    with app.app_context():
        # RemindExpDocs sudah dipindah ke domains/task/models
        # Tidak perlu diimport lagi di sini
        # Knowledge models sudah diimport di models_init.py, tidak perlu diimport lagi di sini
        from models.notion_database import NotionDatabase
        from models.property_mapping import PropertyMapping
        from domains.mobil.models.mobil_models import MobilRequest, WaitingList, Mobil, MobilUsageLog
        # Request pembelian models sudah dipindah ke domains/inventory/models
        # Tidak perlu diimport lagi di sini
        from models.vendor_order_models import VendorOrder
    
    return db
