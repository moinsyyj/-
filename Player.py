"""
文件名：    Player.py
功  能：    游戏的用户类定义。
修改人：    杨彦军
修改日期：  2020.10.26
修改内容：  程序初始原型。
"""


class Player:
    def __init__(self, id):
        self.id = id  # int type

    def get_player_input(self):
        while True:
            try:
                num = float(input('玩家 {} ，请输入你的数字：'.format(self.id)))
                if 0 < num < 100:
                    return num
            except:
                pass
            print('---Invalid input---')

    def get_id(self):
        return self.id
