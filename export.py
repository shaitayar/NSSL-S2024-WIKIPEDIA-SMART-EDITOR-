import json
import os
from datetime import datetime
import glob

class Export():
    def __init__(self):
        self.fname = f"export_{datetime.now().strftime('%Y%m%d_%H')}.json"
        self.folder = "exports"

        os.makedirs(self.folder, exist_ok=True)

    def export_to_json(self, data, class_name):
        filepath = os.path.join(self.folder, self.fname)
        structured_data = {class_name: data}

        with open(filepath, "a") as file:
            json.dump(structured_data, file)

        print(f"Data successfully exported to {filepath}")

class Import():
    def __init__(self, filename):
        self.filename = filename
        self.data = []

    def get_latest_json(self):
        json_files = glob.glob(os.path.join("exports","export_*.json"))
        if not json_files:
            return None
        return max(json_files, key=os.path.getctime)

    def import_from_json(self):
        if(self.filename != ""):
            filepath = os.path.join("exports", self.filename)
        else:
            file = self.get_latest_json()
            filepath = os.path.join("exports", file)

        with open(filepath, "r") as file:
            try:
                data = json.load(file)
            except json.JSONDecodeError:
                print(f"Error Loading {filepath} data")

