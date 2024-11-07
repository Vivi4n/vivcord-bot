import json
import os
from datetime import datetime

class Database:
    def __init__(self, filename):
        self.filename = filename
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.data = self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            # If the file is empty or invalid, return an empty dict
            pass
        return {}
    
    def save_data(self):
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
        # Save with pretty printing
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def ensure_user_data(self, user_id):
        """Ensure user entry exists with all required fields"""
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {
                "warnings": [],
                "kicks": [],
                "bans": [],
                "mutes": [],
                "messages": 0,
                "message_deletes": 0,
                "voice_time": 0,
                "join_date": str(datetime.utcnow()),
                "last_seen": str(datetime.utcnow()),
                "action_history": []
            }
        return self.data[user_id]
    
    def log_action(self, user_id, action_type, details):
        """Log an action with proper user data initialization"""
        user_data = self.ensure_user_data(user_id)
        
        # Add to specific category array
        category_mapping = {
            "warnings": "warnings",  # Changed from "warning" to "warnings"
            "kick": "kicks",
            "ban": "bans",
            "mute": "mutes"
        }
        
        if action_type in category_mapping:
            category = category_mapping[action_type]
            user_data[category].append(details.copy())  # Use copy to prevent reference issues
        
        # Add to general action history
        action_entry = {
            "type": action_type,
            "details": details.copy(),  # Use copy to prevent reference issues
            "timestamp": str(datetime.utcnow())
        }
        user_data["action_history"].append(action_entry)
        
        self.save_data()