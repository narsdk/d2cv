from logger import log, GameError
from pysikuli import Region
from src.config import CONFIG
import pyautogui as pyag
from time import sleep


class GameManager:
    def __init__(self):
        self.screen = Region()

    def start_game(self):
        log.info("Checking if teamviewer message exists.")
        if Region(*CONFIG["TV_REGION"]).exists("images/tv.png", 1, threshold=0.65):
            log.info("TV exists. Clicking ok.")
            self.screen.click((1465, 759))
            sleep(0.5)
        if self.screen.exists("images/play.png", 20):
            log.info("Character in game already")
        else:
            log.error("ERROR: Cannot find game")
            raise GameError

    def create_game(self, difficulty):
        if self.screen.exists("images/online.png"):
            log.info("Online found. clicking it.")
            self.screen.click("images/online.png")
            sleep(20)
        self.screen.click("images/play.png")
        sleep(0.2)
        self.screen.click("images/{}.png".format(difficulty))
        create_timeout = 0.25
        while self.screen.exists("images/ok.png", 2):
            log.error("Failed to create a game. Waiting {} minutes to retry.".format(create_timeout))
            self.screen.click("images/ok.png")
            sleep(60 * create_timeout)
            create_timeout *= 2
            self.screen.click("images/{}.png".format(difficulty))
        if self.screen.exists("images/ingame.png", 20):
            log.info("Game creation success.")
        else:
            log.error("Failed to create a game")
            raise GameError

    def exit_game(self):
        log.info("Exiting game.")
        exiting_timeout = 0
        while not self.screen.exists("images/play.png", 1):
            while not self.screen.exists("images/save_and_exit.png"):
                if Region(*CONFIG["TV_REGION"]).exists("images/tv.png", 1, threshold=0.65):
                    log.info("TV exists. Clicking ok.")
                    self.screen.click((1465, 759))
                    sleep(0.5)
                exiting_timeout += 1
                if exiting_timeout > 10:
                    log.error("Timeout when exiting game")
                    raise GameError("Timeout when exiting game")
                pyag.press("esc")
                sleep(0.2)
            self.screen.click("images/save_and_exit.png")
            sleep(5)

    def game_restore(self):
        log.info("Game restoring start")
        if not self.screen.exists("images/play.png", 1):
            restore_timeout = 0
            while True:
                restore_timeout += 1
                if restore_timeout % 5 == 0:
                    log.info("Alt+F4 as loading found")
                    with pyag.hold('alt'):
                        pyag.press("f4")
                    sleep(10)
                    pyag.press("up")
                    sleep(2)
                    pyag.press("enter")
                    sleep(10)
                if restore_timeout > 100:
                    log.info("Fatal error: cannot find launcher")
                    exit(1)
                # launcher = get_color_location([255, 224, 116], region=(438,1399,151,41))
                # if launcher != (None, None):
                log.info("Clicking launcher")
                self.screen.click((513, 1416))
                sleep(2)

                graj = Region(342, 899, 530, 396).match_color([255, 224, 116])
                if graj != (None, None):
                    log.info("Clicking graj")
                    graj_x, graj_y = graj
                    graj = (graj_x - 100, graj_y)
                    Region(342, 899, 530, 396).click(graj)
                    sleep(2)
                    break
                else:
                    log.error("Cannot find graj")
                    sleep(30)

            while not self.screen.exists("images/play.png", 10):
                log.info("Waiting for play image.")
                sleep(20)
                pyag.press("space")

            log.info("Restoring game success.")
        else:
            log.info("Play exists")


def main():
    log.info("Game manager test")
    sleep(2)
    game_manager = GameManager()
    game_manager.start_game()
    game_manager.create_game(CONFIG["DIFFICULTY"])
    sleep(5)
    game_manager.exit_game()
    log.info("Game manager test finished.")


def restorer_test():
    log.info("Restorer test.")
    sleep(2)
    game_manager = GameManager()
    game_manager.game_restore()


if __name__ == '__main__':
    main()
