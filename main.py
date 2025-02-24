import contributions
import general
import reverts
import general_population
import measurements
import classify
import graphs

import json

from neo4j import GraphDatabase


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
    days =config['duration']['days_for_recent_changes']

    is_measurement = config['operation']
    is_general_population = config['is_general_population']
    is_expansions = config['is_expansions']
    is_graphs = config['is_graphs']

    graph_general_population_hour = config['graphs']['general_population_hour']
    graph_general_population_15min = config['graphs']['general_population_15min']
    graph_general_population_ec_tag = config['graphs']['general_population_ec_tag']
    graph_contributions = config['graphs']['contributions']
    graph_reverts = config['graphs']['reverts']
    graph_ec_reverts = config['graphs']['ec_reverts']
    graph_ec_tag = config['graphs']['ec_tag']

    project_palestine_users = config['wikiProject']['palestine']
    palestine_userbox = config['userboxes']['pro_palestine']
    israel_userbox = config['userboxes']['pro_israel']

    data_from_db = config['data']['is_from_db']
    data_from_csv = config['data']['is_from_csv']


    if (is_measurement):
        config_neo = config['neo4j']['measurements']
        driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
        # 1 expansion then measurements
        contribution = contributions.Contributions(driver, 1, kernel_users, kernel_pages, months_start, months_end, classify)
        revert = reverts.RevertsEC(driver, 1, kernel_users, kernel_pages, months_start, months_end, classify)
        measurement = measurements.DescryptiveAnalytics(driver, kernel_users)
        measurement.routine()


    if (is_general_population):
        config_neo = config['neo4j']['general_population']
        driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
        classify = classify.Classify(driver, project_palestine_users, palestine_userbox, israel_userbox)
        general_population = general_population.GeneralPopulation(driver, kernel_users, kernel_pages, months_start, days, classify)
        general_population.routine()


    if (is_expansions):
        config_neo = config['neo4j']['expansions']
        driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])
        classify = classify.Classify(driver, project_palestine_users, palestine_userbox, israel_userbox)
        contribution = contributions.Contributions(driver, max_iterations_contribs, kernel_users, kernel_pages, months_start, months_end, classify)
        revert = reverts.RevertsEC(driver, max_iterations_reverts, kernel_users, kernel_pages, months_start, months_end, classify)

    if (is_graphs):
        # draw jupyter graphs
        contributions_data = []
        reverts_data = []
        ec_reverts_data = []
        ec_tag_data = []

        if (data_from_db):
            config_neo = config['neo4j']['project']
            driver = connect_to_neo4j(config_neo['uri'], config_neo['username'], config_neo['password'])

        if(data_from_csv):
            with open("data.csv", "r") as f:
                data = json.load(f)
            contributions_data = data['contributions']
            reverts_data = data['reverts']
            ec_reverts_data = data['ec_reverts']
            ec_tag_data = data['ec_tag']


        graph = graphs.Graphs(contributions_data, reverts_data, ec_reverts_data, ec_tag_data, driver)

        #general population
        if(graph_general_population_hour or graph_general_population_15min or graph_general_population_ec_tag):
            if(graph_general_population_hour):
                graph.general_population_graph_hourly()
            if(graph_general_population_15min):
                graph.general_population_graph_15min()
            if(graph_general_population_ec_tag):
                graph.general_population_graph_ec_tag()

        #expansions
        if(graph_contributions or graph_reverts or graph_ec_reverts or graph_ec_tag):
            if(graph_contributions):
                graph.calc_and_plot_ec_contribs()
            if(graph_reverts):
                graph.calc_and_plot_reverts()
            if(graph_ec_reverts):
                graph.calc_and_plot_ec_reverts()
            if(graph_ec_tag):
                graph.calc_and_plot_ec_tag()






    #extract data to output file
    #add jpyter graphs V
    #amoeba

