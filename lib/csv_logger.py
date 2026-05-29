import csv
import os
from datetime import datetime

class CSVLogger:
    def __init__(self, filepath="test_results.csv"):
        self.filepath = filepath
        self.headers = ["Timestamp", "Test_ID", "Category", "Target", "Status", "Details"]
        self._initialize_file()

    def _initialize_file(self):
        if not os.path.exists(self.filepath):
            with open(self.filepath, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.headers)

    def log(self, test_id, category, target, status, details):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, test_id, category, target, status, details])
        
        # Also print to console for user friendliness
        color = "\033[92m" if status.upper() == "PASS" else "\033[91m"
        reset = "\033[0m"
        print(f"[{timestamp}] {color}[{status}]{reset} {test_id} ({category}): {details}")
