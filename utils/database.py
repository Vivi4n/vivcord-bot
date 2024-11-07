import json
import os
from datetime import datetime

class Database:
    def __init__(self, filename):
        self.filename = filename
        self.data = self.load_data()
    
    def load_data(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as f:
                return json.load(f)
        return {}
    
    def save_data(self):
        with open(self.filename, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def log_action(self, user_id, action_type, details):
        user_id = str(user_id)
        if user_id not in self.data:
            self.data[user_id] = {
                "warnings": [],
                "kicks": [],
                "bans": [],
                "mutes": [],
                "messages": 0,
                "message_deletes": 0,
                "voice_time": 0,  # in minutes
                "join_date": str(datetime.utcnow()),
                "last_seen": str(datetime.utcnow()),
                "action_history": []
            }
        
        if action_type in ["warning", "kick", "ban", "mute"]:
            category = f"{action_type}s"
            self.data[user_id][category].append(details)
        
        self.data[user_id]["action_history"].append({
            "type": action_type,
            "details": details,
            "timestamp": str(datetime.utcnow())
        })
        
        self.save_data()