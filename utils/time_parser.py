import re
from datetime import datetime, timedelta

class TimeParseError(Exception):
    """Custom exception for time parsing errors"""
    pass

def parse_time(time_str):
    """Convert a time string (e.g., '24h', '30m', '7d') to seconds"""
    if not time_str:
        return None
    
    time_str = time_str.strip().lower()
    
    time_mapping = {
        'm': ('minutes', 60),
        'h': ('hours', 3600),
        'd': ('days', 86400)
    }
    
    pattern = r'^(\d+)([mhd])$'
    match = re.match(pattern, time_str)
    
    if not match:
        raise TimeParseError(
            f"Invalid time format: '{time_str}'. Please use format: <number><unit> "
            f"where unit is 'm' for minutes, 'h' for hours, or 'd' for days."
        )
    
    amount, unit = match.groups()
    
    try:
        amount = int(amount)
        if amount <= 0:
            raise TimeParseError(f"Time amount must be positive")
        if amount > 365 and unit == 'd':
            raise TimeParseError(f"Time too large: maximum 365 days")
        if amount > 24 and unit == 'h':
            raise TimeParseError(f"Time too large: maximum 24 hours")
        if amount > 1440 and unit == 'm':
            raise TimeParseError(f"Time too large: maximum 1440 minutes")
            
        return amount * time_mapping[unit][1]
        
    except ValueError:
        raise TimeParseError(f"Invalid number: {amount}")

def format_duration(seconds):
    """Convert seconds into a human-readable duration string"""
    if seconds is None:
        return "permanent"
        
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds > 0 and not parts:
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
    return " ".join(parts)