# logger.py
import json
from datetime import datetime
import os


class JarvisLogger:
    def __init__(self, log_dir="logs"):  # Removed jarvis_instance requirement
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Create new log file for each session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = os.path.join(log_dir, f"jarvis_log_{timestamp}.json")
        self.session_logs = {
            "session_start": timestamp,
            "conversations": [],
            "system_logs": [],
            "vision_logs": []
        }
        self.save_logs()
        print(f"Logger initialized. Logging to: {self.log_file}")

    def log_conversation(self, user_input, jarvis_response, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conversation = {
            "timestamp": timestamp,
            "user_input": user_input,
            "jarvis_response": jarvis_response
        }
        self.session_logs["conversations"].append(conversation)
        self.save_logs()

    def log_system(self, event_type, details, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        system_log = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details
        }
        self.session_logs["system_logs"].append(system_log)
        self.save_logs()

    def log_vision(self, event_type, details, detections=None, timestamp=None):
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        vision_log = {
            "timestamp": timestamp,
            "event_type": event_type,
            "details": details,
            "detections": detections if detections else []
        }
        self.session_logs["vision_logs"].append(vision_log)
        self.save_logs()

    def save_logs(self):
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_logs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving logs: {e}")
