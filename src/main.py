from logger import log
import traceback
from time import sleep
from src.config import CONFIG
from game_manager import GameManager
from bot import Bot
import datetime
from stats import Statistics


def main():
    stats = Statistics()
    while stats.runs_number < CONFIG["GAMES_MAX"]:
        try:
            stats.runs_number += 1
            log.info("Start game number " + str(stats.runs_number))
            game_time_start = datetime.datetime.now()
            bot = Bot(stats)
            bot.execute()
            stats.successful_runs += 1

        except Exception as e:
            log.error(e, exc_info=True)
            log.error(traceback.print_exc())
            log.exception('Game crashed. Restoring it')
            stats.issues_counter += 1
            stats.issues_list.append(e)
            GameManager().game_restore()
        finally:
            game_time_stop = datetime.datetime.now()
            game_time = game_time_stop - game_time_start
            game_time = game_time.total_seconds()
            stats.game_times.append(game_time)
            log.info("Game took: " + str(game_time))
            stats.update_stats_file()
            sleep_time = CONFIG["GAME_MIN_TIME"] - game_time if game_time < CONFIG["GAME_MIN_TIME"] else 1
            log.info(f"Sleep {sleep_time} before next game")
            sleep(sleep_time)


if __name__ == '__main__':
    sleep(3)
    try:
        main()
    except:
        traceback.print_exc()
