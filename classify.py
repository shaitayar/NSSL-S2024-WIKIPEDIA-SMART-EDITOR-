class Classify:
    def __init__(self, driver, project_palestine_users, palestine_userbox, israel_userbox):
        self.driver = driver
        self.project_palestine_users = project_palestine_users
        self.palestine_userbox = palestine_userbox
        self.israel_userbox = israel_userbox

    def classify_editor(self):
        query = """
            MATCH (n:Category)<-[]-(u:User)
            WHERE ANY(keyword IN $userboxes WHERE toLower(n.name) CONTAINS keyword)
            SET u.pro_palestine = 1
        """
        with self.driver.session() as session:
            session.run(query, userboxes=self.palestine_userbox)

        query = """
            MATCH (n:Category)<-[]-(u:User)
            WHERE ANY(keyword IN $userboxes WHERE toLower(n.name) CONTAINS keyword)
            SET u.pro_israel = 1
        """
        with self.driver.session() as session:
            session.run(query, userboxes=self.israel_userbox)


    def classify_editor_by_name(self):
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User)
                WHERE u.username =~ '.*[\\u0600-\\u06FF].*'
                SET u.pro_palestine =  1
            """)

            session.run("""
                MATCH (u:User)
                WHERE u.username =~ '.*[\\u0590-\\u05FF].*'
                SET u.pro_israel = 1        
            """)

    def classify_editor_by_palestine_project(self):
        with self.driver.session() as session:
            session.run(f"""
                MATCH (u:User)
                WHERE u.username IN {self.project_palestine_users}
                SET u.pro_palestine =  1
            """)
