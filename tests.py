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


def connect_to_neo4j(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))


class TestGeneralStuff(unittest.TestCase):
    def setUp(self) -> None:
        self.filename = "test_file_name"

    # test if can read from a file
    def test_read_import_file(self):
        ex = export.Export(self.filename)
        ex.export_to_json("world!", "hello")

        im = export.Import(self.filename)
        im.import_from_json()
        data = im.data.get("hello", [])
        self.assertEqual(data, "world!")

    def test_export_multiple_times(self):
        ex1 = export.Export()
        ex1.export_to_json("world!", "Hello")

        ex2 = export.Export()
        ex2.export_to_json("olam!", "Shalom")

        ex3 = export.Export()
        ex3.export_to_json("mundo!", "Hola")


        im = export.Import("")
        im.import_from_json()
        data = im.data.get("Hello", [])
        self.assertEqual(data, "world!")

        data = im.data.get("Shalom", [])
        self.assertEqual(data, "olam!")

        data = im.data.get("Hola", [])
        self.assertEqual(data, "mundo!")


# test if all measurements are correct
class TestMeasurements(unittest.TestCase):
    def setUp(self) -> None:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        config_neo = config['neo4j']['measurements']
        self.kernel_users = config['kernel']['users']
        self.driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])

        self.measurement = measurements.DescryptiveAnalytics(self.driver, self.kernel_users)



# test if general population stats are correct
class TestGeneralPopulation(unittest.TestCase):
    def setUp(self) -> None:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
        config_neo = config['neo4j']['general_population']
        self.driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
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

    # test import and export
    def test_export_import_data(self):
        general_population_total = general.TimeData()
        general_population_ec_tag = general.TimeData()

        self.general_population.general_population_graph_data()
        self.general_population.general_population_ec_tag()
        ex = export.Export()
        ex.export_to_json(self.general_population.time_data.to_dict(), "general_population_total")
        ex.export_to_json(self.general_population.ec_time_data.to_dict(), "general_population_ec_tag")
        im = export.Import(self.filename)
        im.import_from_json()

        general_population_total.insert(im.data.get('general_population_total', []))
        general_population_ec_tag.insert(im.data.get('general_population_ec_tag', []))

        self.assertEqual(general_population_total.time, self.general_population.time_data.time)
        self.assertEqual(general_population_total.pro_palestine, self.general_population.time_data.pro_palestine)
        self.assertEqual(general_population_total.pro_israel, self.general_population.time_data.pro_israel)
        self.assertEqual(general_population_total.neutral, self.general_population.time_data.neutral)

        self.assertEqual(general_population_ec_tag.time, self.general_population.ec_time_data.time)
        self.assertEqual(general_population_ec_tag.pro_palestine, self.general_population.ec_time_data.pro_palestine)
        self.assertEqual(general_population_ec_tag.pro_israel, self.general_population.ec_time_data.pro_israel)
        self.assertEqual(general_population_ec_tag.neutral, self.general_population.ec_time_data.neutral)

        self.driver.close()
    #test routine
    def test_routine(self):
        pass
        self.general_population.routine()

    #test routine if neo4j is down
    def test_routine_no_neo4j(self):
        pass
        self.general_population.routine()



# test if expansions data is correct
class TestExpansions(unittest.TestCase):
    pass

# test graphs class
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
            if self.graph_general_population_hour or self.graph_general_population_15min:
                try: general_population_total.insert(im.data.get('general_population_total', []))
                except: print(f"no General Population Data in {im.filepath}")
            if(self.graph_general_population_ec_tag):
                try: general_population_ec_tag.insert(im.data.get('general_population_ec_tag', []))
                except: print(f"no General Population EC Tag Data in {im.filepath}")

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
            if self.graph_contributions:
                try: contributions_data.insert(im.data['contributions'])
                except: print(f"no Contributions Data in {im.filepath}")
            if self.graph_reverts:
                try: reverts_data.insert(im.data['reverts'])
                except: print(f"no Reverts Data in {im.filepath}")

            if self.graph_ec_reverts:
                try: ec_reverts_data.insert(im.data['ec_reverts'])
                except: print(f"no EC Reverts Data in {im.filepath}")

            if self.graph_ec_tag:
                try: ec_tag_data.insert(im.data['ec_tag'])
                except: print(f"no EC Tag Data in {im.filepath}")

            general_population_total.insert(im.data['general_population_total'])
            graph = graphs.Graphs(self.graph_contributions, self.graph_reverts, self.graph_ec_reverts, self.graph_ec_tag,
                                  contributions_data, reverts_data, ec_reverts_data, ec_tag_data,
                                  general_population_total)
            graph.routine()

    #test what happens if the user tries to plot a graph without data in the json file
    def test_graph_no_data(self):
        reverts_data = general.Data()
        im = export.Import(self.filename)
        im.import_from_json()
        if self.graph_reverts:
            try:
                reverts_data.insert(im.data['reverts'])
            except:
                print(f"no Reverts Data in {im.filepath}")
        graph = graphs.Graphs(graph_contributions=False, graph_reverts=True, graph_ec_reverts=False, graph_ec_tag=False,
                              contributions=None, reverts=reverts_data, ec_reverts=None, data_ec_tag=None,
                              general_population_data=None)
        graph.routine()

if __name__ == "__main__":
    unittest.main()