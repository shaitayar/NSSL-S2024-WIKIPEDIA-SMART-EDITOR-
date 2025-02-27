import json
import os
from datetime import datetime
import glob


class Export:
    def __init__(self, filename=""):
        self.filename = filename if filename != "" else f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        self.folder = "exports"

        os.makedirs(self.folder, exist_ok=True)

    def export_to_json(self, data, class_name):
        filepath = os.path.join(self.folder, self.filename)

        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            with open(filepath, "r") as file:
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, dict):
                        existing_data = {}
                except json.JSONDecodeError:
                    existing_data = {}
        else:
            existing_data = {}

        existing_data[class_name] = data

        with open(filepath, "w") as file:
            json.dump(existing_data, file, indent=4)

        print(f"Data successfully exported to {filepath}")


class Import:
    def __init__(self, filename):
        self.filename = filename
        self.data = []

    def get_latest_json(self):
        json_files = glob.glob(os.path.join("exports", "export_*.json"))
        if not json_files:
            return None
        return max(json_files, key=os.path.getctime)

    def import_from_json(self):
        if(self.filename != ""):
            filepath = os.path.join("exports", self.filename)
        else:
            filepath = self.get_latest_json()

        with open(filepath, "r") as file:
            try:
                self.data = json.load(file)
            except json.JSONDecodeError:
                print(f"Error Loading {filepath} data")

