import amoeba
import general
import pandas as pd
from datetime import datetime


class Grades:
    def __init__(self, driver, grades, prune):
        self.driver = driver
        self.grade1 = grades[1]
        self.grade2 = grades[2]
        self.grade3 = grades[3]
        self.prune = prune

    def calculate_months_difference(self, start_date, end_date):
        return (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)

    def assignGrade(self, user_data):
        total_contribs = user_data.total_contribs
        protected_contribs = user_data.protected_contribs

        g1 = 0
        g2 = 0
        g3 = 0

        if total_contribs != 0 and protected_contribs != 0:
            g1 = (protected_contribs/total_contribs)*self.grade1

        if user_data.registration is not None and user_data.ec_timestamp is not None:
            registration_data = datetime.strptime(user_data.registration, '%Y-%m-%dT%H:%M:%SZ')
            ec_timestamp = datetime.strptime(user_data.ec_timestamp, '%Y-%m-%dT%H:%M:%SZ')

            months_until_ec = self.calculate_months_difference(registration_data, ec_timestamp)
            g2 = (1/(1+months_until_ec)) * self.grade2

        if user_data.total_reverts != 0 and user_data.protected_reverts != 0:
            g3 = (user_data.protected_reverts/user_data.total_reverts)*self.grade3

        return g1+g2+g3

    def get_users(self, contrib_iteration, revert_iteration):
        query = """
         MATCH (u:User) 
         WHERE u.edit_iteration = $contrib_iteration OR u.revert_iteration=$revert_iteration
         OPTIONAL MATCH (u)-[r:CONTRIBUTED_TO]->(p:Page)
         OPTIONAL MATCH (u)-[r2:REVERTED_PAGE]->(p2:Page)
         WITH 
             u.username AS username,
             u.registration AS registration,
             u.ec_timestamp AS ec_timestamp,
             u.edit_iteration AS edit_iteration,
             u.revert_iteration AS revert_iteration,
             u.total_contribs AS total_contribs,
             u.total_reverts AS total_reverts,
             u.pro_palestine AS pro_palestine,
             u.pro_israel AS pro_israel,
             SUM(CASE WHEN p.edit_protection = "extendedconfirmed" THEN r.weight ELSE 0 END) AS protected_contribs,
             SUM(CASE WHEN p2.edit_protection = "extendedconfirmed" THEN r2.weight ELSE 0 END) AS protected_reverts
         RETURN 
             username, edit_iteration, revert_iteration, protected_contribs, protected_reverts, total_contribs, total_reverts, 
             registration, ec_timestamp, pro_palestine, pro_israel
         """

        with self.driver.session() as session:
            result = session.run(query, contrib_iteration=contrib_iteration, revert_iteration=revert_iteration)
            records = result.data()
            return pd.DataFrame(records)

    def insert_grade(self, users_data):
        with self.driver.session() as session:
            for user in users_data:
                session.run(
                    """
                    MERGE (u:User {username: $username})
                    SET u.grade = $grade, u.is_pruned = $is_pruned
                    """, username=user['username'], grade=user['grade'], is_pruned = user['grade']<self.prune)



    def routine(self, contrib_iteration, revert_iteration):
        users_data = self.get_users(contrib_iteration, revert_iteration)
        users_data['grade'] = users_data.apply(lambda row: self.assignGrade(row), axis='columns')
        self.insert_grade(users_data)
