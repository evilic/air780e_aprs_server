import socket
import threading
import time


class Server:
    def __init__(self, port: int, host='0.0.0.0'):
        self.__port = port

        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server.bind((host, port))
        self.__server.listen(1)
        print(f"Server listening on {host}:{port}")

        self.__client = None

    def start(self):
        listener = threading.Thread(
            target=self.__receive, args=())
        listener.start()

    def __send(self):
        current_client = self.__client
        try:
            while True:
                # msg = input('Enter message: ')
                time.sleep(5)
                msg = 'Hello from server'
                if self.__client != current_client:
                    print('Client changed')
                    break
                self.__client.send(msg.encode('utf-8'))
        except Exception as e:
            print(f'Send error: {e}')
        finally:
            print('Send thread quit')

    def __receive(self):
        try:
            while True:
                self.__client, addr = self.__server.accept()
                print(f'New connection from {addr}')
                sender = threading.Thread(
                    target=self.__send, args=())
                sender.start()

                try:
                    while True:
                        msg = self.__client.recv(1024).decode('utf-8')
                        if not msg:
                            break
                        print(f'Received message: {msg}')
                except Exception as ex:
                    print(f'Client recv error: {ex}')
                finally:
                    self.__client.close()
                    self.__client = None
        except Exception as e:
            print(f'Accept error: {e}')
        finally:
            self.__server.close()
            self.__server = None
            print(f'Server({self.__port}) closed')
