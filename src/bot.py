from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import datetime
from game_manager import GameManager
from maptraveler import MapTraveler
from character import Character
from town_manager import TownManager, Act5, Act3
from tasks import Pindelskin, Mephisto
import traceback
from potioner import Potioner
import threading


class Bot:
    def __init__(self, stats):
        self.stats = stats
        self.pysikuli = Region()
        self.game_manager = GameManager()
        self.traveler = MapTraveler()
        self.character = Character(self.traveler)
        self.tasks_list = {"Pindelskin": Pindelskin(self.character, self.traveler),
                           "Mephisto": Mephisto(self.character, self.traveler)
                           }
        self.potioner = Potioner()

    def execute(self):
        self.game_manager.start_game()
        self.game_manager.create_game(CONFIG["DIFFICULTY"])
        potioner_process = None
        try:
            # town_manager = TownManager(self.character, self.stats).recognize_town()
            town_manager = Act5(self.character, self.stats)
            town_manager.execute()
            potioner_process = threading.Thread(target=self.potioner.start)
            potioner_process.daemon = True
            potioner_process.start()
            for task in CONFIG["TASKS"]:
                log.info("Starting potioner process.")
                self.tasks_list[task].execute()
            log.info("Game finished correctly.")
        except Exception as e:
            if Region(*CONFIG["TV_REGION"]).exists("images/tv.png", 1, threshold=0.65):
                log.info("TV exists. Clicking ok.")
                Region().click((1465, 759))
                sleep(0.5)
            log.error(e, exc_info=True)
            log.error(traceback.print_exc())
            log.exception('Exception found.')
            self.stats.issues_counter += 1
            self.stats.issues_list.append(e)
        finally:
            log.info("Finishing potioner thread.")
            self.potioner.running = False
            if potioner_process is not None:
                potioner_process.join()
            self.game_manager.exit_game()


def main():
    log.info("Bot test")
    bot = Bot()
    bot.execute()


if __name__ == '__main__':
    main()
