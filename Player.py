"""
文件名：    Player.py
功  能：    游戏的用户类定义。
修改人：    杨彦军
修改日期：  2020.11.1
修改内容：  添加玩家输入GUI界面。
"""
from tkinter import *


class Player:
    def __init__(self, id):
        self.id = id  # int type

    def get_player_input(self):
        input_window = Tk()
        input_window.title('输入数字')
        Label(input_window, text=f'玩家 {self.id} ，请输入你的数字：').grid(row=0, column=0)
        num = StringVar()
        num.set('0')
        entry = Entry(input_window, width=8, textvariable=num)
        entry.grid(row=0, column=1)
        error_msg = StringVar('')
        Label(input_window, textvariable=error_msg).grid(row=1, column=0, columnspan=2)

        def get_entry():
            try:
                if 0 < float(num.get()) < 100:
                    input_window.destroy()
                    return
            except ValueError:
                pass
            error_msg.set('-非法输入，请重新输入-')

        Button(input_window, text='确认', command= get_entry).grid(row=2, column=0, columnspan=2)
        mainloop()
        return float(num.get())

    def get_id(self):
        return self.id
