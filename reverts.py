import general
from general import IterationsData
import datetime
import requests

class Reverts:
    def __init__(self, driver, max_iterations, kernel_users, kernel_pages, months_start, months_end, classify):
        self.driver = driver
        self.max_iterations = max_iterations
        self.iteration = 0
        self.kernel_users = kernel_users
        self.kernel_pages = kernel_pages
        self.months_start = months_start
        self.months_end = months_end
        self.iterations_data = IterationsData()
        self.classify = classify



    def update_reverts(self):
        self.classify.classify_editor()
        self.classify.classify_editor_by_name()
        self.classify.classify_editor_by_palestine_project()

        self.calculate_data_reverts()

    def insert_users(self):
        with self.driver.session() as session:
            for user in self.kernel_users:
                session.run(
                    """
                    MERGE (u:User {username: $username})
                    SET u.revert_iteration = $iteration
                    """, username=user['user'], iteration=self.iteration)

    def is_user_data_processed(self, username):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {username: $username})-[:USERBOX]->(c:Category)
                RETURN COUNT(c) > 0 AS has_metadata
                """, username=username
            )
            return result.single()['has_metadata']

    def fetch_user_page_data(self, username):
        metadata = {
            "categories": [],
            "links": [],
            "images": []
        }
        response = requests.get(
            f"https://en.wikipedia.org/w/api.php?format=json&action=query&prop=categories|images|links&titles=User:{username}&cllimit=100&imlimit=100&pllimit=100")
        if response.status_code == 200:
            data = response.json()

            try:
                page = data.get('query', {}).get('pages', {})
                for page_id, page_info in page.items():
                    if 'categories' in page_info:
                        metadata['categories'] = [cat['title'] for cat in page_info['categories']]

                    # Extract links
                    if 'links' in page_info:
                        metadata['links'] = [link['title'] for link in page_info['links']]

                    # Extract images
                    if 'images' in page_info:
                        metadata['images'] = [img['title'] for img in page_info['images']]

            except KeyError:
                print(f"No data found for user {username}")

        return metadata

    def calculate_data_reverts(self):
        with self.driver.session() as session:
            pro_palestine_tag_condition = "n.pro_palestine IS NOT NULL"
            pro_israel_tag_condition = "n.pro_israel IS NOT NULL"

            result = session.run(f"""
            MATCH (n:User)
            WHERE {pro_palestine_tag_condition} AND n.revert_iteration = {self.iteration}
            RETURN count(n) as pro_palestine_count
            """)
            pro_palestine_count = result.single()['pro_palestine_count']

            result = session.run(f"""
            MATCH (n:User)
            WHERE {pro_israel_tag_condition} AND n.revert_iteration = {self.iteration}
            RETURN count(n) as pro_israel_count
            """)
            pro_israel_count = result.single()['pro_israel_count']

            result = session.run(f"""
            MATCH (n:User)
            WHERE n.revert_iteration = {self.iteration}
            RETURN count(n) as total_count
            """)
            total_count = result.single()['total_count']

            if self.iteration > 1:
                pro_palestine_count += self.iterations_data.num_palestinians[self.iteration - 2]
                pro_israel_count += self.iterations_data.num_israelis[self.iteration - 2]
                total_count += self.iterations_data.total_users[self.iteration - 2]

            self.iterations_data.update(pro_palestine_count, pro_israel_count, total_count)

    def fetch_user_metadata(self, username):
        metadata = {}
        response = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=users&usprop=registration&ususers={username}")
        if response.status_code == 200:
            data = response.json()
            # Extracting title from the response
            try:
                reg = data['query']['users'][0]
                metadata['registration'] = reg.get('registration')

                response2 = requests.get(
                    f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=logevents&letype=rights&leuser={username}")
                if response2.status_code == 200:
                    data2 = response2.json()
                    logevents = data2.get('query', {}).get('logevents', [])

                    for event in logevents:
                        newgroups = event.get('params', {}).get('newgroups', [])
                        if 'extendedconfirmed' in newgroups:
                            metadata['ec_timestamp'] = event.get('timestamp')
                            break

            except KeyError:
                print(f"No contributions found for user {username}")
        # else:
        #    print(f"Failed to fetch data for user {username}. Status code: {response.status_code}")

        return metadata

    def add_metadata_to_user(self, username, metadata):
        with self.driver.session() as session:
            session.run("""
                MERGE (u:User {username: $username})
                SET u.registration = $registration
            """, username=username, registration=metadata['registration'])

            if 'ec_timestamp' in metadata:
                session.run("""
                    MERGE (u:User {username: $username})
                    SET u.ec_timestamp = $ec_timestamp
                """, username=username, ec_timestamp=metadata['ec_timestamp'])

    def add_userPage_data_to_user(self, username, metadata):
        with self.driver.session() as session:
            for category in metadata['categories']:
                session.run("""
                    MERGE (u:User {username: $username})
                    MERGE (c:Category {name: $category})
                    MERGE (u)-[:USERBOX]->(c)
                """, username=username, category=category)

    def process_user_data(self, usernames, is_not_kernel):
        i = 0
        for username in usernames:
            # print(f"{i}/{len(usernames)}")
            if is_not_kernel:
                if self.is_user_data_processed(username['user']):
                    continue
            # creation_date, is_ec, ec_date, delta_ec_creation
            metadata = self.fetch_user_metadata(username['user'])
            self.add_metadata_to_user(username['user'], metadata)

            # userboxes, links, images
            userbox = self.fetch_user_page_data(username['user'])
            self.add_userPage_data_to_user(username['user'], userbox)
            i += 1

    def routine(self):
        print("\n---------- Reverts to Users ----------\n")
        # insert kernel
        self.insert_users()
        self.process_user_data(self.kernel_users, 1)
        self.update_reverts()

        # get kernel reverts
        self.iteration += 1
        self.process_user_reverts(self.kernel_users)

        curr_users = self.get_users_reverted_in_iteration(self.iteration)
        self.process_user_data(curr_users, 1)

        self.update_reverts()

        print(f"\n------ finished iteration {self.iteration}------------\n")
        print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

        while True:
            self.iteration += 1

            users_before = self.get_users_reverted_in_iteration(self.iteration - 1)

            if len(users_before) == 0:
                print("No More Users, stopping.")
                break

            self.process_user_reverts(users_before)
            users_current = self.get_users_reverted_in_iteration(self.iteration)

            if len(users_current) == 0:
                print("Not Added Users, stopping.")
                break

            self.process_user_data(users_current, 1)

            self.update_reverts()

            print(f"\n------ finished iteration {self.iteration}------------\n")

            if self.iteration >= self.max_iterations:
                print("Max iterations reached, stopping.")
                break

            print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")
            print(f"\n------ israel mean: f{self.iterations_data.il_mean(self.iteration)}")

        self.iterations_data.print_all()




class RevertsEC(Reverts):
    def __init__(self, driver, max_iterations, kernel_users, kernel_pages, months_start, months_end, classify):
        super().__init__(driver, max_iterations, kernel_users, kernel_pages, months_start, months_end, classify)

    def process_user_reverts_EC_Pages_only(self, usernames, iteration):
        i = 0
        for username in usernames:
            # print(f"{i}/{len(usernames)}")
            contributions = []
            self.fetch_user_contributions_no_limit(username["user"], contributions, months_end=7)
            reverts = self.filter_reverts(contributions)  # get only reverts from contribution
            _, reverts_count_all = self.count_reverts_by_title(reverts)
            titles = [{'title': revert['title']} for revert in reverts]
            self.get_page_protection_level_data(titles)
            ec_reverts = self.filter_ec_reverts(reverts)
            revert_user_to_title_counts, _ = self.count_reverts_by_title(ec_reverts)
            revert_user_to_user_count = self.count_reverts_by_user(ec_reverts)
            self.add_reverts_weights_title(username["user"], revert_user_to_title_counts, iteration)
            self.add_revertss_weights_user(username["user"], revert_user_to_user_count, iteration)
            self.add_total_reverts_weight(username["user"], reverts_count_all)
            i += 1

    def routine(self):
        print("\n---------- EC Reverts to Users ----------\n")
        # insert kernel
        self.insert_users()
        self.process_user_data(self.kernel_users, 0)
        self.update_reverts()

        print(f"\n------ finished iteration {self.iteration}------------\n")
        print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

        # get kernel reverts
        self.iteration += 1
        self.process_user_reverts_EC_Pages_only(self.kernel_users)

        curr_users = self.get_users_reverted_in_iteration(self.iteration)
        self.process_user_data(curr_users, 1)

        self.update_reverts()

        print(f"\n------ finished iteration {self.iteration}------------\n")
        print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

        while True:
            self.iteration += 1

            users_before = self.get_users_reverted_in_iteration(self.iteration - 1)

            if len(users_before) == 0:
                print("No More Users, stopping.")
                break

            self.process_user_reverts_EC_Pages_only(users_before)
            users_current = self.get_users_reverted_in_iteration(self.iteration)

            if len(users_current) == 0:
                print("Not Added Users, stopping.")
                break

            self.process_user_data(users_current, 1)

            self.update_reverts()

            print(f"\n------ finished iteration {self.iteration}------------\n")

            if self.iteration >= self.max_iterations:
                print("Max iterations reached, stopping.")
                break

            print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")
            print(f"\n------ israel mean: f{self.iterations_data.il_mean(self.iteration)}")

        self.iterations_data.print_all()
