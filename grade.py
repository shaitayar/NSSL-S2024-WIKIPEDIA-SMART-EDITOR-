import general
from datetime import datetime
class Grades:
    def __init__(self, grades):
        self.grade1 = grades[1]
        self.grade2 = grades[2]
        self.grade3 = grades[3]

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
            g2 = (1/(1+months_until_ec))* self.grade2

        if user_data.total_reverts != 0 and user_data.protected_reverts != 0:
            g3 = (user_data.protected_reverts/user_data.total_reverts)*self.grade3

        return g1+g2+g3
