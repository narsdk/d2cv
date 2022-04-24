from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
from time import sleep
import datetime
from game_manager import GameManager
from maptraveler import MapTraveler
from character import Character
from town_manager import Act5
from tasks import Pindelskin, Mephisto


class Bot:
    def __init__(self):
        self.pysikuli = Region()
        self.game_manager = GameManager()
        self.traveler = MapTraveler()
        self.character = Character(self.traveler)
        self.town_manager = Act5(self.character)
        self.tasks_list = {"Pindelskin": Pindelskin(self.character, self.traveler),
                           "Mephisto": Mephisto(self.character, self.traveler)
                           }

    def execute(self):
        game_time_start = datetime.datetime.now()
        self.game_manager.start_game()
        self.game_manager.create_game(CONFIG["DIFFICULTY"])
        try:
            self.town_manager.execute()
            for task in CONFIG["TASKS"]:
                self.tasks_list[task].execute()
            log.info("Game finished correctly.")
        except GameError as e:
            if Region(*CONFIG["TV_REGION"]).exists("images/tv.png", 1, threshold=0.65):
                log.info("TV exists. Clicking ok.")
                Region().click((1465, 759))
                sleep(0.5)
            log.error(e, exc_info=True)
            log.exception('Exception found.')
            # issues_counter += 1
            # issues_list.append(e)
        finally:
            self.game_manager.exit_game()
            game_time_stop = datetime.datetime.now()
            game_time = game_time_stop - game_time_start
            sleep(95 - game_time.total_seconds())
            log.info("Game took: " + str(game_time.seconds))


def main():
    log.info("Bot test")
    bot = Bot()
    bot.execute()


if __name__ == '__main__':
    main()
