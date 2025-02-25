import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

class Stats:
    pro_israel_mean = 0
    pro_israel_variance = 0
    pro_palestine_mean = 0
    pro_palestine_variance = 0

class Graphs():
    def __init__(self, pro_israel_data, pro_palestine_data, neutral_data, ec_tag_general_population, contributions, reverts, ec_reverts, ec_tag):
        self.pro_israel_data = pro_israel_data
        self.pro_palestine_data = pro_palestine_data
        self.neutral_data = neutral_data
        self.ec_tag_general_population = ec_tag_general_population
        self.total_data = pro_israel_data + pro_palestine_data + neutral_data
        self.total_users_all_day = []

        self.data = Stats()

        self.contributions = contributions
        self.reverts = reverts
        self.ec_reverts = ec_reverts
        self.ec_tag = ec_tag

    def get_hourly_averages(self, data):
        hourly_averages = []
        for hour in range(24):
            hour_data = data[hour * 4: (hour + 1) * 4]
            hourly_averages.append(hour_data.mean())
        return hourly_averages

    def general_population_graph_hourly(self):

        time_intervals = [f"{h:02}:{m:02}" for h in range(24) for m in range(0, 60, 15)]

        self.pro_israel_data = pd.Series(self.pro_israel_15min).reindex(time_intervals, fill_value=0)
        self.pro_palestine_data = pd.Series(self.pro_palestine_15min).reindex(time_intervals, fill_value=0)
        self.neutral_data = pd.Series(self.neutral_15min).reindex(time_intervals, fill_value=0)
        self.total_data = self.pro_israel_data + self.pro_palestine_data + self.neutral_data

        pro_israel_hourly = self.get_hourly_averages(self.pro_israel_data)
        pro_palestine_hourly = self.get_hourly_averages(self.pro_palestine_data)
        total_hourly = self.get_hourly_averages(self.total_data)

        #plot
        plt.figure(figsize=(14, 8))
        width = 0.35
        #pro israel
        plt.bar(range(24), pro_israel_hourly, width=width, label='Pro-Israel', align='center', color='blue')

        #pro palestine
        plt.bar([i + width for i in range(24)], pro_palestine_hourly, width=width, label='Pro-Palestine', align='center',
            color='red')

        plt.xlabel('Hour of the Day')
        plt.ylabel('Average Percentage of Users')
        plt.title('Hourly Average of Recent Changes')
        plt.legend()

        plt.xticks(range(24), [f"{h:02}:00" for h in range(24)])

        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def general_population_graph_15min(self):
        time_intervals = [f"{h:02}:{m:02}" for h in range(24) for m in range(0, 60, 15)]

        pro_israel_data = pd.Series(self.pro_israel_15min).reindex(time_intervals, fill_value=0)
        pro_palestine_data = pd.Series(self.pro_palestine_15min).reindex(time_intervals, fill_value=0)
        neutral_data = pd.Series(self.neutral_15min).reindex(time_intervals, fill_value=0)
        total_data = pro_israel_data + pro_palestine_data + neutral_data
        total_users_all_day = total_data.sum()

        plt.figure(figsize=(14, 8))

        plt.bar([i - 0.3 for i in range(len(pro_israel_data))], (pro_israel_data.values * total_data.values / total_users_all_day),
                width=0.3, label='Pro-Israel')

        plt.bar([i for i in range(len(pro_palestine_data))], (pro_palestine_data.values * total_data.values / total_users_all_day),
                width=0.3, label='Pro-Palestine')

        plt.xlabel('Time (15-Minute Intervals)')
        plt.ylabel('Percentage of Users')
        plt.title('Recent Changes Per 15 Minutes')
        plt.legend()

        plt.xticks(range(len(time_intervals)), time_intervals, rotation=90)
        plt.grid(True)
        plt.tight_layout()
        plt.show()

    def calculate_mean_and_variance(self):
        pro_israel_weights = self.pro_israel_data.values * self.total_data.values / self.total_users_all_day
        pro_palestine_weights = self.pro_palestine_data.values * self.total_data.values / self.total_users_all_day
        neutral_weights = self.neutral_data.values * self.total_data.values / self.total_users_all_day

        self.data.pro_israel_mean = pro_israel_weights.mean()
        self.data.pro_israel_variance = pro_israel_weights.var()
        pro_israel_std_dev = pro_israel_weights.std()

        self.data.pro_palestine_mean = pro_palestine_weights.mean()
        self.data.pro_palestine_variance = pro_palestine_weights.var()
        pro_palestine_std_dev = pro_palestine_weights.std()

    def calc_and_plot_ec_contribs(self):
        data_contribs = self.contributions

        df = pd.DataFrame(data_contribs)
        df['Mean Ratio'] = df['Palestinians'] / df['Total Users']

        plt.figure(figsize=(10, 6))

        bars = plt.bar(df['Iteration'], df['Mean Ratio'], color='red', alpha=0.7)

        plt.axhline(y=self.data.pro_palestine_mean - self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean-variance= {(self.data.pro_palestine_mean - self.data.pro_palestine_variance) * 100:.2}e-2')
        plt.axhline(y=self.data.pro_palestine_mean + self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean+variance= {(self.data.pro_palestine_mean + self.data.pro_palestine_variance) * 100:.2}e-2')

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.0005, f'{yval:.6f}', ha='center', va='bottom',
                     fontsize=12)

        plt.xlabel('Iteration', fontsize=14)
        plt.ylabel('Mean Pro Palestinians', fontsize=14)

        plt.title('EC Pages Contributions', fontsize=16)
        plt.legend(fontsize=12)
        plt.xticks(range(0, len(df['Iteration'])))
        plt.show()

    def calc_and_plot_reverts(self):

        df = pd.DataFrame(self.reverts)

        df['Palestinian Ratio'] = df['Palestinians'] / df['Total Users']
        df['Israeli Ratio'] = df['Israelis'] / df['Total Users']

        plt.figure(figsize=(12, 7))

        bars_palestinians = plt.bar(df['Iteration'] - 0.2, df['Palestinian Ratio'], width=0.4, color='red', alpha=0.7,
                                    label='Palestinians')
        bars_israelis = plt.bar(df['Iteration'] + 0.2, df['Israeli Ratio'], width=0.4, color='blue', alpha=0.7,
                                label='Israelis')

        plt.axhline(y=self.data.pro_palestine_mean - self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean-variance= {(self.data.pro_palestine_mean - self.data.pro_palestine_variance) * 100:.2}e-2')
        plt.axhline(y=self.data.pro_palestine_mean + self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean+variance= {(self.data.pro_palestine_mean + self.data.pro_palestine_variance) * 100:.2}e-2')

        plt.xlabel('Iteration', fontsize=16)
        plt.ylabel('Mean', fontsize=16)

        plt.title('Reverts', fontsize=18)
        plt.xticks(range(0, len(df['Iteration'])))

        plt.legend(fontsize=14)
        plt.show()

        #for i, row in df.iterrows():
        #    print(f"Iteration: {row['Iteration']} - Palestinians: {row['Palestinians']} Israelis: {row['Israelis']} Total Users: {row['Total Users']}")

    def calc_and_plot_ec_reverts(self):
        df = pd.DataFrame(self.ec_reverts)

        df['Palestinian Ratio'] = df['Palestinians'] / df['Total Users']
        df['Israeli Ratio'] = df['Israelis'] / df['Total Users']

        plt.figure(figsize=(12, 7))

        bars_palestinians = plt.bar(df['Iteration'] - 0.2, df['Palestinian Ratio'], width=0.4, color='red', alpha=0.7,
                                    label='Palestinians')
        bars_israelis = plt.bar(df['Iteration'] + 0.2, df['Israeli Ratio'], width=0.4, color='blue', alpha=0.7,
                                label='Israelis')

        plt.axhline(y=self.data.pro_palestine_mean - self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean-variance= {(self.data.pro_palestine_mean - self.data.pro_palestine_variance) * 100:.2}e-2')
        plt.axhline(y=self.data.pro_palestine_mean + self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean+variance= {(self.data.pro_palestine_mean + self.data.pro_palestine_variance) * 100:.2}e-2')

        plt.xlabel('Iteration', fontsize=16)
        plt.ylabel('Mean', fontsize=16)

        plt.title('Reverts on EC pages', fontsize=18)
        plt.xticks(range(0, len(df['Iteration'])))

        plt.legend(fontsize=14)
        plt.show()

    def calc_and_plot_ec_tag(self):
        pro_palestine_ratio = [pp / t for pp, t in zip(self.ec_tag.pro_palestine, self.ec_tag.total)]
        pro_israel_ratio = [pi / t for pi, t in zip(self.ec_tag.pro_israel, self.ec_tag.total)]

        bar_width = 0.35
        index = np.arange(len(self.ec_tag.months))

        plt.figure(figsize=(10, 6))
        plt.bar(index - bar_width / 2, pro_palestine_ratio, bar_width, color='red', label='Pro-Palestine Ratio')
        plt.bar(index + bar_width / 2, pro_israel_ratio, bar_width, color='blue', label='Pro-Israel Ratio')

        plt.xlabel('Months', fontsize=14)
        plt.ylabel('Mean (Pro-Palestine / Pro-Israel)', fontsize=14)
        plt.title('Got EC Within Months From Registration', fontsize=16)

        plt.xticks(index, self.ec_tag.months)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.show()

    def general_population_graph_ec_tag(self):
        pro_palestine_ratio = [pp * 100 / t for pp, t in zip(self.ec_tag_general_population.pro_palestine, self.ec_tag_general_population.total)]
        pro_israel_ratio = [pi * 100 / t for pi, t in zip(self.ec_tag_general_population.pro_israel, self.ec_tag_general_population.total)]

        bar_width = 0.35
        index = np.arange(len(self.ec_tag_general_population.months))

        plt.figure(figsize=(10, 6))
        plt.bar(index - bar_width / 2, pro_palestine_ratio, bar_width, color='red', label='Pro-Palestine')
        plt.bar(index + bar_width / 2, pro_israel_ratio, bar_width, color='blue', label='Pro-Israel')

        plt.xlabel('Months', fontsize=14)
        plt.ylabel('Percentage of Pro Israel and Pro Palestine users(%)', fontsize=14)
        plt.title('Got EC Within Months From Registration - General Population', fontsize=16)

        plt.xticks(index, self.ec_tag_general_population.months)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.show()

