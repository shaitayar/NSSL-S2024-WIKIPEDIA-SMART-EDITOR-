import json
import os
from datetime import datetime

class Export():
    def __init__(self, data, folder):
        self.data = data
        self.folder = folder

    def export_to_json(self):
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        filepath = os.path.join(self.folder, filename)

        with open(filepath, "w") as file:
            json.dump(self.data, file)

        print(f"Data successfully exported to {filepath}")
