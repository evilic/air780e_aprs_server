import socket
import threading
from air780e import Chip

config = {
    '868488071666208': {
        'callsign': 'bi3xyz',
        'passcode': '123456',
    },
}


def start_tcp_server(port=9985):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', port))
    server.listen(10)
    print(f"Server listening on {port}")

    try:
        while True:
            client, addr = server.accept()
            print(f'New connection from {addr}')

            chip = Chip(client)
            t = threading.Thread(target=chip.serv)
            t.start()
    except Exception as e:
        print(f'start_tcp_server error: {e}')
    finally:
        server.close()
        print('Server closed')


if __name__ == "__main__":
    start_tcp_server(9985)
