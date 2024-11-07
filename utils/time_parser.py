import re
from datetime import datetime, timedelta

class TimeParseError(Exception):
    """Custom exception for time parsing errors"""
    pass

def parse_time(time_str):
    """
    Convert a time string (e.g., '24h', '30m', '7d') to seconds
    
    Args:
        time_str (str): Time string in format: <number><unit>
                       Units: m (minutes), h (hours), d (days)
                       
    Returns:
        int: Time in seconds
        
    Raises:
        TimeParseError: If the time string format is invalid
    """
    if not time_str:
        return None
    
    # Strip whitespace
    time_str = time_str.strip().lower()
    
    time_mapping = {
        'm': ('minutes', 60),        # minutes to seconds
        'h': ('hours', 3600),       # hours to seconds
        'd': ('days', 86400)        # days to seconds
    }
    
    pattern = r'^(\d+)([mhd])$'
    match = re.match(pattern, time_str)
    
    if not match:
        raise TimeParseError(
            f"Invalid time format: '{time_str}'. "
            f"Please use format: <number><unit> "
            f"where unit is 'm' for minutes, 'h' for hours, or 'd' for days. "
            f"Examples: '30m', '24h', '7d'"
        )
    
    amount, unit = match.groups()
    
    try:
        amount = int(amount)
        if amount <= 0:
            raise TimeParseError(f"Time amount must be positive, got: {amount}")
        if amount > 365 and unit == 'd':  # Reasonable limit for days
            raise TimeParseError(f"Time too large: maximum 365 days")
        if amount > 24 and unit == 'h':   # Reasonable limit for hours
            raise TimeParseError(f"Time too large: maximum 24 hours")
        if amount > 1440 and unit == 'm':  # Reasonable limit for minutes (24 hours)
            raise TimeParseError(f"Time too large: maximum 1440 minutes (24 hours)")
            
        return amount * time_mapping[unit][1]
        
    except ValueError:
        raise TimeParseError(f"Invalid number: {amount}")

def format_duration(seconds):
    """
    Convert seconds into a human-readable duration string
    
    Args:
        seconds (int): Number of seconds
        
    Returns:
        str: Formatted duration string (e.g., "1 day 2 hours 30 minutes")
    """
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
    if seconds > 0 and not parts:  # Only show seconds if no larger unit
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
    return " ".join(parts)

# Example usage:
if __name__ == "__main__":
    test_times = ["30m", "24h", "7d", "1h", "60m", "invalid", "0m", "-5h"]
    
    for time_str in test_times:
        try:
            seconds = parse_time(time_str)
            print(f"{time_str} = {seconds} seconds ({format_duration(seconds)})")
        except TimeParseError as e:
            print(f"Error parsing '{time_str}': {str(e)}")