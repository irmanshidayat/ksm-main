#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Timezone Utilities untuk KSM Main Backend
Utility functions untuk menangani timezone Jakarta
"""

from datetime import datetime
import pytz
from config.config import Config

def get_jakarta_time():
    """
    Get current time in Jakarta timezone (Asia/Jakarta)
    
    Returns:
        datetime: Current time in Jakarta timezone
    """
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    return datetime.now(jakarta_tz)

def get_jakarta_utc_time():
    """
    Get current time in Jakarta timezone but return as UTC datetime
    This is useful for database storage where we want to store Jakarta time as UTC
    
    Returns:
        datetime: Current Jakarta time as UTC datetime
    """
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    jakarta_time = datetime.now(jakarta_tz)
    # Convert to UTC for database storage
    return jakarta_time.astimezone(pytz.UTC).replace(tzinfo=None)

def utc_to_jakarta(utc_datetime):
    """
    Convert UTC datetime to Jakarta timezone
    
    Args:
        utc_datetime (datetime): UTC datetime
        
    Returns:
        datetime: Jakarta timezone datetime
    """
    if utc_datetime is None:
        return None
    
    utc_tz = pytz.UTC
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    
    # If datetime is naive, assume it's UTC
    if utc_datetime.tzinfo is None:
        utc_datetime = utc_tz.localize(utc_datetime)
    
    return utc_datetime.astimezone(jakarta_tz)

def jakarta_to_utc(jakarta_datetime):
    """
    Convert Jakarta datetime to UTC for database storage
    
    Args:
        jakarta_datetime (datetime): Jakarta timezone datetime
        
    Returns:
        datetime: UTC datetime
    """
    if jakarta_datetime is None:
        return None
    
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    utc_tz = pytz.UTC
    
    # If datetime is naive, assume it's Jakarta time
    if jakarta_datetime.tzinfo is None:
        jakarta_datetime = jakarta_tz.localize(jakarta_datetime)
    
    return jakarta_datetime.astimezone(utc_tz).replace(tzinfo=None)

def format_jakarta_datetime(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """
    Format datetime to Jakarta timezone string
    
    Args:
        dt (datetime): Datetime to format
        format_str (str): Format string
        
    Returns:
        str: Formatted datetime string in Jakarta timezone
    """
    if dt is None:
        return None
    
    jakarta_dt = utc_to_jakarta(dt)
    return jakarta_dt.strftime(format_str)

def get_jakarta_date():
    """
    Get current date in Jakarta timezone
    
    Returns:
        date: Current date in Jakarta timezone
    """
    return get_jakarta_time().date()
