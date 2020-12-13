"""
文件名：    GameBoard.py
功  能：    游戏主界面类定义。
修改人：    杨彦军
修改日期：  2020.10.26
修改内容：  程序初始原型。
"""
import os
import matplotlib.pyplot as plt
from Player import Player


class GameBoard:
    def __init__(self, playerNum):
        self.playerNum = playerNum  # 玩家数量
        self.players = []           # 存储实例化的玩家
        self.g_nums = []            # 存储每轮的G_num
        self.player_scores = {}     # int: [score, last_input] type， 存储玩家分数和最后一轮输入
        self.player_inputs = []     # [[], []] type， 存储玩家每轮输入
        for player_id in range(self.playerNum):  # 实例化玩家
            self.players.append(Player(player_id))
            self.player_scores[player_id] = [0, 0]
        self.start_round()

    def start_round(self):
        while True:
            self.get_player_input()
            self.get_result()
            if 'n' == input('是否继续游戏（y/n）：'):
                break

    def get_player_input(self):
        inputs = []
        for player in self.players:
            player_input = player.get_player_input()
            self.player_scores[player.get_id()][1] = player_input    # 缓存玩家最后一轮输入
            inputs.append(player_input)
        # 计算G_num
        g = sum(inputs) / len(inputs) * 0.618
        self.g_nums.append(g)
        self.player_inputs.append(inputs)

    def get_result(self):
        temp_dic = {}
        # 计算绝对值阶段
        for player_id, player_input in self.player_scores.items():
            temp_dic[player_id] = abs(player_input[-1] - self.g_nums[-1])  # 用户输入与G值的绝对值
        temp_dic = sorted(temp_dic.items(), key=lambda x: x[1], reverse=False)  # 升序排序，返回的temp_dic [(id,abs),...] type
        # 计分阶段
        player_id, player_abs = temp_dic[0]
        for player in temp_dic:  # player (id,abs) type， 遍历查找是否有相同绝对值
            if player_abs != player[1]:
                break
            self.player_scores[player[0]][0] += self.playerNum  # 加N分

        player_id, player_abs = temp_dic[-1]
        for player in temp_dic[::-1]:  # 逆序列表来找绝对值最大的
            if player_abs != player[1]:
                break
            self.player_scores[player[0]][0] += -2  # 加-2分
        # matplotlib展示阶段
        os.system("cls")
        print('\b', end='')
        # 显示分数表
        print('---Score Table---')
        for player_id in self.player_scores:
            print('玩家 {} 当前分数 {}'.format(player_id, self.player_scores[player_id][0]))
        # 显示matplotlib图表
        # TODO: 完善matplotlib展示
        plt.figure()
        plt.xlabel('Game Round')
        plt.ylabel('Number')
        plt.plot(self.g_nums, label='G-num', marker='o', ls=':')
        plt.plot(self.player_inputs, marker='x', ls='')
        plt.legend()
        plt.grid()
        plt.show()

        pass


while True:
    try:
        playerNum = int(input('本次游戏共有多少名玩家：'))
        break
    except:
        print('---Invalid input---')
game = GameBoard(playerNum)
