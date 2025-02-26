import os
import unittest
import general_population
import classify
import export
import json
import measurements
from neo4j import GraphDatabase
import general
import graphs

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
        self.filename = config['graph_input_filename']
        self.classify = classify.Classify(self.driver, self.project_palestine_users, self.project_israel_users, self.palestine_userbox, self.israel_userbox)
        self.general_population = general_population.GeneralPopulation(self.driver, self.kernel_users, self.kernel_pages, self.months_start, self.days, self.classify)


    def test_export_import_data(self):
        self.general_population.general_population_graph_data()
        ex = export.Export()
        ex.export_to_json(self.general_population.time_data.to_dict(), "general_population_total")

        im = export.Import(self.filename)
        im.import_from_json()

        pro_palestine_data = im.data.get('pro_palestine', [])
        pro_israel_data = im.data.get('pro_israel', [])
        neutral_data = im.data.get('neutral', [])
        time_intervals = im.data.get('time', [])
        self.assertNotEqual(time_intervals, self.general_population.time_data.time)
        self.assertNotEqual(pro_palestine_data, self.general_population.time_data.pro_palestine)
        self.assertNotEqual(pro_israel_data, self.general_population.time_data.pro_israel)
        self.assertNotEqual(neutral_data, self.general_population.time_data.neutral)

        self.driver.close()

    def test_export_import_ec_tag(self):
        pass
    def test_routine(self):
        #self.general_population.routine()
        pass

#test if expansions data is correct
class TestExpansions(unittest.TestCase):
    pass

#test if data imported correctly
class TestGraphs(unittest.TestCase):
    def setUp(self) -> None:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.graph_general_population_hour = config['graphs']['general_population_hour']
        self.graph_general_population_15min = config['graphs']['general_population_15min']
        self.graph_general_population_ec_tag = config['graphs']['general_population_ec_tag']
        self.graph_contributions = config['graphs']['contributions']
        self.graph_reverts = config['graphs']['reverts']
        self.graph_ec_reverts = config['graphs']['ec_reverts']
        self.graph_ec_tag = config['graphs']['ec_tag']
        self.filename = config['graph_input_filename']

    def test_general_population_graph(self):
        if (self.graph_general_population_hour or self.graph_general_population_15min or self.graph_general_population_ec_tag):
            general_population_total = general.TimeData()
            general_population_ec_tag = general.TimeData()

            im = export.Import(self.filename)
            im.import_from_json()
            general_population_total.insert(im.data.get('general_population_total', []))
            general_population_ec_tag.insert(im.data.get('general_population_ec_tag', []))
            gp_graph = graphs.GeneralPopulationGraph(self.graph_general_population_hour, self.graph_general_population_15min,
                                                     self.graph_general_population_ec_tag, general_population_total,
                                                     general_population_ec_tag)
            gp_graph.routine()

    def test_expansions_graph(self):
        if (self.graph_contributions or self.graph_reverts or self.graph_ec_reverts or self.graph_ec_tag):
            contributions_data = general.Data()
            reverts_data = general.Data()
            ec_reverts_data = general.Data()
            ec_tag_data = general.TimeData()
            general_population_total = general.TimeData()

            im = export.Import(self.filename)
            im.import_from_json()
            contributions_data.insert(im.data['contributions'])
            reverts_data.insert(im.data['reverts'])
            ec_reverts_data.insert(im.data['ec_reverts'])
            ec_tag_data.insert(im.data['ec_tag'])
            general_population_total.insert(im.data['general_population_total'])

            graph = graphs.Graphs(self.graph_contributions, self.graph_reverts, self.graph_ec_reverts, self.graph_ec_tag,
                                  contributions_data, reverts_data, ec_reverts_data, ec_tag_data,
                                  general_population_total)
            graph.routine()


if __name__ == "__main__":
    unittest.main()