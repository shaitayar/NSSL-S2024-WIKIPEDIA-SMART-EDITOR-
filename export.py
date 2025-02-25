import json
import os
from datetime import datetime

class Export():
    def __init__(self, fname, folder= ""):
        self.fname = fname
        self.folder = folder

    def export_to_json(self, data, class_name):
        if self.folder == "":
            self.folder = f"export_{datetime.now().strftime('%Y%m%d_%H')}"
        filepath = os.path.join(self.folder, self.fname)
        structured_data = {class_name: data}

        with open(filepath, "a") as file:
            json.dump(structured_data, file)

        print(f"Data successfully exported to {filepath}")
