#****************************************************
# Purpose:  classify raw data into groups:
#           pro_palestine, pro_israel and neutral
# Classes:  Classify
#****************************************************

class Classify:
    """
    Inputs:   driver: the driver to connect neo4j
              project_palestine_users: contributors in the project will be classified as pro_palestine
              project_israel_users: same, but classified as pro_israel
              palestine_userbox: users that have userbox from that list will be classified as pro_palestine
              israel_userbox: same, but classified as pro_israel
    Comment:  Should call the relevant function
    """

    def __init__(self, driver, project_palestine_users, project_israel_users, palestine_userbox, israel_userbox):
        self.driver = driver
        self.project_palestine_users = project_palestine_users
        self.palestine_userbox = palestine_userbox
        self.israel_userbox = israel_userbox
        self.project_israel_users = project_israel_users

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

    def classify_editor_by_israel_project(self):
        with self.driver.session() as session:
            session.run(f"""
                MATCH (u:User)
                WHERE u.username IN {self.project_israel_users}
                SET u.pro_israel =  1
            """)
