from logger import log
import datetime
import os


class Statistics:
    def __init__(self):
        self.runs_number = 0
        self.successful_runs = 0
        self.start_time = datetime.datetime.now()
        self.issues_counter = 0
        self.issues_list = []

        self.corpses_collected = 0
        self.merc_resurrected = 0

        self.life_potions_bought = 0
        self.mana_potions_bought = 0

        self.found_items_list = []
        self.ignored_items_list = []

        # Create file where will be current statistics of run
        if not os.path.exists("statistics"):
            os.mkdir("statistics")

        self.execution_number = max([int(x.split(".")[1]) for x in os.listdir("statistics")]) \
            if len(os.listdir("statistics")) > 0 else 0
        self.execution_number += 1

        self.stats_file = open("statistics/run." + str(self.execution_number) + ".log", "w+")
        self.last_update = datetime.datetime.now()

        self.game_times = []
        self.longest_game = 0
        self.average_game = 0
        self.shortest_game = 0

    def get_stats(self):
        return '''---------------------------------------------------------------------
Runs number ''' + str(self.runs_number) + ' in bot execution number '+str(self.execution_number)+'''.
Run start: ''' + str(self.start_time) + '''.
Last update: ''' + str(self.last_update) + '''.
--------------------------------------------------------------------- 
Current number of issues: ''' + str(self.issues_counter) + '''.
Issues list: ''' + str(self.issues_list) + '''. 
Corpses collected: ''' + str(self.corpses_collected) + '''.
Merc resurrections: ''' + str(self.merc_resurrected) + '''.
Life/mana potions used: ''' + str(self.life_potions_bought) + "/" + str(self.mana_potions_bought) + '''.
Correct finish: ''' + str(self.successful_runs) + '''.
Found items list: ''' + str(self.found_items_list) + '''.
Ignored items list: ''' + str(self.ignored_items_list) + '''.  
---------------------------------------------------------------------
Times:
Longest game time: ''' + str(self.longest_game) + '''.
Average game time: ''' + str(self.average_game) + '''.
Shortest game time: ''' + str(self.shortest_game) + '''.
'''

    def update_stats_file(self):
        self.last_update = datetime.datetime.now()
        self.calculate_stats()

        self.stats_file.seek(0)
        self.stats_file.write(self.get_stats())
        self.stats_file.truncate()

    def calculate_stats(self):
        if len(self.game_times) > 0:
            self.longest_game = max(self.game_times)
            self.average_game = sum(self.game_times)/len(self.game_times)
            self.shortest_game = min(self.game_times)

def main():
    log.info("Statistics test.")
    stats = Statistics()
    log.info(stats.get_stats())
    stats.update_stats_file()


if __name__ == '__main__':
    main()
