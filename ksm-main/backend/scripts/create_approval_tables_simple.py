#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script sederhana untuk membuat table approval di database
"""

import os
import sys
from datetime import datetime

# Add parent directory to path untuk import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.database import db, init_database
from flask import Flask
from sqlalchemy import text

def create_app():
    """Create Flask app untuk database operations"""
    app = Flask(__name__)
    
    # Database configuration
    db_user = os.getenv('DB_USER', 'root')
    db_password = os.getenv('DB_PASSWORD', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME', 'KSM_main')
    charset = 'utf8mb4'
    
    # Coba MySQL dulu, fallback ke SQLite jika gagal
    mysql_uri = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?charset={charset}"
    
    # Test MySQL connection
    try:
        import pymysql
        connection = pymysql.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name,
            charset=charset
        )
        connection.close()
        app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
        print("✅ Connected to MySQL database")
    except Exception as e:
        print(f"⚠️ MySQL connection failed: {e}")
        print("🔄 Falling back to SQLite...")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///KSM_main_fallback.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'KSM-main-secret-key'
    
    return app

def create_approval_tables():
    """Create approval tables dengan SQL langsung"""
    try:
        print("🚀 Creating approval tables...")
        
        # Create app
        app = create_app()
        
        # Initialize database
        init_database(app)
        
        with app.app_context():
            # SQL untuk membuat table approval_requests
            approval_requests_sql = """
            CREATE TABLE IF NOT EXISTS approval_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                workflow_id INT,
                requester_id INT,
                module VARCHAR(50),
                action_type VARCHAR(50),
                resource_id INT,
                resource_data JSON,
                status VARCHAR(20) DEFAULT 'pending',
                current_step INT DEFAULT 1,
                timeout_at DATETIME,
                completed_at DATETIME,
                rejection_reason TEXT,
                delegation_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # SQL untuk membuat table approval_workflows
            approval_workflows_sql = """
            CREATE TABLE IF NOT EXISTS approval_workflows (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                module VARCHAR(50) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                description TEXT,
                department_id INT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # SQL untuk membuat table approval_steps
            approval_steps_sql = """
            CREATE TABLE IF NOT EXISTS approval_steps (
                id INT AUTO_INCREMENT PRIMARY KEY,
                workflow_id INT,
                step_order INT NOT NULL,
                step_name VARCHAR(100) NOT NULL,
                approver_role_id INT,
                approval_type VARCHAR(20) DEFAULT 'single',
                is_required BOOLEAN DEFAULT TRUE,
                timeout_hours INT DEFAULT 24,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # SQL untuk membuat table approval_actions
            approval_actions_sql = """
            CREATE TABLE IF NOT EXISTS approval_actions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id INT NOT NULL,
                step_id INT NOT NULL,
                approver_id INT,
                action_type VARCHAR(20) NOT NULL,
                comments TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # SQL untuk membuat table escalation_logs
            escalation_logs_sql = """
            CREATE TABLE IF NOT EXISTS escalation_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                request_id INT NOT NULL,
                escalated_from_user_id INT,
                escalated_to_user_id INT,
                escalation_reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            # SQL untuk membuat table approval_templates
            approval_templates_sql = """
            CREATE TABLE IF NOT EXISTS approval_templates (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                module VARCHAR(50) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                template_data JSON,
                department_id INT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
            """
            
            # Execute SQL statements
            tables = [
                ("approval_requests", approval_requests_sql),
                ("approval_workflows", approval_workflows_sql),
                ("approval_steps", approval_steps_sql),
                ("approval_actions", approval_actions_sql),
                ("escalation_logs", escalation_logs_sql),
                ("approval_templates", approval_templates_sql)
            ]
            
            for table_name, sql in tables:
                try:
                    db.session.execute(text(sql))
                    db.session.commit()
                    print(f"✅ Created table: {table_name}")
                except Exception as e:
                    print(f"⚠️ Error creating table {table_name}: {e}")
                    db.session.rollback()
            
            print("🎉 All approval tables created successfully!")
            
            # Add sample data
            add_sample_data(app)
            
    except Exception as e:
        print(f"❌ Error creating approval tables: {e}")
        import traceback
        traceback.print_exc()

def add_sample_data(app):
    """Add sample data untuk testing"""
    try:
        print("📝 Adding sample data...")
        
        with app.app_context():
            # Check if data already exists
            result = db.session.execute(text("SELECT COUNT(*) FROM approval_workflows"))
            count = result.scalar()
            
            if count > 0:
                print("⚠️ Sample data already exists, skipping...")
                return
            
            # Add sample approval workflow
            workflow_sql = """
            INSERT INTO approval_workflows (name, module, action_type, description, is_active)
            VALUES ('User Registration Workflow', 'user_management', 'create_user', 'Workflow for user registration approval', TRUE)
            """
            
            db.session.execute(text(workflow_sql))
            db.session.commit()
            
            # Get workflow ID
            result = db.session.execute(text("SELECT id FROM approval_workflows WHERE name = 'User Registration Workflow'"))
            workflow_id = result.scalar()
            
            # Add workflow steps
            steps_sql = [
                """
                INSERT INTO approval_steps (workflow_id, step_order, step_name, approval_type, is_required, timeout_hours)
                VALUES (?, 1, 'Manager Approval', 'single', TRUE, 24)
                """,
                """
                INSERT INTO approval_steps (workflow_id, step_order, step_name, approval_type, is_required, timeout_hours)
                VALUES (?, 2, 'Admin Approval', 'single', TRUE, 48)
                """
            ]
            
            for step_sql in steps_sql:
                db.session.execute(text(step_sql), {'workflow_id': workflow_id})
            
            db.session.commit()
            print("✅ Added sample approval workflow")
            
            print("🎉 Sample data added successfully!")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        import traceback
        traceback.print_exc()
        with app.app_context():
            db.session.rollback()

if __name__ == '__main__':
    create_approval_tables()
