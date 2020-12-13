"""
文件名：    GameBoard.py
功  能：    游戏主界面类定义。
修改人：    杨彦军,尹鸿伟
修改日期：  2020.11.1
修改内容：  添加游戏GUI界面。
"""
import matplotlib.pyplot as plt
from tkinter import *
from Player import Player


class GameBoard:
    def __init__(self):
        self.playerNum = self.get_player_number()  # 玩家数量
        if 0 == self.playerNum:
            return
        self.players = []  # 存储实例化的玩家
        self.g_nums = []  # 存储每轮的G_num
        self.player_scores = {}  # int: [score, last_input] type， 存储玩家分数和最后一轮输入
        self.player_inputs = []  # [[], []] type， 存储玩家每轮输入
        for player_id in range(self.playerNum):  # 实例化玩家
            self.players.append(Player(player_id))
            self.player_scores[player_id] = [0, 0]
        self.start_round()

    def start_round(self):
        while True:
            self.get_player_input()
            keep_play = self.get_result()
            if 'n' == keep_play:
                break

    def get_player_input(self):
        inputs = []
        for player in self.players:
            player_input = player.get_player_input()
            self.player_scores[player.get_id()][1] = player_input  # 缓存玩家最后一轮输入
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
        result_window = Tk()
        result_window.title('本轮结束')
        Label(result_window, text='---Score Table---\n' +
                                  ''.join(f'玩家 {player_id} 当前分数 {self.player_scores[player_id][0]}\n'
                                          for player_id in self.player_scores)).grid(row=0, column=0)
        # todo: MATPLOTLIB FIGURE
        fig = plt.figure(figsize=(4, 4), tight_layout=True)
        plt.xlabel('Game Round')
        plt.ylabel('Number')
        plt.plot(self.g_nums, label='G-num', marker='o', ls=':')
        plt.plot(self.player_inputs, marker='x', ls='')
        plt.legend()
        plt.grid()
        # plt.savefig('temp.png')
        # Label(result_window, image=PhotoImage(file='temp.png')).grid(row=0, column=1)
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=result_window)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=1)
        plt.close()
        choice = StringVar()
        choice.set('n')

        def get_entry(c):
            choice.set(c)
            result_window.destroy()
            return

        Button(result_window, text='再玩一轮', command=lambda: get_entry('y')).grid(row=2, column=0, sticky=E)
        Button(result_window, text='结束游戏', command=lambda: get_entry('n')).grid(row=2, column=1, sticky=W)
        mainloop()
        return choice.get()

    def get_player_number(self):
        input_window = Tk()
        input_window.title('玩家数量')
        Label(input_window, text='本次游戏共有多少名玩家：').grid(row=0, column=0)
        num = StringVar()
        num.set('0')
        entry = Entry(input_window, width=8, textvariable=num)
        entry.grid(row=0, column=1)
        error_msg = StringVar('')
        Label(input_window, textvariable=error_msg).grid(row=1, column=0, columnspan=2)

        def get_entry():
            try:
                if 0 < int(num.get()):
                    input_window.destroy()
                    return
            except ValueError:
                pass
            error_msg.set('-非法输入，请重新输入-')

        Button(input_window, text='确认', command=get_entry).grid(row=2, column=0, columnspan=2)
        mainloop()
        return int(num.get())


# while True:
#     try:
#         playerNum = int(input('本次游戏共有多少名玩家：'))
#         break
#     except:
#         print('---Invalid input---')
# game = GameBoard(playerNum)
game = GameBoard()
