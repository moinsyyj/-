import tkinter as tk


class ButtonHover(tk.Button):
    def __init__(self, master=None, cnf={}, **kw):
        super().__init__(master=master, cnf=cnf, **kw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, e):
        self['background'] = self['activebackground']

    def _on_leave(self, e):
        self['background'] = 'SystemButtonFace'


def none():
    pass


class InputFrame(tk.Frame):
    """
    组件：输入一个数字。
    """

    def __init__(self, master=None, hint_='hint_text', type_=str,
                 restrict_=lambda _: True, button_handler=none, cnf={}, **kw):
        super().__init__(master=master, cnf=cnf, **kw)
        self.value = None
        self.input_hint = tk.StringVar(value=hint_)
        self.target_type = type_
        self.judge_method = restrict_
        self.button_handler = button_handler

        self._create_widget()

    def _create_widget(self):
        tk.Label(self, textvariable=self.input_hint).grid(row=0, column=0, columnspan=2)
        self._input_entry = tk.Entry(self, width=18)
        self._input_entry.grid(row=1, column=0)
        self._submit_button = tk.Button(self, text='确认', command=self._get_entry)
        self._submit_button.grid(row=1, column=1)
        self._error_hint = tk.StringVar(value='')
        tk.Label(self, textvariable=self._error_hint).grid(row=2, column=0, columnspan=2)

    def _get_entry(self):
        try:
            input_value = self.target_type(self._input_entry.get())
            if self.judge_method(input_value):
                self.value = input_value
                self._error_hint.set('成功获取了你的输入')
                self.set_disable(True)
                self.button_handler()
                return
        except ValueError:
            pass
        self._error_hint.set('-非法输入，请重新输入-')

    def get(self):
        return self.value

    def set_disable(self, status: bool):
        if status:
            cmd = 'disabled'
        else:
            cmd = 'normal'
        self._input_entry['state'] = cmd
        self._submit_button['state'] = cmd


class StatusFrame(tk.Frame):
    def __init__(self, master=None, msg_='msg', cnf={}, **kw):
        super().__init__(master=master, cnf=cnf, **kw)
        self._status_msg = tk.StringVar(value=msg_)

        self.create_widget()

    def create_widget(self):
        tk.Label(self).grid(row=0, column=0)
        tk.Label(self, textvariable=self._status_msg).grid(row=1, column=0)
        tk.Label(self).grid(row=2, column=0, rowspan=3)

    def display_info(self, _info_msg='msg'):
        self._status_msg.set(_info_msg)
        pass


if __name__ == '__main__':
    root = tk.Tk()
    root.title("测试")

    # app = InputFrame(root, hint_="请输入一个数字", type_=int, restrict_=lambda x: x > 0)

    def b():
        global root
        # app2 = StatusFrame(root, msg_="Test")
        tk.Button(root, text='??????').grid(row=1, column=0)


    app = InputFrame(root, hint_="请输入房主IP", type_=str, button_handler=b)

    # app2.display_info("请等待其他玩家输入")
    app.grid(row=0, column=0)

    tk.mainloop()
    print(app.get())
