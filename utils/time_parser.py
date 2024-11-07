import re
from datetime import datetime, timedelta

def parse_time(time_str):
    """Convert a time string (e.g., '24h', '30m', '7d') to seconds"""
    if not time_str:
        return None
    
    time_mapping = {
        'm': 60,          # minutes to seconds
        'h': 3600,        # hours to seconds
        'd': 86400        # days to seconds
    }
    
    pattern = r'(\d+)([mhd])'
    match = re.match(pattern, time_str.lower())
    
    if not match:
        return None
    
    amount, unit = match.groups()
    return int(amount) * time_mapping[unit]