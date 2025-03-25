from server import Server
import time


if __name__ == "__main__":
    s = Server(9985)
    s.start()

    while True:
        time.sleep(5)
