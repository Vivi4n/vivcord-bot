import json
import os
from datetime import datetime
import logging

class Database:
    def __init__(self, filename):
        self.filename = filename
        self.logger = logging.getLogger('Database')
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.data = self.load_data()
    
    def load_data(self):
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse {self.filename}")
            # If the file is empty or invalid, return an empty dict
            pass
        return {}
    
    def save_data(self):
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.filename), exist_ok=True)
            # Save with pretty printing
            with open(self.filename, 'w') as f:
                json.dump(self.data, f, indent=4)
            self.logger.info(f"Saved data to {self.filename}")
        except Exception as e:
            self.logger.error(f"Failed to save data: {str(e)}")
    
    def ensure_user_data(self, user_id):
        """Ensure user entry exists with all required fields"""
        user_id = str(user_id)
        if user_id not in self.data:
            self.logger.info(f"Creating new user data for {user_id}")
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
        self.logger.info(f"Logging action {action_type} for user {user_id}")
        user_data = self.ensure_user_data(user_id)
        
        # Add to specific category array
        category_mapping = {
            "warnings": "warnings",
            "warning": "warnings",  # Add both singular and plural
            "kick": "kicks",
            "ban": "bans",
            "mute": "mutes"
        }
        
        if action_type in category_mapping:
            category = category_mapping[action_type]
            self.logger.info(f"Adding to category {category}")
            user_data[category].append(details.copy())
        
        # Add to general action history
        action_entry = {
            "type": action_type,
            "details": details.copy(),
            "timestamp": str(datetime.utcnow())
        }
        user_data["action_history"].append(action_entry)
        
        self.save_data()
        self.logger.info(f"Action logged successfully for {user_id}")