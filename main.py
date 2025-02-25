import contributions
import general
import reverts
import general_population
import measurements
import classify
import graphs
import export
import json
from neo4j import GraphDatabase

import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def connect_to_neo4j(uri, username, password):
    return GraphDatabase.driver(uri, auth=(username, password))

if __name__ == '__main__':

    #Load configuration
    with open("config.json", "r") as f:
        config = json.load(f)
    """
    #install packages to environment
    packages = ["neo4j", "requests", "numpy", "pandas", "seaborn", "logging", "matplotlib"]
    for package in packages:
        install(package)
    """

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

    general_population_data = config['data']['is_from_db']
    expanding_data = config['data']['is_from_json']



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
        #Todo: add grades and cutoff
        #Todo: print data to json

    if (is_graphs):
        # draw jupyter graphs
        contributions_data = general.Data()
        reverts_data = general.Data()
        ec_reverts_data = general.Data()
        ec_tag_data = general.TimeData()

        with open(f"{expanding_data}.json", "r") as f:
            data = json.load(f)
        contributions_data.insert(data['contributions'])
        reverts_data.insert(data['reverts'])
        ec_reverts_data.insert(data['ec_reverts'])
        ec_tag_data.insert(data['ec_tag'])

        with open(f"{general_population_data}.json", "r") as g:
            general = json.load(g)

        pro_palestine_data = general['pro_palestine_data']
        pro_israel_data = general['pro_israel_data']
        neutral_data = general['neutral_data']


        graph = graphs.Graphs(pro_israel_data, pro_palestine_data, neutral_data, contributions_data, reverts_data, ec_reverts_data, ec_tag_data)

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
    #add expansions with cutoff
    #add final user list


