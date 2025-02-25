import json
import os
from datetime import datetime

class Export():
    def __init__(self, fname, folder= ""):
        self.fname = fname if fname.endswith(".json") else f"{fname}.json"
        self.folder = folder or f"exports\export_{datetime.now().strftime('%Y%m%d_%H')}"

        os.makedirs(self.folder, exist_ok=True)

    def export_to_json(self, data, class_name):
        filepath = os.path.join(self.folder, self.fname)
        structured_data = {class_name: data}

        with open(filepath, "w") as file:
            json.dump(structured_data, file)

        print(f"Data successfully exported to {filepath}")
