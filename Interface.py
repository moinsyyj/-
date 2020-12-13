import tkinter as tk
import GUIutil as tk2
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from threading import Thread, Event
import GameBoard


class Interface:
    def __init__(self):
        self.GAME_MODE = None  # 's'表示服务器 or 'c'表示客户端
        self.player = GameBoard.Player()
        self._server_addr = None
        self.game_round = 0

        self._RECV_RESULT_FINISHED = Event()
        # GUI布局
        self.root = tk.Tk()
        self.start_frame = None
        self.input_frame = None  # type: tk2.InputFrame
        self.game_frame = None
        self._goto_start()

    def _init_server(self):
        """
        如果是房主模式，初始化服务器再初始化客户端（加入游戏）。
        """
        player_number = self.input_frame.get()  # type: int
        self.game_board = GameBoard.GameBoard(player_number)
        self._server_addr = self.game_board.get_server_address()
        self.game_board.start()
        messagebox.showinfo(message=f'请将下列地址告诉其他玩家。\n{self._server_addr[0]}:{self._server_addr[1]}')
        self._join_game()

    def _join_game(self):
        """
        初始化客户端。
        """
        if self._server_addr is None:  # 说明不是房主模式，房主模式在初始化服务器时已获得服务器地址
            addr_ = self.input_frame.get().split(':')
            self._server_addr = (addr_[0], int(addr_[1]))
        try:
            self.player.connect(self._server_addr[0], self._server_addr[1])
        except (ConnectionRefusedError, TimeoutError):
            # todo: messagebox
            messagebox.showerror(title='ConnectionRefusedError', message='Can not connect to server, check again.')
            self.input_frame.set_disable(False)
            return
        # 成功加入游戏，进入游戏界面
        self._goto_game()

    def _goto_start(self):
        self.root.title('选择模式')
        # 初始化frame
        self.start_frame = tk.Frame(self.root)
        tk2.ButtonHover(self.start_frame, text='创建房间', command=lambda: self._goto_input('s'),
                        font=('黑体', 20, 'bold'), height=3, width=20, activebackground='gold').grid(row=0, column=0)
        tk2.ButtonHover(self.start_frame, text='加入房间', command=lambda: self._goto_input('c'),
                        font=('黑体', 20, 'bold'), height=3, width=20, activebackground='gold').grid(row=1, column=0)
        self.start_frame.grid()

    def _goto_input(self, game_mode):
        self.GAME_MODE = game_mode
        self.start_frame.destroy()
        # 初始化frame
        if self.GAME_MODE == 's':
            self.root.title("服务器")
            self.input_frame = tk2.InputFrame(self.root, hint_="请输入玩家数量", type_=int,
                                              restrict_=lambda x: 0 < x < 100, button_handler=self._init_server)
        else:
            self.root.title("客户端")
            # todo:针对网址的restrict_没有写
            self.input_frame = tk2.InputFrame(self.root, hint_="请输入房主的地址", type_=str,
                                              button_handler=self._join_game)
        self.input_frame.grid()

    def _goto_game(self):
        self.input_frame.destroy()
        # 初始化frame
        self.game_frame = tk.Frame(self.root)
        # 0,0 玩家输入窗口
        player_id = self.player.get_player_id()
        self.input_frame = tk2.InputFrame(self.game_frame, hint_=f"玩家{player_id}：请输入你的数字", type_=float,
                                          restrict_=lambda x: 0 < x < 100, button_handler=self._send_input)
        self.input_frame.grid(row=0, column=0)
        # 0,1 游戏状态提示
        self._net_state = tk.StringVar(value='---欢迎加入游戏---')
        tk.Label(self.game_frame, textvariable=self._net_state,  font=("微软雅黑", 20, "bold")).grid(row=0, column=1)
        # 1,0 显示成绩表
        self._score_table = ttk.Treeview(self.game_frame, show='headings', columns=("ID", "score"))
        self._score_table.column("ID", width=75)  # 设置列
        self._score_table.column("score", width=75)
        self._score_table.heading("ID", text="ID")  # 设置显示的表头名
        self._score_table.heading("score", text="分数")
        self._score_table.grid(row=1, column=0)
        # 1,1 matplotlib可视化结果
        fig = plt.figure(figsize=(4, 4), tight_layout=True)
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        self.canvas = FigureCanvasTkAgg(fig, master=self.game_frame)
        self.canvas.get_tk_widget().grid(row=1, column=1)
        self.ax = fig.add_subplot()
        self.ax.set_title('Result')
        self.ax.plot([], 'o:y', label='G-num')  # 用于生成第一次图例
        self.ax.set_xticks((0,))
        self.ax.set_xticklabels(('R1',))
        self.ax.legend()  # 图例
        self.ax.grid()  # 网格线
        self.canvas.draw()
        plt.close()

        self.game_frame.grid()
        self.root.mainloop()

    def _send_input(self):
        player_input = self.input_frame.get()
        self.player.send_input(player_input)
        self._net_state.set('---正在等待服务器返回结果---')
        T_result = Thread(target=self._recv_result_thread)
        T_result.setDaemon(True)
        T_result.start()
        self.root.after(2000, self._recv_result_main)

    def _recv_result_main(self):
        if self._RECV_RESULT_FINISHED.is_set():
            self._RECV_RESULT_FINISHED.clear()
            self.game_round += 1
            # 1.判定g是否非负. _g_value = -1 时表示抛弃本轮结果，异常退出游戏
            g_value = self.player.get_g()[-1]
            if g_value == -1:
                messagebox.showinfo(title="游戏发生异常", message="由于服务器异常退出，程序将在确认后退出。")
                self.root.after(3000, self.root.destroy)
                return
            # 3.利用score更新分数表
            for _ in self._score_table.get_children():
                self._score_table.delete(_)
            for id_, score_ in zip(range(len(self.player.get_last_score())), self.player.get_last_score()):
                self._score_table.insert('', 'end', values=(id_, score_))
            # 4.利用g inputs更新分数表
            for _ in self.ax.get_lines():
                _.remove()
            self.ax.plot(self.player.get_g(), 'o:y', label='G-num')
            self.ax.plot(self.player.get_input(), 'x', linestyle='')
            self.ax.text(self.game_round-1, g_value + 0.2, '%.0f' % g_value, ha='center', va='bottom')
            self.ax.set_xticks(list(range(self.game_round+1)))
            self.ax.set_xticklabels(['R%d' % (1 + _) for _ in range(self.game_round+1)])
            self.canvas.draw()
            # 2.判定play_again. False时表示显示本轮结果，正常退出游戏
            if not self.player.is_play_again():
                messagebox.showinfo(title="游戏结束", message="游戏结束了，程序将在确认后退出。")
                self.root.after(3000, self.root.destroy)
                return

            self._net_state.set(f'---第 {self.game_round} 轮结果如下---')
            self.input_frame.set_disable(False)
        else:
            print('C-DEBUG: def _recv_result_main: result is not ready.')
            self.root.after(2000, self._recv_result_main)

    def _recv_result_thread(self):
        self.player.get_round_result()  # 阻塞至成功获取本轮结果
        self._RECV_RESULT_FINISHED.set()

    def launch(self):
        self.root.mainloop()


if '__main__' == __name__:
    game = Interface()
    game.launch()
