import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from enum import Enum

class Type(Enum):
    CONTRIBS = 1
    REVERTS = 2

class DescryptiveAnalytics:
    def __init__(self, driver, users):
        self.type = 1
        self.driver = driver
        self.users = users

    def fetch_data(self, tx):
        params = {}
        match type:
            case 1:
                params= {
                'edge': 'r:CONTRIBUTED_TO',
                'user': 'u.total_contribs'}
            case 2:
                params = {
                'edge': 'r:REVERTED_PAGE',
                'user': 'u.total_reverts'}

        query = f"""
        MATCH (u:User)-[{params['edge']}]->(p:Page)
        WITH 
            u.username AS username, 
            {params['user']} AS total,
            SUM(CASE WHEN p.edit_protection = "extendedconfirmed" THEN r.weight ELSE 0 END) AS protected
        RETURN 
            username, 
            total, 
            protected,
            toFloat((protected)*100 / toFloat(total)) AS percent_protected
        """
        return tx.run(query).data()

    def create_scatter(self, users):
        with self.driver.session() as session:
            data = session.execute_read(self.fetch_data)

        usernames = [record['username'] for record in data]
        total = [record['total'] for record in data]
        percent_protected = [record['percent_protected'] for record in data]

        plt.figure(figsize=(10, 6))
        plt.scatter(percent_protected, total, alpha=0.5)


        for i, username in enumerate(usernames):
            if username in users:
                plt.scatter(percent_protected[i], total[i], color='red', label=f'Highlighted: {username}')
        match type:
            case 1:
                plt.title('User Contributions to EC Pages')
                plt.xlabel('% of Contributions to EC Pages')
                plt.ylabel('Total Contributions')
            case 2:
                plt.title('User Reverts to EC Pages')
                plt.xlabel('% of Reverts to EC Pages')
                plt.ylabel('Total Reverts')

        plt.grid(True)
        plt.show()

    def ecdf(self, users):
        with self.driver.session() as session:
            data = session.execute_read(self.fetch_data)

        usernames = [record['username'] for record in data]
        total = [record['total'] for record in data]
        percent_protected = [record['percent_protected'] for record in data]

        in_list_percent_protected = []
        not_in_list_percent_protected= []

        user_set = set(user['user'] for user in users)

        for i, username in enumerate(usernames):
            if username in user_set:
                in_list_percent_protected.append(percent_protected[i])
            else:
                not_in_list_percent_protected.append(percent_protected[i])

        in_list_percent_protected_contribs = np.array(in_list_percent_protected)
        not_in_list_percent_protected_contribs = np.array(not_in_list_percent_protected)

        sns.ecdfplot(data=in_list_percent_protected_contribs, color='red', label='In List')
        sns.ecdfplot(data=not_in_list_percent_protected_contribs, color='blue', label='Not in List')

        plt.xlabel('')
        plt.ylabel('ECDF')

        match type:
            case 1:
                plt.title('ECDF for % EC Contributions')
            case 2:
                plt.title('ECDF for % EC Reverts')

        plt.legend()
        plt.grid(True)
        plt.show()

    def routine(self):
        self.create_scatter(set(user['user'] for user in self.users))
        self.ecdf(self.users)

        self.type = 2

        self.create_scatter(set(user['user'] for user in self.users))
        self.ecdf_reverts(self.users)

