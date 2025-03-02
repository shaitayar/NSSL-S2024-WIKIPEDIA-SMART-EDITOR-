import general
from general import IterationsData
import datetime
import requests
import re

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

    def fetch_user_contributions_no_limit(self, username, all_contributions):
        # cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days)
        # print(f"{cutoff_date}")
        end_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.months_end * 30)
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.months_start * 30)

        uccontinue = None
        while True:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=usercontribs&ucstart={start_date}&ucend={end_date}&format=json&uclimit=500&ucuser={username}"
            if uccontinue:
                url += f"&uccontinue={uccontinue}"

            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()

                try:
                    contributions = data['query']['usercontribs']
                    if contributions:
                        for contrib in contributions:
                            title = contrib.get('title')
                            timestamp = contrib.get('timestamp')
                            comment = contrib.get('comment', '')
                            _comment = comment.lower()
                            revert_keywords = ['reverted', 'undid', 'rollback']
                            is_revert = any(keyword in _comment for keyword in revert_keywords)

                            if title:
                                all_contributions.append(
                                    {
                                        "user": username,
                                        "title": title,
                                        "timestamp": timestamp,
                                        "is_revert": is_revert,
                                        "comment": comment
                                    })

                    if 'continue' in data:
                        uccontinue = data['continue']['uccontinue']
                    else:  # No more pages to fetch
                        break
                except KeyError:
                    # print(f"No contributions found for user {username}")
                    break
            else:
                # print(f"Failed to fetch data for user {username}. Status code: {response.status_code}")
                break

    def filter_reverts(self, contributions):
        reverts = [contrib for contrib in contributions if contrib.get('is_revert')]
        return reverts

    def add_reverts_weights_title(self, user, title_counts):
        with self.driver.session() as session:
            for title, count in title_counts.items():
                result = session.run(
                    """
                    MATCH (p:Page {title: $title})
                    RETURN p.revert_iteration AS iteration
                    """, title=title)

                existing_iteration = result.single()

                if not existing_iteration or existing_iteration['iteration'] is None:
                    session.run(
                        """
                        MATCH (p:Page {title: $title})
                        SET p.revert_iteration = $iteration
                        """, title=title, iteration=self.iteration)
                    # print(f"Iteration for {title} set to {iteration}")

                session.run(
                    """
                    MERGE (u:User {username: $username})
                    MERGE (p:Page {title: $title})
                    MERGE (u)-[r:REVERTED_PAGE]->(p)
                    SET r.weight = $count
                    """, username=user, title=title, count=count)

                # print(f"{user} -REVERTED_PAGE:{count}-> {title} inserted to Neo4j")

    def is_user_processed_reverts(self, username):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {username: $username}) 
                Where u.revert_iteration is not NULL
                RETURN u
                """,
                username=username
            )
            return result.single() is not None

    def add_reverts_weights_user(self, user, user_counts):
        with self.driver.session() as session:
            for user2, count in user_counts.items():
                if not self.is_user_processed_reverts(user2):
                    session.run(
                        """
                        MERGE (u:User {username: $username})
                        MERGE (u2:User {username: $username2})
                        MERGE (u)-[r:REVERTED_USER]->(u2)
                        SET r.weight = $count
                        SET u2.revert_iteration = $iteration
                        """, username=user, username2=user2, count=count, iteration=self.iteration)
                else:
                    session.run(
                        """
                        MERGE (u:User {username: $username})
                        MERGE (u2:User {username: $username2})
                        MERGE (u)-[r:REVERTED_USER]->(u2)
                        SET r.weight = $count
                        """, username=user, username2=user2, count=count)

    def count_reverts_by_title(self, reverts):
        title_counts = {}
        count_all = 0
        for revert in reverts:
            title = revert['title']
            if title not in title_counts:
                title_counts[title] = 0
            title_counts[title] += 1
            count_all += 1
        return title_counts, count_all

    def count_reverts_by_user(self, reverts):
        pattern = r'\[\[Special:Contributions/([^|\]]+)\|'
        user_counts = {}
        for revert in reverts:
            match = re.search(pattern, revert['comment'])
            if match:
                user = match.group(1)

                if user not in user_counts:
                    user_counts[user] = 0
                user_counts[user] += 1
        return user_counts

    def add_total_reverts_weight(self, user, total_count):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {username: $username})
                SET u.total_reverts = $count
                """, username=user, count=total_count)
            # print(f"{user}, total_reverts: {total_count} inserted to Neo4j")


    def process_user_reverts(self, usernames):
        i = 0
        for username in usernames:
            # print(f"{i}/{len(usernames)}")
            contributions = []
            self.fetch_user_contributions_no_limit(username["user"], contributions)
            reverts = self.filter_reverts(contributions)  # get only reverts from contribution
            revert_user_to_title_counts, reverts_count_all = self.count_reverts_by_title(reverts)
            revert_user_to_user_count = self.count_reverts_by_user(reverts)
            self.add_reverts_weights_title(username["user"], revert_user_to_title_counts)
            self.add_reverts_weights_user(username["user"], revert_user_to_user_count)
            self.add_total_reverts_weight(username["user"], reverts_count_all)
            i += 1

    def get_users_reverted_in_iteration(self, iteration):
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (n:User) 
                WHERE n.revert_iteration = $iteration
                RETURN n.username AS user
                """, iteration=iteration
            )
            return result.data()

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

    def add_metadata_to_node(self, page):
        with self.driver.session() as session:
            query = """
            MERGE (p:Page {title: $title})
            """

            set_clauses = []

            if page['protection'] != "no protection":
                for protection in page['protection']:
                    protection_type = protection.get('type')
                    protection_level = protection.get('level')

                    if protection_type == 'edit':
                        set_clauses.append("p.edit_protection = $edit_protection")
                    elif protection_type == 'move':
                        set_clauses.append("p.move_protection = $move_protection")

                if set_clauses:
                    query += " SET " + ", ".join(set_clauses)

                session.run(query,
                            title=page.get('title'),
                            edit_protection=next((p['level'] for p in page['protection'] if p['type'] == 'edit'), None),
                            move_protection=next((p['level'] for p in page['protection'] if p['type'] == 'move'), None)
                            )

            else:
                query += " SET p.edit_protection = 'no protection'"
                session.run(query, title=page.get('title'))

            if 'protection' in page and page['protection'] != "no protection":
                e = next((p['level'] for p in page['protection'] if p['type'] == 'edit'), None)
                m = next((p['level'] for p in page['protection'] if p['type'] == 'move'), None)
                # print(f"Page Title: {page.get('title')}, Edit Protection: {e}, Move Protection: {m} inserted into Neo4j")
            # else:
            # print(f"Page Title: {page.get('title')} inserted into Neo4j without protection")

    def get_page_protection_level_data(self, pages):
        i = 0
        for page in pages:
            i += 1
            # print(f"{i}/{len(pages)}")
            resp = requests.get(
                "https://en.wikipedia.org/w/api.php?action=query&prop=info&format=json&inprop=protection&titles=" +
                page[
                    'title'])

            if resp.status_code == 200:
                data = resp.json()
                try:
                    p = data.get('query', {}).get('pages', {})
                    for page_id, page_info in p.items():
                        protection = page_info.get('protection', [])
                        if protection:
                            title = page_info.get('title')
                            if title:
                                p = {
                                    "title": title,
                                    "protection": protection
                                }
                                # print(f"Page: {title}, Protection: {protection}")
                                self.add_metadata_to_node(p)
                        else:
                            title = page_info.get('title')
                            p = {
                                "title": title,
                                "protection": "no protection"
                            }
                            # print(f"Page: {title}, Protection: no protection")
                            self.add_metadata_to_node(p)

                except KeyError:
                    print(f"No protection level found for page {page}")
            # else:
            #    print(f"Failed to fetch data for page {page}. Status code: {resp.status_code}")

    def filter_ec_reverts(self, reverts):
        titles = [revert['title'] for revert in reverts]
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Page)
                WHERE p.title IN $titles AND p.edit_protection = 'extendedconfirmed'
                RETURN p.title
                """,
                titles=titles
            )
            ec_titles = {record['p.title'] for record in result}

        ec_reverts = [revert for revert in reverts if revert['title'] in ec_titles]

        return ec_reverts

    def process_user_reverts_EC_Pages_only(self, usernames):
        i = 0
        for username in usernames:
            # print(f"{i}/{len(usernames)}")
            contributions = []
            self.fetch_user_contributions_no_limit(username["user"], contributions)
            reverts = self.filter_reverts(contributions)  # get only reverts from contribution
            _, reverts_count_all = self.count_reverts_by_title(reverts)
            titles = [{'title': revert['title']} for revert in reverts]
            self.get_page_protection_level_data(titles)
            ec_reverts = self.filter_ec_reverts(reverts)
            revert_user_to_title_counts, _ = self.count_reverts_by_title(ec_reverts)
            revert_user_to_user_count = self.count_reverts_by_user(ec_reverts)
            self.add_reverts_weights_title(username["user"], revert_user_to_title_counts)
            self.add_reverts_weights_user(username["user"], revert_user_to_user_count)
            self.add_total_reverts_weight(username["user"], reverts_count_all)
            i += 1



    def routine_one(self):
        #print("\n---------- EC Reverts to Users ----------\n")
        # insert kernel
        if self.iteration == 0:
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

        else:
            users_before = self.get_users_reverted_in_iteration(self.iteration - 1)

            if len(users_before) == 0:
                print("No More Users, stopping.")
                return

            self.process_user_reverts_EC_Pages_only(users_before)
            users_current = self.get_users_reverted_in_iteration(self.iteration)

            if len(users_current) == 0:
                print("Not Added Users, stopping.")
                return

            self.process_user_data(users_current, 1)

            self.update_reverts()

            print(f"\n------ finished iteration {self.iteration}------------\n")

            print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")
            print(f"\n------ israel mean: f{self.iterations_data.il_mean(self.iteration)}")

            if self.iteration >= self.max_iterations:
                print("Max iterations reached, stopping.")


    def routine_all(self):
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

        #self.iterations_data.print_all()
