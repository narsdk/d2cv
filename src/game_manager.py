from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
import pyautogui as pyag
from time import sleep


class GameManager:
    def __init__(self):
        self.pysikuli = Region()

    def start_game(self):
        log.info("Checking if teamviewer message exists.")
        if Region(*CONFIG["TV_REGION"]).exists("images/tv.png", 1, threshold=0.65):
            log.info("TV exists. Clicking ok.")
            self.pysikuli.click((1465, 759))
            sleep(0.5)
        if self.pysikuli.exists("images/play.png", 20):
            log.info("Character in game already")
        else:
            log.error("ERROR: Cannot find game")
            raise GameError

    def create_game(self, difficulty):
        if self.pysikuli.exists("images/online.png"):
            log.info("Online found. clicking it.")
            self.pysikuli.click("images/online.png")
            sleep(20)
        self.pysikuli.click("images/play.png")
        sleep(0.2)
        self.pysikuli.click("images/{}.png".format(difficulty))
        create_timeout = 0.25
        while self.pysikuli.exists("images/ok.png", 2):
            log.error("Failed to create a game. Waiting {} minutes to retry.".format(create_timeout))
            self.pysikuli.click("images/ok.png")
            sleep(60 * create_timeout)
            create_timeout *= 2
            self.pysikuli.click("images/{}.png".format(difficulty))
        if self.pysikuli.exists("images/ingame.png", 20):
            log.info("Game creation success.")
        else:
            log.error("Failed to create a game")
            raise GameError

    def exit_game(self):
        log.info("Exiting game.")
        exiting_timeout = 0
        while not self.pysikuli.exists("images/play.png", 1):
            while not self.pysikuli.exists("images/save_and_exit.png"):
                if Region(*CONFIG["TV_REGION"]).exists("images/tv.png", 1, threshold=0.65):
                    log.info("TV exists. Clicking ok.")
                    self.pysikuli.click((1465, 759))
                    sleep(0.5)
                exiting_timeout += 1
                if exiting_timeout > 10:
                    log.error("Timeout when exiting game")
                    raise GameError("Timeout when exiting game")
                pyag.press("esc")
                sleep(0.2)
            self.pysikuli.click("images/save_and_exit.png")
            sleep(5)


def main():
    log.info("Game manager test")
    sleep(2)
    game_manager = GameManager()
    game_manager.start_game()
    game_manager.create_game(CONFIG["DIFFICULTY"])
    sleep(5)
    game_manager.exit_game()
    log.info("Game manager test finished.")


if __name__ == '__main__':
    main()
