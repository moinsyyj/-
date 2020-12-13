"""
文件名：    Network.py
功  能：    游戏网络层定义。server/Client模块。
修改人：    杨彦军
修改日期：  2020年11月28日
修改内容：  初版。
"""
import socket
import json
from threading import Thread, Semaphore, Event, RLock

SERVER_DEFAULT_PORT = 8721


def get_lan_ip() -> str:
    """
    获取本机局域网IP。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
    s.connect(('192.168.1.1', 80))
    ip_ = s.getsockname()[0]
    s.close()
    return ip_


def port_is_occupied(ip_: str, port_: int) -> bool:
    """
    检测ip:port是否被占用。
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
    try:
        s.connect((ip_, port_))
        occupied = True
    except ConnectionRefusedError:
        occupied = False
    finally:
        s.close()
    return occupied


def _send_data(target_socket: socket.socket, protocol, **kw):
    """
    向target_socket发送消息。协议规范参考CMD.protocol。
    """
    data = CMD.protocol[protocol].copy()
    data.update(kw)
    msg = {'CMD': protocol, 'DATA': data}
    msg = json.dumps(msg)
    target_socket.sendall(msg.encode())


def _recv_data(target_socket: socket.socket):
    """
    从target_socket接收消息 -> 可能出现json.decoder.JSONDecodeError
    """
    msg = target_socket.recv(1024)  # type: bytes
    msg = msg.decode()  # type: str  # json str
    msg = json.loads(msg)  # type: dict  # 如果Error可以使用 , strict=False 参数
    return msg


def _handle_message(data: dict, target_socket: socket.socket = None):
    """
    ！！！！！！这是一个测试功能
    """
    print(f'NOTICE: message from {target_socket.getpeername()} : {data["MESSAGE"]}')
    if target_socket is not None:
        _send_data(target_socket, CMD.MESSAGE, MESSAGE=socket.gethostname() + ' GOT YOUR MESSAGE!')


class Server:
    """
    网络层-服务器模块。GameBoard的所有属性初始化后才能实例化本类！

    启动方式：server.listen(target_port)
    """

    def __init__(self, client_number: int):
        self._CLIENT_NUMBER = client_number
        self._processed_client_number = 0
        self._CLIENT_CONNECTION_SEMAPHORE = Semaphore(self._CLIENT_NUMBER)  # 限流
        self._ip = get_lan_ip()  # type: str
        self._port = None
        self.server_socket = None
        self._conn_pool = dict.fromkeys(range(self._CLIENT_NUMBER))

        self._CLIENT_WRITE_LOCK = RLock()
        self._GAME_READ_INPUTS_EVENT = Event()
        self._SERVER_READ_RESULT_EVENT = Event()
        # 缓存的临时数据
        self._player_inputs = list(range(self._CLIENT_NUMBER))
        self._t_g_value = -50.0
        self._t_scores = []
        self._t_play_again = True

    def listen(self, target_port: int):
        """listen(target_port) -> (server_ip, listened_port)

        该函数用于启动服务器。

        输入想要服务器监听的端口；返回服务器局域网ip和服务器最终监听的端口。
        """
        self._port = target_port
        while port_is_occupied(self._ip, self._port):
            self._port += 1  # 如果端口被占用，就换一个端口
        if self.server_socket is not None:
            self.server_socket.close()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self._ip, self._port))
        self.server_socket.listen(3)  # 最大等待数（有很多人理解为最大连接数，其实是错误的）
        T_accept_client = Thread(target=self._client_acceptor)
        T_accept_client.setDaemon(True)
        T_accept_client.start()
        print(f"S-INFO: server start listen {self._ip}:{self._port}")
        return self.server_socket.getsockname()

    def _client_acceptor(self):
        """
        处理客户端连接请求。
        """
        while True:
            try:
                client, addr = self.server_socket.accept()  # 阻塞，等待客户端连接
            except OSError:
                break
            self._CLIENT_CONNECTION_SEMAPHORE.acquire()
            client_id = None
            # todo: self.conn_pool是关键资源！理论上不会出现找不到 None的情况，但实际上可能会有。
            for available_id, _ in self._conn_pool.items():  # 查找连接池中有无可用ID
                if _ is None:
                    self._conn_pool[available_id] = client
                    client_id = available_id
                    break
            print(f'S-INFO: Accept a new client ID{client_id}-{addr[0]}:{addr[1]}')
            # 给每个客户端创建一个独立的线程进行管理
            T_handle_client = Thread(target=self._client_handler, args=(client, client_id))
            T_handle_client.setDaemon(True)
            T_handle_client.start()

    def _client_cleaner(self, client_id: int):
        # todo: 可能会有KeyError
        client = self._conn_pool[client_id]
        if client is not None:
            client.close()
            self._conn_pool[client_id] = None
            print(f"S-INFO: Client {client_id} offline.")
            self._CLIENT_CONNECTION_SEMAPHORE.release()

    def server_exit(self):
        for _ in self._conn_pool:
            self._client_cleaner(_)
        self.server_socket.close()

    def _client_handler(self, client: socket.socket, client_id: int):
        """
        处理客户端消息。
        """
        # 第一次握手
        try:
            msg = _recv_data(client)
            assert CMD.C_JOIN == msg['CMD']
            # 向客户端返回注册的ID
            _send_data(client, CMD.S_JOIN, ID=client_id)
        except (json.decoder.JSONDecodeError, KeyError, AssertionError) as e:  # 不是从合法客户端发来的消息
            print(f'S-INFO: First handshake with Client {client_id} failed. \n\t\tError reported as ', repr(e))
            self._client_cleaner(client_id)
            return
        # 后续通讯
        while True:
            try:
                if not self._t_play_again:
                    break
                msg = _recv_data(client)
                assert CMD.C_INPUT == msg['CMD']
                self._handle_client_input(msg['DATA'], client)
            except AssertionError:  # 客户端发来的命令未在CMD中枚举
                print(f'S-EXCEPTION: Unable to parse command "{msg["CMD"]}" from Client {client_id}.')
            except ConnectionResetError:  # 客户端主动断开链接
                # todo: 怎样实现客户端重连？
                print(f'S-EXCEPTION: Client {client_id} forcibly closed an existing connection.')
                self._client_cleaner(client_id)
                break

    def get_player_inputs(self):
        self._GAME_READ_INPUTS_EVENT.wait()  # GameBoard等待所有玩家都上传输入。
        self._GAME_READ_INPUTS_EVENT.clear()  # GameBoard已完成读玩家输入。
        return self._player_inputs

    def send_result(self, g_value: float, scores: list, play_again: bool):
        self._t_g_value = g_value
        self._t_scores = scores
        self._t_play_again = play_again
        self._SERVER_READ_RESULT_EVENT.set()  # Server可以开始发送本轮结果了

    def _handle_client_input(self, data, client):
        client_id = data['ID']  # type: int
        player_input = data['VALUE']  # type: float
        with self._CLIENT_WRITE_LOCK:
            self._player_inputs[client_id] = player_input
            self._processed_client_number += 1
            if self._processed_client_number == self._CLIENT_NUMBER:  # 判断是否处理完了所有客户端
                self._GAME_READ_INPUTS_EVENT.set()  # GameBoard可以开始读玩家输入了

        self._SERVER_READ_RESULT_EVENT.wait()  # 等待GameBoard计算结果，调用server_can_read_result(g_value, scores):
        _send_data(client, CMD.S_INPUT, INPUTS=self._player_inputs, G=self._t_g_value,
                   SCORE=self._t_scores, AGAIN=self._t_play_again)  # 向客户端返回本轮游戏结果

        with self._CLIENT_WRITE_LOCK:
            self._processed_client_number -= 1
            if self._processed_client_number == 0:  # 判断是否处理完了所有客户端
                self._SERVER_READ_RESULT_EVENT.clear()  # Server已完成结果发送工作


class Client:
    """
    网络层-客户端模块。

    启动方式：Client.connect(server_ip, server_port)
    """

    def __init__(self):
        self.server_socket = None
        self.client_id = None

        self._GAME_READ_PLAYER_ID = Event()
        self._GAME_READ_RESULT = Event()

        self._player_inputs = None
        self._t_g_value = None
        self._t_scores = None
        self._t_play_again = True

    def connect(self, server_ip: str, server_port: int):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 第一次握手
        try:
            self.server_socket.connect((server_ip, server_port))  # 尝试连接server
            _send_data(self.server_socket, CMD.C_JOIN)
            msg = _recv_data(self.server_socket)
            assert CMD.S_JOIN == msg['CMD']
            self.client_id = msg['DATA']['ID']
            self._GAME_READ_PLAYER_ID.set()
        except (socket.gaierror, TypeError, ConnectionRefusedError,  # 连接时出错
                json.decoder.JSONDecodeError, KeyError, AssertionError) as e:  # 通信时出错，连上了错误的主机
            # todo: delete this
            print('\t\tError reported as ', repr(e))
            self.server_socket.close()
            raise ConnectionRefusedError('Server address Incorrect, check again.')  # 在主线程抛出异常
        T_handle_server = Thread(target=self._server_handler)
        T_handle_server.setDaemon(True)
        T_handle_server.start()

    def _server_handler(self):
        # 后续通讯
        while True:
            try:
                if not self._t_play_again:  # server发来消息，正常退出
                    self.server_socket.close()
                    break
                msg = _recv_data(self.server_socket)
                assert CMD.S_INPUT == msg['CMD']
                self._player_inputs = msg['DATA']['INPUTS']
                self._t_g_value = msg['DATA']['G']
                self._t_scores = msg['DATA']['SCORE']
                self._t_play_again = msg['DATA']['AGAIN']
                self._GAME_READ_RESULT.set()
            except AssertionError:  # 发来的命令未在CMD.exec中枚举
                print('C-EXCEPTION: Unable to parse command "{msg["CMD"]}".')
            except ConnectionResetError:  # 服务器异常退出，主线程无法感知
                print('C-EXCEPTION: Server forcibly closed an existing connection.')
                self._t_play_again = False
                self._t_g_value = -1  # 表示一个异常
                self._GAME_READ_RESULT.set()
                self.server_socket.close()
                break

    def send_input(self, value: float):
        _send_data(self.server_socket, CMD.C_INPUT, ID=self.client_id, VALUE=value)

    def get_player_id(self):
        self._GAME_READ_PLAYER_ID.wait()
        # _GAME_READ_PLAYER_ID不需要clear
        print(f'C-DEBUG: Player get client id as {self.client_id}')
        return self.client_id

    def get_round_result(self):
        self._GAME_READ_RESULT.wait()
        print('C-DEBUG: Player get result.')
        self._GAME_READ_RESULT.clear()
        return self._player_inputs, self._t_g_value, self._t_scores, self._t_play_again

    def send_message(self):
        """
        ！！！！！！这是一个测试功能
        """
        while True:
            msg = input("请输入要发送的信息:")
            _send_data(self.server_socket, CMD.MESSAGE, MESSAGE=msg)


class CMD:
    """
    通信协议类。

    exec绑定相关协议处理函数。protocol定义协议包含参数，使用dict：update(kwargs)规范化。
    """
    C_JOIN = 1000
    S_JOIN = 1010
    C_INPUT = 2000
    S_INPUT = 2010
    MESSAGE = 3000
    # 协议定义
    protocol = {
        C_JOIN: {
            'SEED': 12345  # 加密使用随机种子
        },
        S_JOIN: {
            'ID': -1  # 服务器分配给客户端的ID，-1表示失败
        },
        C_INPUT: {
            'ID': -1,  # 客户端的ID，注意不是玩家ID
            'VALUE': 50.0  # type: float  # 玩家的输入
        },
        S_INPUT: {
            'INPUTS': [],  # 所有玩家的输入
            'G': -1,  # 当前轮的G值
            'SCORE': [],  # 所有玩家的分数
            'AGAIN': True  # 是否继续游戏
        },
        MESSAGE: {
            'MESSAGE': 'Null Message.'  # message，虽然不知道有啥用
        }
    }


if __name__ == '__main__':
    import time
    while True:
        print('不能从这里运行。')
        time.sleep(1)
