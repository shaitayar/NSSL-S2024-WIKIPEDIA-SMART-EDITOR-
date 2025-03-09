from general import IterationsData
import datetime
import requests


class Contributions:
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

    def calculate_data(self, is_prune):
        with self.driver.session() as session:
            iteration_tag_condition = "n.edit_iteration IS NOT NULL"

            pro_palestine_tag_condition = "n.pro_palestine IS NOT NULL"
            pro_israel_tag_condition = "n.pro_israel IS NOT NULL"
            prune_condition = "n.is_prune = false"

            if is_prune:
                iteration_tag_condition += f" AND {prune_condition}"

            result = session.run(f"""
            MATCH (n:User)
            WHERE {pro_palestine_tag_condition} AND {iteration_tag_condition}
            RETURN count(n) as pro_palestine_count
            """, pro_palestine_tag_condition=pro_palestine_tag_condition,
                                 iteration_tag_condition=iteration_tag_condition)
            pro_palestine_count = result.single()['pro_palestine_count']

            result = session.run(f"""
            MATCH (n:User)
            WHERE {pro_israel_tag_condition} AND {iteration_tag_condition}
            RETURN count(n) as pro_israel_count
            """, pro_israel_tag_condition=pro_israel_tag_condition, iteration_tag_condition=iteration_tag_condition)
            pro_israel_count = result.single()['pro_israel_count']

            result = session.run(f"""
            MATCH (n:User)
            WHERE {iteration_tag_condition}
            RETURN count(n) as total_count
            """, iteration_tag_condition=iteration_tag_condition)
            total_count = result.single()['total_count']

            self.iterations_data.update(pro_palestine_count, pro_israel_count, total_count)


    def update(self, is_grade = False):
        self.classify.classify_editor()
        self.classify.classify_editor_by_name()
        self.classify.classify_editor_by_palestine_project()
        self.calculate_data(is_grade)

    def remove_duplicates_pages(self, arr):
        seen_titles = set()
        unique_dicts = []
        for d in arr:
            title = d['title']
            if title not in seen_titles:
                seen_titles.add(title)
                unique_dicts.append(d)
        return unique_dicts

    def remove_duplicates(self, arr):
        seen_names = set()
        unique_dicts = []
        for d in arr:
            name = d['user']
            if name not in seen_names:
                seen_names.add(name)
                unique_dicts.append(d)
        return unique_dicts

    def get_all_ec_pages_iter(self, iteration):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Page)
                WHERE p.edit_protection = 'extendedconfirmed'
                AND p.edit_iteration = $iteration
                RETURN p.title AS title
                """, iteration= iteration
            )
            return result.data()

    def get_all_pages_iter(self):
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (p:Page)
                WHERE p.edit_iteration = $iteration
                RETURN p.title AS title
                """, iteration= self.iteration
            )
            return result.data()

    def add_total_contribs_weight(self, user, total_count):
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {username: $username})
                SET u.total_contribs = $count
                SET u.edit_iteration = $iteration
                """, username=user, count=total_count, iteration=self.iteration)
            # print(f"{user}, total_contribs: {total_count} inserted to Neo4j")

    def pages_to_users_no_limit(self, pages, all_users):
        # cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)
        end_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.months_end * 30)
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.months_start * 30)

        for page in pages:
            rccontinue = None
            while True:

                url = f"https://en.wikipedia.org/w/api.php?action=query&prop=revisions&rvstart={start_date}&rvend={end_date}&rvlimit=500&format=json&titles={page['title']}"
                if rccontinue:
                    url += f"&rccontinue={rccontinue}"


                resp = requests.get(url)

                if resp.status_code == 200:
                    data = resp.json()

                    try:
                        p = data.get('query', {}).get('pages', {})
                        for page_id, page_info in p.items():
                            contributors = page_info.get('revisions', [])
                            if contributors:
                                for contrib in contributors:
                                    name = contrib.get('user')
                                    timestamp_str = contrib.get('timestamp')
                                    if name and timestamp_str:
                                        timestamp = datetime.datetime.strptime(contrib['timestamp'],
                                                                               '%Y-%m-%dT%H:%M:%SZ')

                                        all_users.append(
                                            {
                                                "user": name,
                                                "title": page['title']
                                            }
                                        )

                        if 'continue' in data:
                            rccontinue = data['continue']['rccontinue']
                        else:
                            break
                    except KeyError:
                        # print(f"No contributions found for page {page['title']}")
                        break
                else:
                    # print(f"Failed to fetch data for page {page['title']}. Status code: {resp.status_code}")
                    break

    def add_contribs_weights(self, user, title_counts):
        with self.driver.session() as session:
            for title, count in title_counts.items():
                if count > 1:
                    result = session.run(
                        """
                        MATCH (p:Page {title: $title})
                        RETURN p.edit_iteration AS iteration
                        """, title=title)

                    existing_iteration = result.single()

                    if not existing_iteration or existing_iteration['iteration'] is None:
                        # If no iteration exists, set it
                        session.run(
                            """
                            MATCH (p:Page {title: $title})
                            SET p.edit_iteration = $iteration
                            """, title=title, iteration=self.iteration)
                        # print(f"Iteration for {title} set to {iteration}")

                    session.run(
                        """
                        MERGE (u:User {username: $username})
                        MERGE (p:Page {title: $title})
                        MERGE (u)-[r:CONTRIBUTED_TO]->(p)
                        SET r.weight = $count
                        """, username=user, title=title, count=count)

                    # print(f"{user} -CONTRIBUTED_TO:{count}-> {title} inserted to Neo4j")


    def add_userPage_data_to_user(self, username, metadata):
        with self.driver.session() as session:
            for category in metadata['categories']:
                session.run("""
                    MERGE (u:User {username: $username})
                    MERGE (c:Category {name: $category})
                    MERGE (u)-[:USERBOX]->(c)
                """, username=username, category=category)

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

    def fetch_user_metadata(self, username):
        metadata = {}
        response = requests.get(
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=users&usprop=registration&ususers={username}")
        if response.status_code == 200:
            data = response.json()
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

        return metadata

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
        # else:
        #    print(f"Failed to fetch data for user {username}. Status code: {response.status_code}")

        return metadata

    def process_user_data(self, usernames):
        i = 0
        for username in usernames:
            # print(f"{i}/{len(usernames)}")
            if self.iteration != 0:
                if self.is_user_data_processed(username['user']):
                    continue
            # creation_date, is_ec, ec_date, delta_ec_creation
            metadata = self.fetch_user_metadata(username['user'])
            self.add_metadata_to_user(username['user'], metadata)

            # userboxes, links, images
            userbox = self.fetch_user_page_data(username['user'])
            self.add_userPage_data_to_user(username['user'], userbox)
            i += 1

    def get_all_users(self):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (n:User)
                RETURN n.username AS user
                """
            )
            return result.data()

    def count_contributions_by_title(self, contributions):
        title_counts = {}
        count_all = 0
        for contrib in contributions:
            title = contrib['title']
            if title not in title_counts:
                title_counts[title] = 0
            title_counts[title] += 1
            count_all += 1
        return title_counts, count_all

    def is_user_processed(self, username):
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {username: $username}) 
                WHERE u.edit_iteration is not NULL
                RETURN u
                """,
                username=username
            )
            return result.single() is not None

    def add_metadata_to_node(self, page):
        with self.driver.session() as session:
            query = """
            MERGE (p:Page {title: $title})
            """

            set_clauses = []

            if page['protection'] != "no protection":
                # Check the type of protection
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

    def fetch_user_contributions_no_limit(self, username, all_contributions):
        end_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.months_end * 30)
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.months_start * 30)

        uccontinue = None
        while True:
            #add uccontinue if it exists
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
                    else:  # no more pages to fetch
                        break
                except KeyError:
                    # print(f"No contributions found for user {username}")
                    break
            else:
                # print(f"Failed to fetch data for user {username}. Status code: {response.status_code}")
                break

    def process_user_contributions(self, usernames):
        i = 0
        for username in usernames:
            # print(f"{i}/{len(usernames)}")
            if self.iteration != 0:
                if self.is_user_processed(username["user"]):
                    continue
            contributions = []
            self.fetch_user_contributions_no_limit(username["user"], contributions)
            title_counts, count_all = self.count_contributions_by_title(contributions)
            self.add_contribs_weights(username["user"], title_counts)
            self.add_total_contribs_weight(username["user"], count_all)
            i += 1

    def routine_all(self):
        self.process_user_contributions(self.kernel_users)

        all_users = []
        all_users = self.get_all_users()
        self.process_user_data(all_users)

        # update iterations data
        self.update()

        all_pages = self.get_all_pages_iter()
        temp2 = self.remove_duplicates_pages(all_pages)
        self.get_page_protection_level_data(temp2)
        protected_pages = self.get_all_ec_pages_iter(self.iteration)

        last_iterate_pages = protected_pages
        print(f"\n------ finished iteration {self.iteration}------------\n")
        print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

        while True:
            self.iteration += 1
            users2 = []

            if self.iteration == 1:
                self.pages_to_users_no_limit(last_iterate_pages + self.kernel_pages, users2)

            else:
                self.pages_to_users_no_limit(last_iterate_pages, users2)

            temp = self.remove_duplicates(users2)

            if len(temp) == 0:
                print("No More Users, stopping.")
                break

            self.process_user_contributions(temp)

            self.process_user_data(temp)

            all_pages = self.get_all_pages_iter()  # get all pages
            self.get_page_protection_level_data(all_pages)  # add tag ec or not ec
            protected_pages = self.get_all_ec_pages_iter(self.iteration)  # get only ec

            if len(protected_pages) == 0:
                print("No More EC Pages, stopping.")
                break

            last_iterate_pages = protected_pages
            self.update()

            print(f"\n------ finished iteration {self.iteration}------------\n")

            if self.iteration >= self.max_iterations:
                print("Max iterations reached, stopping.")
                break

            print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

        #self.iterations_data.print_all()

    def routine_one(self):
        if self.iteration == 0:
            self.process_user_contributions(self.kernel_users)

            all_users = []
            all_users = self.get_all_users()

            self.process_user_data(all_users)

            # update iterations data
            self.update()

            all_pages = self.get_all_pages_iter()
            temp2 = self.remove_duplicates_pages(all_pages)
            self.get_page_protection_level_data(temp2)

            print(f"\n------ finished iteration {self.iteration}------------\n")
            print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

        else:
            users2 = []
            last_iterate_pages = self.get_all_ec_pages_iter(self.iteration-1)

            if self.iteration == 1:
                self.pages_to_users_no_limit(last_iterate_pages + self.kernel_pages, users2)
            else:
                self.pages_to_users_no_limit(last_iterate_pages, users2)

            temp = self.remove_duplicates(users2)

            if len(temp) == 0:
                print("No More Users, stopping.")
                return

            self.process_user_contributions(temp)

            self.process_user_data(temp)

            all_pages = self.get_all_pages_iter()  # get all pages
            self.get_page_protection_level_data(all_pages)  # add tag ec or not ec
            protected_pages = self.get_all_ec_pages_iter(self.iteration)  # get only ec

            if len(protected_pages) == 0:
                print("No More EC Pages, stopping.")
                return

            self.update(True)

            print(f"\n------ finished iteration {self.iteration}------------\n")
            print(f"\n------ palestine mean: f{self.iterations_data.ps_mean(self.iteration)}")

            if self.iteration >= self.max_iterations:
                print("Max iterations reached, stopping.")
