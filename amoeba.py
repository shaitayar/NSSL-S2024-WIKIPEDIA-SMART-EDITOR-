import export
import pandas as pd


class Amoeba:
    def __init__(self, driver, output_file= "users_to_amoeba"):
        self.driver = driver
        self.output_file = output_file + ".csv"

    def export_users_to_amoeba(self):
        query = """
        MATCH (u:User) 
        WHERE u.edit_iteration = 1 OR u.revert_iteration=2
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
            result = session.run(query)
            records = result.data()
            df = pd.DataFrame(records)

            df.to_csv(self.output_file, index=False)

            print(f"Data successfully exported to {self.output_file}")