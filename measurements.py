#****************************************************
# Purpose:  Draw the graphs for measuring 1 iteration:
#           ECDF and Scatter.
# Classes:  DescryptiveAnalytics
#****************************************************
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from enum import Enum
import general
import export

class Type(Enum):
    CONTRIBS = 1
    REVERTS = 2

class DescryptiveAnalytics:
    def __init__(self, driver, users):
        self.types = Type.CONTRIBS
        self.driver = driver
        self.users = users
        self.data = general.MeasurementsData()

    def fetch_data(self, tx):
        params = {}
        if self.types == Type.CONTRIBS:
            params= {
            'edge': 'r:CONTRIBUTED_TO',
            'user': 'u.total_contribs'}
        elif self.types == Type.REVERTS:
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

        if self.types == Type.CONTRIBS:
            self.data.contribs_usernames = usernames
            self.data.contribs_total = total
            self.data.contribs_percent_protected = percent_protected

        elif self.types == Type.REVERTS:
            self.data.reverts_usernames = usernames
            self.data.reverts_total = total
            self.data.reverts_percent_protected = percent_protected

        for i, username in enumerate(usernames):
            if username in users:
                plt.scatter(percent_protected[i], total[i], color='red', label=f'Highlighted: {username}')

        if self.types == Type.CONTRIBS:
            plt.title('User Contributions to EC Pages')
            plt.xlabel('% of Contributions to EC Pages')
            plt.ylabel('Total Contributions')
        elif self.types == Type.REVERTS:
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

        if self.types == Type.CONTRIBS:
            self.data.in_list_percent_protected_contribs = list(in_list_percent_protected_contribs)
            self.data.not_in_list_percent_protected_contribs = list(not_in_list_percent_protected_contribs)

        elif self.types == Type.REVERTS:
            self.data.in_list_percent_protected_reverts = list(in_list_percent_protected_contribs)
            self.data.not_in_list_percent_protected_reverts = list(not_in_list_percent_protected_contribs)


        sns.ecdfplot(data=in_list_percent_protected_contribs, color='red', label='In List')
        sns.ecdfplot(data=not_in_list_percent_protected_contribs, color='blue', label='Not in List')

        plt.xlabel('')
        plt.ylabel('ECDF')

        if self.types == Type.CONTRIBS:
            plt.title('ECDF for % EC Contributions')
        elif self.types == Type.REVERTS:
            plt.title('ECDF for % EC Reverts')

        plt.legend()
        plt.grid(True)
        plt.show()

    def routine(self):
        self.create_scatter(set(user['user'] for user in self.users))
        self.ecdf(self.users)

        self.types = Type.REVERTS

        self.create_scatter(set(user['user'] for user in self.users))
        self.ecdf(self.users)

        #export data for further use
        ex = export.Export("measurements\\analytics")
        ex.export_to_json(self.data.to_dict(), "measurements")


    def draw_graphs(self):
        im = export.Import("measurements\\analytics")
        im.import_from_json()

        self.data.insert(im.data.get('measurements', []))


        self.draw_scatter()
        self.draw_ecdf()

        self.types = Type.REVERTS

        self.draw_scatter()
        self.draw_ecdf()


    def draw_ecdf(self):
        if self.types == Type.CONTRIBS:
            in_list_percent_protected_contribs = np.array(self.data.in_list_percent_protected_contribs)
            not_in_list_percent_protected_contribs = np.array(self.data.not_in_list_percent_protected_contribs)
        elif self.types == Type.REVERTS:
            in_list_percent_protected_contribs = np.array(self.data.in_list_percent_protected_reverts)
            not_in_list_percent_protected_contribs = np.array(self.data.not_in_list_percent_protected_reverts)

        sns.ecdfplot(data=in_list_percent_protected_contribs, color='red', label='In List')
        sns.ecdfplot(data=not_in_list_percent_protected_contribs, color='blue', label='Not in List')

        plt.xlabel('')
        plt.ylabel('ECDF')

        if self.types == Type.CONTRIBS:
            plt.title('ECDF for % EC Contributions')
        elif self.types == Type.REVERTS:
            plt.title('ECDF for % EC Reverts')

        plt.legend()
        plt.grid(True)
        plt.show()

    def draw_scatter(self):
        if self.types == Type.CONTRIBS:
            usernames = self.data.contribs_usernames
            total = self.data.contribs_total
            percent_protected = self.data.contribs_percent_protected

        elif self.types == Type.REVERTS:
            usernames = self.data.reverts_usernames
            total = self.data.reverts_total
            percent_protected = self.data.reverts_percent_protected

        plt.figure(figsize=(10, 6))
        plt.scatter(percent_protected, total, alpha=0.5)

        for i, username in enumerate(usernames):
            if username in set(user['user'] for user in self.users):
                plt.scatter(percent_protected[i], total[i], color='red', label=f'Highlighted: {username}')

        if self.types == Type.CONTRIBS:
            plt.title('User Contributions to EC Pages')
            plt.xlabel('% of Contributions to EC Pages')
            plt.ylabel('Total Contributions')
        elif self.types == Type.REVERTS:
            plt.title('User Reverts to EC Pages')
            plt.xlabel('% of Reverts to EC Pages')
            plt.ylabel('Total Reverts')

        plt.grid(True)
        plt.show()