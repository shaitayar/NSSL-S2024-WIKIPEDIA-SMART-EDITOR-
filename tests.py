import os
import unittest
import general_population
import classify
import export
import json
import measurements
from neo4j import GraphDatabase

import subprocess
import sys

def connect_to_neo4j(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))


uri = "bolt://localhost:7687"
username = "neo4j"
password = "87654321"


#test if all measurements are correct
class TestMeasurements(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = connect_to_neo4j(uri, username, password)
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.kernel_users = config['kernel']['users']
        self.measurement = measurements.DescryptiveAnalytics(self.driver, self.kernel_users)


#test if general population stats are correct
class TestGeneralPopulation(unittest.TestCase):
    def setUp(self) -> None:
        self.driver = connect_to_neo4j(uri, username, password)
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.kernel_users = config['kernel']['users']
        self.kernel_pages = config['kernel']['pages']
        self.months_start = config['duration']['months_start']
        self.days = config['duration']['days_for_recent_changes']
        self.project_palestine_users = config['wikiProject']['palestine']
        self.project_israel_users = config['wikiProject']['israel']
        self.palestine_userbox = config['userboxes']['pro_palestine']
        self.israel_userbox = config['userboxes']['pro_israel']
        self.folderName = config['folder']
        self.classify = classify.Classify(self.driver, self.project_palestine_users, self.project_israel_users, self.palestine_userbox, self.israel_userbox)
        self.general_population = general_population.GeneralPopulation(self.driver, self.kernel_users, self.kernel_pages, self.months_start, self.days, self.classify)


    def test_export_import(self):
        self.general_population.general_population_graph_data()
        ex = export.Export()
        ex.export_to_json(self.general_population.time_data.to_dict(), "general_population_total")

        filepath = os.path.join(ex.folder, ex.fname)

        with open(filepath, "r") as g:
            general = json.load(g)

        pro_palestine_data = general.get('pro_palestine_data', [])
        pro_israel_data = general.get('pro_israel_data', [])
        neutral_data = general.get('neutral_data', [])
        time_intervals = general.get('time', [])
        self.assertNotEqual(time_intervals, self.general_population.time_data.time)
        self.assertNotEqual(pro_palestine_data, self.general_population.time_data.pro_palestine)
        self.assertNotEqual(pro_israel_data, self.general_population.time_data.pro_israel)
        self.assertNotEqual(neutral_data, self.general_population.time_data.total)

        self.driver.close()

    def test_routine(self):
        #self.general_population.routine()
        pass

#test if expansions data is correct
class TestExpansions(unittest.TestCase):
    pass

#test if data imported correctly
class TestGraphs(unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()