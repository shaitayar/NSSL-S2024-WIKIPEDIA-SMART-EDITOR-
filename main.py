import contributions
import general
import reverts
import general_population
import measurements
import classify
import graphs
import export
import expansion
import amoeba
import json
from neo4j import GraphDatabase
import ec_tag



def connect_to_neo4j(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))

if __name__ == '__main__':

    #Load configuration
    with open("config.json", "r") as f:
        config = json.load(f)

    #Reading from configuration file
    kernel_users = config['kernel']['users']
    kernel_pages = config['kernel']['pages']
    months_start = config['duration']['months_start']
    months_end = config['duration']['months_end']
    max_iterations_contribs = config['max_iterations']['contribs']
    max_iterations_reverts = config['max_iterations']['reverts']
    days = config['duration']['days_for_recent_changes']

    is_measurement = config['operation']['is_measurement']
    is_general_population = config['operation']['is_general_population']
    is_expansions = config['operation']['is_expansions']
    is_graphs = config['operation']['is_graphs']

    graph_general_population_hour = config['graphs']['general_population_hour']
    graph_general_population_15min = config['graphs']['general_population_15min']
    graph_general_population_ec_tag = config['graphs']['general_population_ec_tag']
    graph_contributions = config['graphs']['contributions']
    graph_reverts = config['graphs']['reverts']
    graph_ec_reverts = config['graphs']['ec_reverts']
    graph_ec_tag = config['graphs']['ec_tag']

    project_palestine_users = config['wikiProject']['palestine']
    project_israel_users = config['wikiProject']['israel']
    palestine_userbox = config['userboxes']['pro_palestine']
    israel_userbox = config['userboxes']['pro_israel']

    filename = config['graph_input_filename']

    is_expansions_with_grades = config['Amoeba_Results']['is_grade']
    grades = config['Amoeba_Results']['grades']
    prune = config['Amoeba_Results']['prune']

    export_to_amoeba = ['export_to_amoeba']

    if (is_measurement or export_to_amoeba):
        config_neo = config['neo4j']['measurements']
        driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
        # 1 expansion then measurements
        classify = classify.Classify(driver, project_palestine_users, project_israel_users, palestine_userbox, israel_userbox)

        contribution = contributions.Contributions(driver, 1, kernel_users, kernel_pages, months_start, months_end, classify)
        revert = reverts.RevertsEC(driver, 2, kernel_users, kernel_pages, months_start, months_end, classify)
        measurement = measurements.DescryptiveAnalytics(driver, kernel_users)

        contribution.routine_all()
        revert.routine_all()

        ex = export.Export('measurements')
        ex.export_to_json(contribution.iterations_data.to_dict(), "contributions")
        ex.export_to_json(revert.iterations_data.to_dict(), "ec_reverts")

        measurement.routine()

        #export data to Amoeba in Matlab
        am = amoeba.Amoeba(driver)
        am.export_users_to_amoeba()
        driver.close()

    if (is_general_population):
        config_neo = config['neo4j']['general_population']
        driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
        classify = classify.Classify(driver, project_palestine_users, project_israel_users, palestine_userbox, israel_userbox)
        general_population = general_population.GeneralPopulation(driver, months_start, days, classify)
        general_population.routine()

        ex = export.Export('general_population')
        ex.export_to_json(general_population.time_data.to_dict(), "general_population_total")
        ex.export_to_json(general_population.ec_time_data.to_dict(), "general_population_ec_tag")
        driver.close()

    if (is_expansions):
        config_neo = config['neo4j']['expansions']
        driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
        classify = classify.Classify(driver, project_palestine_users, project_israel_users, palestine_userbox, israel_userbox)
        expansion = expansion.Expansion(driver, max_iterations_contribs, max_iterations_reverts, kernel_users, kernel_pages, months_start, months_end, classify, prune, grades, is_expansions_with_grades)
        expansion.routine()
        expansion.export_final_users_to_csv()

        driver.close()

    if (is_graphs):
        if(graph_general_population_hour or graph_general_population_15min or graph_general_population_ec_tag):
            general_population_total = general.TimeData()
            general_population_ec_tag = general.TimeData()

            im = export.Import(filename)
            im.import_from_json()
            if graph_general_population_hour or graph_general_population_15min:
                try: general_population_total.insert(im.data.get('general_population_total', []))
                except: print(f"no General Population Data in {im.filepath}")

            if(graph_general_population_ec_tag):
                try: general_population_ec_tag.insert(im.data.get('general_population_ec_tag', []))
                except: print(f"no General Population EC Tag Data in {im.filepath}")

            gp_graph = graphs.GeneralPopulationGraph(graph_general_population_hour, graph_general_population_15min,
                                                     graph_general_population_ec_tag, general_population_total, general_population_ec_tag)
            gp_graph.routine()

        #expansions
        if(graph_contributions or graph_reverts or graph_ec_reverts or graph_ec_tag):
            contributions_data = general.Data()
            reverts_data = general.Data()
            ec_reverts_data = general.Data()
            ec_tag_data = general.TimeData()
            general_population_total = general.TimeData()

            im = export.Import("expansion_no_grades", filename)
            im.import_from_json()
            if graph_contributions:
                try: contributions_data.insert(im.data.get('contributions', []))
                except: print(f"no Contributions Data in {im.filepath}")
            if graph_reverts:
                try: reverts_data.insert(im.data.get('reverts', []))
                except: print(f"no Reverts Data in {im.filepath}")

            if graph_ec_reverts:
                try: ec_reverts_data.insert(im.data.get('ec_reverts', []))
                except: print(f"no EC Reverts Data in {im.filepath}")

            if graph_ec_tag:
                try: ec_tag_data.insert(im.data.get('ec_tag', []))
                except: print(f"no EC Tag Data in {im.filepath}")

            im_general = export.Import("general_population")
            im_general.import_from_json()

            general_population_total.insert(im_general.data.get('general_population_total', []))

            graph = graphs.Graphs(graph_contributions, graph_reverts, graph_ec_reverts, graph_ec_tag,
                                  contributions_data, reverts_data, ec_reverts_data, ec_tag_data, general_population_total)
            graph.routine()




