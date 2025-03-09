import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

class Stats:
    pro_israel_mean = 0
    pro_israel_variance = 0
    pro_palestine_mean = 0
    pro_palestine_variance = 0

class Graphs():
    def __init__(self, graph_contributions, graph_reverts, graph_ec_reverts, graph_ec_tag, contributions, reverts, ec_reverts, data_ec_tag, general_population_data):
        self.graph_contributions = graph_contributions
        self.graph_reverts = graph_reverts
        self.graph_ec_reverts = graph_ec_reverts
        self.graph_ec_tag = graph_ec_tag
        self.contributions = contributions
        self.reverts = reverts
        self.ec_reverts = ec_reverts
        self.data_ec_tag = data_ec_tag
        self.data = Stats()
        self.general_population_data = general_population_data

    def routine(self):
        self.calculate_mean_and_variance()
        if (self.graph_contributions):
            self.calc_and_plot_ec_contribs()
        if (self.graph_reverts):
            self.calc_and_plot_reverts()
        if (self.graph_ec_reverts):
            self.calc_and_plot_ec_reverts()
        if (self.graph_ec_tag):
            self.calc_and_plot_ec_tag()

    def calculate_mean_and_variance(self):
        time_intervals = (self.general_population_data.to_dict())['time']

        dd = self.general_population_data.to_default_dict()
        pro_israel_data = pd.Series(dd['pro_israel_dict']).reindex(time_intervals, fill_value=0)
        pro_palestine_data = pd.Series(dd['pro_palestine_dict']).reindex(time_intervals, fill_value=0)
        neutral_data = pd.Series(dd['neutral_dict']).reindex(time_intervals, fill_value=0)
        total_data = pro_israel_data + pro_palestine_data + neutral_data

        total_users_all_day = total_data.sum()

        pro_israel_weights = pro_israel_data * total_data.values / total_users_all_day
        pro_palestine_weights = pro_palestine_data * total_data.values / total_users_all_day
        neutral_weights = neutral_data * total_data.values / total_users_all_day

        self.data.pro_israel_mean = pro_israel_weights.mean()
        self.data.pro_israel_variance = pro_israel_weights.var()
        pro_israel_std_dev = pro_israel_weights.std()

        self.data.pro_palestine_mean = pro_palestine_weights.mean()
        self.data.pro_palestine_variance = pro_palestine_weights.var()
        pro_palestine_std_dev = pro_palestine_weights.std()

    def calc_and_plot_ec_contribs(self):
        if not self.contributions:
            print("Unable To Plot Contributions Graph - Empty Contributions")
            return
        data = self.contributions.to_dict()
        df = pd.DataFrame.from_dict(data)
        df['mean_ratio'] = df['pro_palestine'] / df['neutral']

        plt.figure(figsize=(10, 6))

        bars = plt.bar(df['iterations'], df['mean_ratio'], color='red', alpha=0.7)

        plt.axhline(y=self.data.pro_palestine_mean - self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean-variance= {((self.data.pro_palestine_mean - self.data.pro_palestine_variance) * 100):.2f}e-2')
        plt.axhline(y=self.data.pro_palestine_mean + self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean+variance= {((self.data.pro_palestine_mean + self.data.pro_palestine_variance) * 100):.2f}e-2')

        for bar in bars:
            yval = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, yval + 0.0005, f'{yval:.6f}', ha='center', va='bottom',
                     fontsize=12)

        plt.xlabel('Iteration', fontsize=14)
        plt.ylabel('Mean Pro Palestinians', fontsize=14)

        plt.title('EC Pages Contributions', fontsize=16)
        plt.legend(fontsize=12)
        plt.xticks(range(0, len(df['iterations'])))
        plt.show()

    def calc_and_plot_reverts(self):
        if not self.reverts:
            print("Unable To Plot Reverts Graph - Empty Reverts")
            return
        data = self.reverts.to_dict()
        df = pd.DataFrame.from_dict(data)

        df['palestine_ratio'] = df['pro_palestine'] / df['neutral']
        df['Israeli Ratio'] = df['pro_israel'] / df['neutral']

        plt.figure(figsize=(12, 7))

        bars_palestinians = plt.bar(df['iterations'] - 0.2, df['palestine_ratio'], width=0.4, color='red', alpha=0.7,
                                    label='Palestinians')
        bars_israelis = plt.bar(df['iterations'] + 0.2, df['israel_ratio'], width=0.4, color='blue', alpha=0.7,
                                label='Israelis')

        plt.axhline(y=self.data.pro_palestine_mean - self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean-variance= {((self.data.pro_palestine_mean - self.data.pro_palestine_variance) * 100):.2f}e-2')
        plt.axhline(y=self.data.pro_palestine_mean + self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean+variance= {((self.data.pro_palestine_mean + self.data.pro_palestine_variance) * 100):.2f}e-2')

        plt.xlabel('Iteration', fontsize=16)
        plt.ylabel('Mean', fontsize=16)

        plt.title('Reverts', fontsize=18)
        plt.xticks(range(0, len(df['iterations'])))

        plt.legend(fontsize=14)
        plt.show()

        #for i, row in df.iterrows():
        #    print(f"Iteration: {row['Iteration']} - Palestinians: {row['Palestinians']} Israelis: {row['Israelis']} Total Users: {row['Total Users']}")

    def calc_and_plot_ec_reverts(self):
        if not self.ec_reverts:
            print("Unable To Plot EC Reverts Graph - Empty EC Reverts")
            return
        data = self.ec_reverts.to_dict()
        df = pd.DataFrame.from_dict(data)

        df['palestine_ratio'] = df['pro_palestine'] / df['neutral']
        df['israel_ratio'] = df['pro_israel'] / df['neutral']

        plt.figure(figsize=(12, 7))

        bars_palestinians = plt.bar(df['iterations'] - 0.2, df['palestine_ratio'], width=0.4, color='red', alpha=0.7,
                                    label='Palestinians')
        bars_israelis = plt.bar(df['iterations'] + 0.2, df['israel_ratio'], width=0.4, color='blue', alpha=0.7,
                                label='Israelis')

        plt.axhline(y=self.data.pro_palestine_mean - self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean-variance= {((self.data.pro_palestine_mean - self.data.pro_palestine_variance) * 100):.2f}e-2')
        plt.axhline(y=self.data.pro_palestine_mean + self.data.pro_palestine_variance, color='green', linestyle='-',
                    label=f'General Population: mean+variance= {((self.data.pro_palestine_mean + self.data.pro_palestine_variance) * 100):.2f}e-2')

        plt.xlabel('Iteration', fontsize=16)
        plt.ylabel('Mean', fontsize=16)

        plt.title('Reverts on EC pages', fontsize=18)
        plt.xticks(range(0, len(df['iterations'])))

        plt.legend(fontsize=14)
        plt.show()

    def calc_and_plot_ec_tag(self):
        if not self.data_ec_tag:
            print("Unable To Plot EC Tag Graph - Empty EC Tag")
            return
        total = [(pp + pi + n) for pp, pi, n in zip(self.data_ec_tag.pro_palestine, self.data_ec_tag.pro_israel, self.data_ec_tag.neutral)]
        pro_palestine_ratio = [pp / t if t != 0 else 0 for pp, t in zip(self.data_ec_tag.pro_palestine, total)]
        pro_israel_ratio = [pi / t if t != 0 else 0 for pi, t in zip(self.data_ec_tag.pro_israel, total)]

        bar_width = 0.35
        index = np.arange(len(self.data_ec_tag.months))

        plt.figure(figsize=(10, 6))
        plt.bar(index - bar_width / 2, pro_palestine_ratio, bar_width, color='red', label='Pro-Palestine Ratio')
        plt.bar(index + bar_width / 2, pro_israel_ratio, bar_width, color='blue', label='Pro-Israel Ratio')

        plt.xlabel('Months', fontsize=14)
        plt.ylabel('Mean (Pro-Palestine / Pro-Israel)', fontsize=14)
        plt.title('Got EC Within Months From Registration', fontsize=16)

        plt.xticks(index, self.data_ec_tag.months)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.show()


class GeneralPopulationGraph:
    def __init__(self, graph_general_population_hour, graph_general_population_15min, graph_general_population_ec_tag,
                 general_population_total, general_population_ec_tag):
        self.graph_general_population_hour = graph_general_population_hour
        self.graph_general_population_15min = graph_general_population_15min
        self.graph_general_population_ec_tag = graph_general_population_ec_tag
        self.time_data = general_population_total
        self.ec_time_data = general_population_ec_tag


    def routine(self):
        if(self.graph_general_population_hour):
            self.general_population_graph_hourly()
        if(self.graph_general_population_15min):
            self.general_population_graph_15min()
        if(self.graph_general_population_ec_tag):
            self.general_population_graph_ec_tag()



    def get_hourly_averages(self, data):
        hourly_averages = []
        for hour in range(24):
            hour_data = data[hour * 4: (hour + 1) * 4]
            hourly_averages.append(hour_data.mean())
        return hourly_averages

    def general_population_graph_hourly(self):
        if not self.time_data:
            print("Unable To Plot General Population Graph - Empty General Population")
            return
        time_intervals = [f"{h:02}:{m:02}" for h in range(24) for m in range(0, 60, 15)]
        dd = self.time_data.to_default_dict()
        pro_israel_data = pd.Series(dd['pro_israel_dict']).reindex(time_intervals, fill_value=0)
        pro_palestine_data = pd.Series(dd['pro_palestine_dict']).reindex(time_intervals, fill_value=0)
        neutral_data = pd.Series(dd['neutral_dict']).reindex(time_intervals, fill_value=0)
        total_data = pro_israel_data + pro_palestine_data + neutral_data

        pro_israel_hourly = self.get_hourly_averages(pro_israel_data)
        pro_palestine_hourly = self.get_hourly_averages(pro_palestine_data)
        total_hourly = self.get_hourly_averages(total_data)

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
        if not self.time_data:
            print("Unable To Plot General Population Graph - Empty General Population")
            return

        time_intervals = [f"{h:02}:{m:02}" for h in range(24) for m in range(0, 60, 15)]

        dd = self.time_data.to_default_dict()
        pro_israel_data = pd.Series(dd['pro_israel_dict']).reindex(time_intervals, fill_value=0)
        pro_palestine_data = pd.Series(dd['pro_palestine_dict']).reindex(time_intervals, fill_value=0)
        neutral_data = pd.Series(dd['neutral_dict']).reindex(time_intervals, fill_value=0)
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

    def general_population_graph_ec_tag(self):
        if not self.ec_time_data:
            print("Unable To Plot General Population EC Tag Graph - Empty General Population EC Tag")
            return
        pro_palestine_ratio = [pp * 100 / t for pp, t in zip(self.ec_time_data.pro_palestine, self.ec_time_data.neutral)]
        pro_israel_ratio = [pi * 100 / t for pi, t in zip(self.ec_time_data.pro_israel, self.ec_time_data.neutral)]

        bar_width = 0.35
        index = np.arange(len(self.ec_time_data.months))

        plt.figure(figsize=(10, 6))
        plt.bar(index - bar_width / 2, pro_palestine_ratio, bar_width, color='red', label='Pro-Palestine')
        plt.bar(index + bar_width / 2, pro_israel_ratio, bar_width, color='blue', label='Pro-Israel')

        plt.xlabel('Months', fontsize=14)
        plt.ylabel('Percentage of Pro Israel and Pro Palestine users(%)', fontsize=14)
        plt.title('Got EC Within Months From Registration - General Population', fontsize=16)

        plt.xticks(index, self.ec_time_data.months)
        plt.legend(fontsize=12)
        plt.tight_layout()
        plt.show()
