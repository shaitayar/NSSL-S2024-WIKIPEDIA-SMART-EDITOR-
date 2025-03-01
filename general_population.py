import csv
import requests
import datetime
import general
from collections import defaultdict
import pandas as pd

class GeneralPopulation:
    def __init__(self, driver, kernel_users, kernel_pages, months_start, days, classify):
        self.driver = driver
        self.kernel_users = kernel_users
        self.kernel_pages = kernel_pages
        self.months_start = months_start
        self.days = days
        self.classify = classify

        self.time_data = general.TimeData()
        self.ec_time_data = general.TimeData()

    def routine(self):
        recent_edit_users = self.get_recent_edits()
        recent_edit_users_no_dups = self.round_to_quarter_hour(recent_edit_users)
        insert_all_to_neo4j = self.insert_all(recent_edit_users_no_dups)
        all_users = self.fetch_users_every_15_minutes()

        #csv_file = "names.csv"

        #with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        #    writer = csv.writer(file)
        #    for user in all_users:
        #        writer.writerow([user['user']])

        self.process_user_data(all_users)

        self.classify.classify_editor()
        self.classify.classify_editor_by_name()
        self.classify.classify_editor_by_palestine_project()
        self.classify.classify_editor_by_israel_project()
        self.general_population_graph_data()
        self.general_population_ec_tag()


    def general_population_graph_data(self):
        pro_israel_15min = defaultdict(int)
        pro_palestine_15min = defaultdict(int)
        neutral_15min = defaultdict(int)

        il = 0  # pro-Israel total
        pn = 0  # pro-Palestine total
        neutral_count = 0

        all_intervals = [f"{hour:02}:{minute:02}" for hour in range(24) for minute in [0, 15, 30, 45]]

        with self.driver.session() as session:
            res = session.run("""
                MATCH (u:User)
                RETURN u.username, u.pro_israel, u.pro_palestine, u.time
            """)

            for record in res:
                is_pro_israel = record.get('u.pro_israel', None)
                is_pro_palestine = record.get('u.pro_palestine', None)
                time = record.get('u.time', None)
                if time:
                    # Group based on the hour
                    if is_pro_israel is not None:
                        pro_israel_15min[time] += 1
                        il += 1
                    if is_pro_palestine is not None:
                        pro_palestine_15min[time] += 1
                        pn += 1
                    if is_pro_israel is None and is_pro_palestine is None:
                        neutral_15min[time] += 1
                        neutral_count += 1

        pro_israel_15min_array = [pro_israel_15min.get(interval, 0) for interval in all_intervals]
        pro_palestine_15min_array = [pro_palestine_15min.get(interval, 0) for interval in all_intervals]
        neutral_15min_array = [neutral_15min.get(interval, 0) for interval in all_intervals]

        self.time_data.time = all_intervals
        self.time_data.pro_palestine = pro_israel_15min_array
        self.time_data.pro_israel = pro_palestine_15min_array
        self.time_data.neutral = neutral_15min_array

    def run_query(self, months):
        query = """
        MATCH (u:User)
        WITH u,
            datetime(replace(u.registration, "Z", "")) AS regDate,
            datetime(replace(u.ec_timestamp, "Z", "")) AS ecDate
        WITH u,
        duration.between(regDate, ecDate) AS duration
        WHERE (duration.years * 12 + duration.months + duration.days/30.0) < $months
        AND (duration.years * 12 + duration.months + duration.days/30.0) >= $pre_months

        RETURN 
            SUM(CASE WHEN u.pro_palestine is not NULL THEN 1 ELSE 0 END) AS num_pro_palestine,
            SUM(CASE WHEN u.pro_israel is not NULL THEN 1 ELSE 0 END) AS num_pro_israel,
            count(u.username) AS neutral
        """

        with self.driver.session() as session:
            result = session.run(query, months=months, pre_months=months - 1)
            for record in result:
                self.ec_time_data.pro_palestine.append(record['num_pro_palestine'])
                self.ec_time_data.pro_israel.append(record['num_pro_israel'])
                self.ec_time_data.neutral.append(record['neutral'])

    def run_query_final(self):
        query = """
        MATCH (u:User)
        WITH u,
            datetime(replace(u.registration, "Z", "")) AS regDate,
            datetime(replace(u.ec_timestamp, "Z", "")) AS ecDate
        WITH u,
        duration.between(regDate, ecDate) AS duration
        WHERE (duration.years * 12 + duration.months) > 12
        RETURN 
            SUM(CASE WHEN u.pro_palestine is not NULL THEN 1 ELSE 0 END) AS num_pro_palestine,
            SUM(CASE WHEN u.pro_israel is not NULL THEN 1 ELSE 0 END) AS num_pro_israel,
            count(u.username) AS neutral
        """

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                self.ec_time_data.pro_palestine.append(record['num_pro_palestine'])
                self.ec_time_data.pro_israel.append(record['num_pro_israel'])
                # actually, this is total and not neutral but it need to fit the class
                self.ec_time_data.neutral.append(record['neutral'])

    def general_population_ec_tag(self):
        for month in range(2, 13):
            self.run_query(month)
        self.run_query_final()

    def round_to_quarter_hour(self, arr):
        rounded_dict = []
        for user in arr:
            timestamp = datetime.datetime.strptime(user['time'], '%Y-%m-%dT%H:%M:%SZ')
            minute = (timestamp.minute // 15) * 15
            rounded_time = timestamp.replace(minute=minute, second=0, microsecond=0)

            rounded_dict.append({
                'user': user['user'],
                'time': rounded_time.strftime('%H:%M')
            })

        return rounded_dict

    def insert_all(self, users):
        with self.driver.session() as session:
            for user in users:
                session.run("MERGE (u:User {username: $username, time: $time})", username=user['user'],
                            time=user['time'])

    def fetch_users_every_15_minutes(self):
        all_users = []

        for i in range(0, 24, 1):  # For 24 hours
            for j in range(0, 60, 15):  # Every 15 minutes
                time = f'{i:02}:{j:02}'

                users = self.get_users_from_neo4j(time)
                all_users.extend(users)
        return all_users

    def get_users_from_neo4j(self, time):
        with self.driver.session() as session:
            query = """
            MATCH (u:User)
            WHERE u.time = $time 
            AND NOT tolower(u.username) CONTAINS 'bot'
            AND NOT (u)-[:USERBOX]->() 
            RETURN u.username AS user, u.time AS time
            LIMIT 300
            """
            result = session.run(query, time=time)
            users = [{"user": record["user"], "time": record["time"]} for record in result]
        return users

    def get_recent_edits(self):
        end_time = datetime.datetime.utcnow()
        userlist = []

        # Loop over days days, 24 hours and 15-minute intervals
        for i in range(self.days*24):
            for j in range(0, 60, 15):
                print(f" day {i // 24 + 1} hour {i % 24}:{j}")

                start_time = end_time - datetime.timedelta(minutes=15)

                start_time_str = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
                end_time_str = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

                rccontinue_token = None
                interval_users = []
                while True:
                    url = f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=recentchanges&rcprop=user|timestamp&rclimit=500&rcstart={end_time_str}&rcend={start_time_str}"
                    if rccontinue_token:
                        url += f"&rccontinue={rccontinue_token}"

                    resp = requests.get(url)
                    if resp.status_code == 200:
                        data = resp.json()

                        try:
                            changes = data['query']['recentchanges']
                            for change in changes:
                                interval_users.append({
                                    "user": change['user'],
                                    "time": change['timestamp']
                                })
                        except KeyError:
                            print(f"No data found for recent edits")

                        if 'continue' in data:
                            rccontinue_token = data['continue']['rccontinue']
                        else:
                            break
                    else:
                        print(f"Error: {resp.status_code}")
                        break

                unique_interval_users = self.remove_duplicates(interval_users)
                userlist.extend(unique_interval_users)

                end_time = start_time
                print(len(unique_interval_users))
        return userlist

    def remove_duplicates(self, arr):
        seen_names = set()
        unique_dicts = []
        for user in arr:
            if user['user'] not in seen_names:
                seen_names.add(user['user'])

                unique_dicts.append({
                    'user': user['user'],
                    'time': user['time']
                })

        return unique_dicts

    def process_user_data(self, users):
        user_data = []
        i = 0
        for user in users:
            print(f"{i}/{len(users)}")
            # creation_date, is_ec, ec_date, delta_ec_creation
            metadata = self.fetch_user_metadata(user['user'])

            # userboxes, links, images
            userbox = self.fetch_user_page_data(user['user'])

            user_data.append(
                {
                    "name": user['user'],
                    "time": user['time'],
                    "registration": metadata['registration'] if 'registration' in metadata else None,
                    "ec_timestamp": metadata['ec_timestamp'] if 'ec_timestamp' in metadata else None,
                    "categories": userbox['categories'] if 'categories' in userbox else None
                }
            )
            self.add_userPage_data_to_user(user['user'], user['time'], userbox)
            i += 1
        return user_data

    def add_userPage_data_to_user(self, username, time, metadata):
        with self.driver.session() as session:
            for category in metadata['categories']:
                session.run("""
                    MERGE (u:User {username: $username, time: $time})
                    MERGE (c:Category {name: $category})
                    MERGE (u)-[:USERBOX]->(c)
                """, username=username, time=time, category=category)

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
        else:
            print(f"Failed to fetch data for user {username}. Status code: {response.status_code}")

        return metadata

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
        else:
            print(f"Failed to fetch data for user {username}. Status code: {response.status_code}")

        return metadata