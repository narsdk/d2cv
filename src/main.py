from logger import log
import traceback
from time import sleep
from src.config import CONFIG
import multiprocessing
from potioner import Potioner
from game_manager import GameManager
from bot import Bot
import datetime
import ctypes


def main():
    log.info("main module test")
    game_number = 0
    while game_number < CONFIG["GAMES_MAX"]:
        potioner = Potioner()
        try:
            game_number += 1
            log.info("Start game number " + str(game_number))
            game_time_start = datetime.datetime.now()

            potioner_process = multiprocessing.Process(target=potioner.start)
            potioner_process.daemon = True
            potioner_process.start()

            bot = Bot()
            bot.execute()

        except Exception as e:
            log.error(e, exc_info=True)
            log.error(traceback.print_exc())
            log.exception('Game crashed. Restoring it')
            # issues_counter += 1
            # issues_list.append(e)
            GameManager().game_restore()
        finally:
            log.info("Finishing potioner thread.")
            potioner_process.kill()
            game_time_stop = datetime.datetime.now()
            game_time = game_time_stop - game_time_start
            # sleep(abs(95 - game_time.total_seconds()))
            log.info("Game took: " + str(game_time.seconds))


if __name__ == '__main__':
    sleep(3)
    try:
        main()
    except:
        traceback.print_exc()