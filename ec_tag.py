import general


class ECTag:
    def __init__(self, driver):
        self.driver = driver
        self.time_data = general.TimeData()

    def run_query(self, months, is_prune):
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
        if is_prune:
            query += """
            AND u.is_prune = false
            """
        query += """
        RETURN 
            SUM(CASE WHEN u.pro_palestine is not NULL THEN 1 ELSE 0 END) AS num_pro_palestine,
            SUM(CASE WHEN u.pro_israel is not NULL THEN 1 ELSE 0 END) AS num_pro_israel,
            COUNT(u) AS total
        """

        with self.driver.session() as session:
            result = session.run(query, months=months, pre_months=months - 1)
            for record in result:
                self.time_data.pro_palestine.append(record['num_pro_palestine'])
                self.time_data.pro_israel.append(record['num_pro_israel'])
                self.time_data.neutral.append(record['neutral'])

    def run_query_final(self, is_prune):
        query = """
        MATCH (u:User)
        WITH u,
            datetime(replace(u.registration, "Z", "")) AS regDate,
            datetime(replace(u.ec_timestamp, "Z", "")) AS ecDate
        WITH u,
        duration.between(regDate, ecDate) AS duration
        WHERE (duration.years * 12 + duration.months) > 12
        """

        if is_prune:
            query += """
            AND u.is_prune = false
            """

        query += """
        RETURN 
            SUM(CASE WHEN u.pro_palestine IS NOT NULL THEN 1 ELSE 0 END) AS num_pro_palestine,
            SUM(CASE WHEN u.pro_israel IS NOT NULL THEN 1 ELSE 0 END) AS num_pro_israel,
            COUNT(u) AS total
        """

        with self.driver.session() as session:
            result = session.run(query)
            for record in result:
                self.time_data.pro_palestine.append(record['num_pro_palestine'])
                self.time_data.pro_israel.append(record['num_pro_israel'])
                self.time_data.neutral.append(record['neutral'])

    def routine(self, is_prune):
        for month in range(2, 13):
            self.run_query(month, is_prune)
        self.run_query_final(is_prune)
