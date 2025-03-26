import socket
import time
import re
import threading


class Command:
    def __init__(self, cmd: str, timeout: int, func_test, func_parse):
        self.__cmd = cmd
        self.__timeout = timeout
        self.__test = func_test
        self.__parse = func_parse
        self.__response = None

    def get_cmd(self):
        return self.__cmd

    def get_timeout(self):
        return self.__timeout

    def test_response(self, response):
        if self.__test(response):
            self.__response = response
            return True
        return False

    def has_response(self):
        return self.__response is not None

    def parse_response(self):
        result = self.__parse(self.__response)
        self.__response = None
        return result


class Communication:
    conn_timeout = 90  # 连接超时时间

    def __init__(self, s: socket.socket):
        self.alive = True
        self.__socket = s
        self.__last_hb_at = time.time()  # 上次心跳时间
        self.__current_operation = None
        self.__current_operation_id = 0

    def send(self, cmd: Command):
        if self.__current_operation:
            raise Exception('Current operation is not finished yet')

        self.__current_operation = cmd
        self.__current_operation_id += 1
        operation_timeout_at = time.time() + cmd.get_timeout()
        while time.time() <= operation_timeout_at:
            time.sleep(1)
            if self.__current_operation.has_response():
                result = self.__current_operation.parse_response()
                self.__current_operation = None
                return result

        raise Exception('Operation timeout')

    def loop_send(self):
        current_op_id = -1
        while self.alive:
            if self.__current_operation and \
                    current_op_id != self.__current_operation_id:
                msg = self.__current_operation.get_cmd()
                self.__socket.send(msg.encode('utf-8'))
                current_op_id = self.__current_operation_id
            time.sleep(1)

    def loop_alive_check(self):  # 可以通过设置 timeout 来代替这个方法
        while self.alive:
            if time.time() - self.__last_hb_at > Communication.conn_timeout:
                self.alive = False
                break
            time.sleep(1)

    def loop_receive(self):
        while self.alive:
            raw = self.__socket.recv(1024)
            print(f'Received message: {raw}')

            if not raw:
                self.alive = False
                break

            if self.__is_heartbeat(raw):
                continue

            if self.__is_ctrl_c(raw):
                self.alive = False
                break

            if self.__current_operation and \
                    self.__current_operation.test_response(raw):
                continue

            print(f'Unknown message: {raw}')
        # TODO: 需要处理异常；需要关闭连接

    def __is_heartbeat(self, raw):
        if raw == b'\x00':
            self.__last_hb_at = time.time()
            return True
        return False

    def __is_ctrl_c(self, raw):
        if raw == b'\x03':
            return True
        return False


class Chip:
    def __init__(self, s: socket.socket):
        self.__com = Communication(s)
        self.__last_location = None
        self.__last_location_update_at = 0
        self.__location_update_interval = 60  # 初始更新间隔（秒）
        self.__cmd_get_lbsloc = None
        self.__cmd_get_gps = None

    def __get_gps_location(self):
        if not self.__cmd_get_gps:
            def test(response):
                match = re.search(r'config,gps', response)
                if match:
                    return True
                return False

            def parse(response):
                match = re.search(
                    r'config,gps,(\w+),(\w+),(\d+\.\d+),(\w+),(\d+\.\d+)',
                    response)
                if match:
                    if match.group(1) != 'ok':
                        return None
                    return match.group(2, 3, 4, 5)
                return None

            self.__cmd_get_gps = Command(
                'config,get,gps\r\n', 60, test, parse)

        return self.__com.send(self.__cmd_get_gps)

    def __get_cell_location(self):
        if not self.__cmd_get_lbsloc:
            def test(response):
                match = re.search(r'config,lbsloc', response)
                if match:
                    return True
                return False

            def parse(response):
                match = re.search(
                    r'config,lbsloc,(\w+),(\d{3}\.\d{7}),(\d{3}\.\d{7})',
                    response)
                if match:
                    if match.group(1) != 'ok':
                        return None
                    return match.group(2, 3)
                return None

            self.__cmd_get_lbsloc = Command(
                'config,get,lbsloc\r\n', 60, test, parse)

        return self.__com.send(self.__cmd_get_lbsloc)

    def get_best_location(self):
        gps_location = self.__get_gps_location()
        if gps_location:
            return gps_location

        return self.__get_cell_location()

    def serv(self):
        threading.Thread(target=self.__com.loop_receive).start()
        threading.Thread(target=self.__com.loop_send).start()
        threading.Thread(target=self.__com.loop_alive_check).start()

        while True:
            if not self.__com.alive:
                break

            current_time = time.time()
            time_elapsed = current_time - self.__last_location_update_at
            if time_elapsed >= self.__location_update_interval:
                # TODO 可引入 卡尔曼滤波
                # TODO 可引入 地图匹配
                location = self.get_best_location()
                # if location != self.__last_location:
                self.__last_location = location
                self.__last_location_update_at = current_time
                # do something else

                if location:  # 动态调整更新间隔
                    self.__location_update_interval = 60
                else:
                    self.__location_update_interval = 60

            time.sleep(1)

    # def get_imei(self):
    #     self.__send('config,get,imei\r\n')

    # def parse_imei_response(self, response):
    #     match = re.search(r"config,imei,ok,(\d+)", response)
    #     if match:
    #         imei = match.group(1)  # 提取括号中的内容
    #         return imei
    #     else:
    #         return None

    # def get_csq(self):
    #     self.__send('config,get,csq\r\n')

    # def parse_csq_response(self, response):
    #     match = re.search(r"config,csq,ok,(\d+)", response)
    #     if match:
    #         csq = match.group(1)
    #         return csq
    #     else:
    #         return None

    # def set_lp(self):
    #     self.__send('config,get,lp\r\n')

    # def parse_lp_response(self, response):
    #     match = re.search(r"config,lp,ok,(\d+)", response)
    #     if match:
    #         lp = match.group(1)
    #         return lp
    #     else:
    #         return None

    # def get_gpsext(self):
    #     self.__send('config,get,gpsext\r\n')

    # def parse_gpsext_response(self, response):
    #     match = re.search(r"config,gpsext,ok,(\d+)", response)
    #     if match:
    #         gpsext = match.group(1)
    #         return gpsext
    #     else:
    #         return None

    # def get_vbatt(self):
    #     self.__send('config,get,vbatt\r\n')

    # def parse_vbatt_response(self, response):
    #     match = re.search(r"config,vbatt,ok,(\d+)", response)
    #     if match:
    #         vbatt = match.group(1)
    #         return vbatt
    #     else:
    #         return None
