"""
文件名：    GameBoard.py
功  能：    游戏数据层定义。GameBoard/Player模块。
修改人：    杨彦军
修改日期：  2020年11月29日
修改内容：  将数据交流拆分到网络层，将GUI拆分到界面层。
"""
from threading import Thread

import Network

SERVER_DEFAULT_PORT = 8721


class GameBoard:
    def __init__(self, player_number: int):
        self._PLAYER_NUMBER = player_number  # 玩家数量
        self.server = Network.Server(self._PLAYER_NUMBER)
        self._server_started = False
        self._server_addr = None

        self.g_nums = []  # 存储每轮的G_num
        self.player_scores_all = [[0 for _ in range(player_number)]]  # [round][player_id]二维数组，存储玩家分数
        self.player_inputs_all = []  # [round][player_id]二维数组，存储玩家每轮输入

    def get_server_address(self):
        if not self._server_started:
            self._server_addr = self.server.listen(SERVER_DEFAULT_PORT)  # (ip, port)
            self._server_started = True
        return self._server_addr

    def start(self):
        if not self._server_started:
            self.get_server_address()
        T_server = Thread(target=self._start)
        T_server.setDaemon(True)
        T_server.start()

    def _start(self):
        while True:
            # 获取输入
            inputs = self._get_player_input()
            # 计算G值
            g_value = self._calculate_g(inputs)
            # 计算成绩
            scores = self._calculate_scores(inputs)
            # 是否继续游戏
            play_again = self._get_play_again_choice()
            # 发送结果
            self.server.send_result(g_value, scores, play_again)
            if not play_again:
                self.game_exit()
                break

    def game_exit(self):
        import time
        time.sleep(5)
        self.server.server_exit()
        # todo: 保存self.g_nums self.player_scores_all self.player_inputs_all

    def _get_player_input(self) -> list:
        inputs = self.server.get_player_inputs()
        self.player_inputs_all.append(inputs)
        return inputs

    def _calculate_g(self, inputs: list) -> float:
        g = sum(inputs) / len(inputs) * 0.618
        self.g_nums.append(g)
        return g

    def _calculate_scores(self, inputs: list) -> list:
        # 计算绝对值阶段
        t_inputs = dict(zip(range(self._PLAYER_NUMBER), inputs))
        g_value = self.g_nums[-1]
        for id_, input_ in t_inputs.items():
            t_inputs[id_] = abs(input_ - g_value)  # 用户输入与G值的绝对值
        t_inputs = sorted(t_inputs.items(), key=lambda x: x[1], reverse=False)  # 升序排序，返回[(id,abs),]
        # 计分阶段
        t_scores = dict(zip(range(self._PLAYER_NUMBER), self.player_scores_all[-1]))
        id_, input_ = t_inputs[0]  # 这里的input_其实是绝对值
        for player in t_inputs:  # player (id,abs)， 遍历查找是否有相同绝对值
            if input_ != player[1]:
                break
            t_scores[player[0]] += self._PLAYER_NUMBER  # 加N分
        id_, input_ = t_inputs[-1]
        for player in t_inputs[::-1]:  # 逆序找绝对值最大的
            if input_ != player[1]:
                break
            t_scores[player[0]] += -2  # 加-2分
        # append
        t_scores = list(t_scores.values())  # dict转list
        self.player_scores_all.append(t_scores)
        return t_scores

    @staticmethod
    def _get_play_again_choice() -> bool:
        from tkinter import messagebox
        choice = messagebox.askyesno(title='继续游戏？', message='您是房主，请决定是否继续游戏。')
        return choice


class Player:
    def __init__(self):
        self.player_id = None  # int
        self.client = Network.Client()  # 客户端

        self.g_nums = []  # 存储每轮的G_num
        self.player_scores_all = []  # [round][player_id]二维数组，存储玩家分数
        self.player_inputs_all = []  # [round][player_id]二维数组，存储玩家每轮输入
        self.play_again = True

    def connect(self, server_ip: str, server_port: int):
        self.client.connect(server_ip, server_port)

    def send_input(self, value: float):
        self.client.send_input(value)

    def get_player_id(self):
        if self.player_id is None:
            self.player_id = self.client.get_player_id()
        return self.player_id

    def get_round_result(self):
        """
        g_value = -1表示出现了异常
        """
        player_inputs, g_value, scores, play_again = self.client.get_round_result()
        self.player_inputs_all.append(player_inputs)
        self.g_nums.append(g_value)
        self.player_scores_all.append(scores)
        self.play_again = play_again

    def get_last_score(self):
        return self.player_scores_all[-1]

    def get_input(self):
        return self.player_inputs_all

    def get_g(self):
        return self.g_nums

    def is_play_again(self):
        return self.play_again


if __name__ == '__main__':
    import time
    while True:
        print('不能从这里运行。')
        time.sleep(1)

