import general


class ECTag:
    def __init__(self, driver, is_iteration, edit_iteration, revert_iteration):
        self.driver = driver
        self.is_iteration = is_iteration
        self.edit_iteration = edit_iteration
        self.revert_iteration = revert_iteration
        self.time_data = general.TimeData()

    def run_query(self, months, contrib_iteration=None, revert_iteration=None):
        query = """
        MATCH (u:User)
        WITH u,
            datetime(replace(u.registration, "Z", "")) AS regDate,
            datetime(replace(u.ec_timestamp, "Z", "")) AS ecDate
        WITH u,
        duration.between(regDate, ecDate) AS duration
        WHERE (duration.years * 12 + duration.months + duration.days/30.0) < $months
        AND (duration.years * 12 + duration.months + duration.days/30.0) >= $pre_months
        """
        if self.is_iteration:
            query += """
            AND (u.edit_iteration = $contrib_iteration OR u.revert_iteration = $revert_iteration)
            """
        query += """
        RETURN 
            SUM(CASE WHEN u.pro_palestine is not NULL THEN 1 ELSE 0 END) AS num_pro_palestine,
            SUM(CASE WHEN u.pro_israel is not NULL THEN 1 ELSE 0 END) AS num_pro_israel,
            COUNT(u) AS total
        """

        with self.driver.session() as session:
            result = session.run(query, months=months, pre_months=months - 1,
                                 contrib_iteration=contrib_iteration, revert_iteration=revert_iteration)
            for record in result:
                self.time_data.pro_palestine.append(record['num_pro_palestine'])
                self.time_data.pro_israel.append(record['num_pro_israel'])
                self.time_data.neutral.append(record['neutral'])

    def run_query_final(self, contrib_iteration=None, revert_iteration=None):
        query = """
        MATCH (u:User)
        WITH u,
            datetime(replace(u.registration, "Z", "")) AS regDate,
            datetime(replace(u.ec_timestamp, "Z", "")) AS ecDate
        WITH u,
        duration.between(regDate, ecDate) AS duration
        WHERE (duration.years * 12 + duration.months) > 12
        """

        if self.is_iteration:
            query += """
            AND (u.edit_iteration = $contrib_iteration OR u.revert_iteration = $revert_iteration)
            """

        query += """
        RETURN 
            SUM(CASE WHEN u.pro_palestine IS NOT NULL THEN 1 ELSE 0 END) AS num_pro_palestine,
            SUM(CASE WHEN u.pro_israel IS NOT NULL THEN 1 ELSE 0 END) AS num_pro_israel,
            COUNT(u) AS total
        """

        with self.driver.session() as session:
            result = session.run(query, contrib_iteration=contrib_iteration, revert_iteration=revert_iteration)
            for record in result:
                self.time_data.pro_palestine.append(record['num_pro_palestine'])
                self.time_data.pro_israel.append(record['num_pro_israel'])
                self.time_data.neutral.append(record['neutral'])

    def routine(self):
        if self.is_iteration:
            for month in range(2, 13):
                self.run_query(month, self.edit_iteration, self.revert_iteration)
            self.run_query_final(self.edit_iteration, self.revert_iteration)
        else:
            for month in range(2, 13):
                self.run_query(month)
            self.run_query_final()
