class General_Population:
    def __init__(self, il_mean, il_variance, il_std,
                 ps_mean, ps_variance, ps_std):
        self.il_mean = il_mean
        self.il_variance = il_variance
        self.il_std = il_std
        self.ps_mean = ps_mean
        self.ps_variance = ps_variance
        self.ps_std = ps_std


class IterationsData:
    def __init__(self):
        self.num_of_iterations = 0
        self.num_palestinians = []
        self.num_israelis = []
        self.total_users = []

    def update(self, num_palestinians, num_israelis, total_users):
        self.num_palestinians.append(num_palestinians)
        self.num_israelis.append(num_israelis)
        self.total_users.append(total_users)
        self.num_of_iterations+=1

    def print_all(self):
        for i in range(0, self.num_of_iterations):
            print (f"\nIteration: {i} "
                   f"\nPalestinians: {self.num_palestinians[i]} "
                   f"\nIsraelis: {self.num_israelis[i]} "
                   f"\nTotal Users: {self.total_users[i]}")

    def ps_mean(self, iteration):
        return self.num_palestinians[iteration] / self.total_users[iteration]

    def il_mean(self, iteration):
        return self.num_israelis[iteration] / self.total_users[iteration]

class Data:
    def __init__(self):
        self.iterations = []
        self.pro_palestine = []
        self.pro_israel = []
        self.total_users = []

    def insert(self, raw_data):


class TimeData:
    def __init__(self):
        self.months = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, "12+"]
        self.pro_palestine = []
        self.pro_israel = []
        self.total = []

    def insert(self, raw_data):
