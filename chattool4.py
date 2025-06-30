import asyncio
import json
import os
import re
import warnings
from datetime import datetime
from urllib.parse import quote

import markdown
import wx
import wx.html2

from kimiChatClient import KimiChatClient
from settingsDialog import SettingsDialog

# 忽略特定的警告
# warnings.filterwarnings("ignore", message="iCCP: known incorrect sRGB profile")
# warnings.filterwarnings("ignore", message="iCCP: cHRM chunk does not match sRGB")


class MyFrame(wx.Frame):
    def __init__(self):
        # 加载配置文件
        self.config = load_config()
        print(self.config)
        self.htmlFile = "chat.html"

        self.loading_chat = False

        # 根据配置文件设置窗口的位置和大小
        position = self.config.get("position", (100, 100))
        size = self.config.get("size", (800, 600))
        version = self.config.get("version", "1.0")
        self.selectedlang = self.config.get("lang", "en")
        self.lang = load_lang(self.selectedlang)
        super().__init__(None, title="Ai Agent v" + version, pos=wx.Point(position), size=wx.Size(size))
        self.Bind(wx.EVT_PAINT, self.onPaint)

        self.SetIcon(wx.Icon('./icons/app_icon.ico', wx.BITMAP_TYPE_ICO))
        # 设置窗口的最小尺寸
        self.SetMinSize(wx.Size(700, 500))

        self.main_splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.left_panel = wx.Panel(self.main_splitter, style=wx.BORDER_THEME)

        self.chat_data = load_chat_data()

        # 绑定分隔条事件
        self.main_splitter.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.on_sash_changed)

        # 设置左侧部分的最小宽度
        self.main_splitter.SetMinimumPaneSize(224)

        # self.splitter.SetMinimumPaneSize(20)

        # 左侧工具栏
        self.left_toolbar = wx.BoxSizer(wx.HORIZONTAL)
        self.save_button = wx.Button(self.left_panel, label=self.lang.get("save"), size=wx.Size(45, 22))
        self.load_button = wx.Button(self.left_panel, label=self.lang.get("reload"), size=wx.Size(45, 22))
        self.setting_button = wx.Button(self.left_panel, label=self.lang.get("settings"), size=wx.Size(55, 22))
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save)
        self.load_button.Bind(wx.EVT_BUTTON, self.on_load)
        self.setting_button.Bind(wx.EVT_BUTTON, self.on_setting)
        # 将按钮添加到工具栏
        self.left_toolbar.Add(self.save_button, 0, wx.ALL, 0)
        self.left_toolbar.Add(self.load_button, 0, wx.ALL, 0)
        self.left_toolbar.Add(self.setting_button, 0, wx.ALL, 0)
        # 左侧列表框
        # self.list_box = wx.CheckListBox(self.left_panel, choices=[], style=wx.BORDER_STATIC)
        self.list_box = wx.ListBox(self.left_panel, choices=[], style=wx.BORDER_STATIC)
        # self.list_box.Bind(wx.EVT_CHECKLISTBOX, self.on_check)
        self.list_box.Bind(wx.EVT_LISTBOX, self.on_listbox_select)
        self.fill_listbox()

        # 左侧布局
        left_sizer = wx.BoxSizer(wx.VERTICAL)
        left_sizer.Add(self.left_toolbar, 0, wx.ALL | wx.EXPAND, 5)
        left_sizer.Add(self.list_box, 1, wx.ALL | wx.EXPAND, 5)
        self.left_panel.SetSizer(left_sizer)

        # 根据配置文件设置左侧部分的宽度和是否显示
        left_width = self.config.get("left_width", 288)
        show_left = self.config.get("show_left", True)

        # 右侧
        self.right_panel = wx.Panel(self.main_splitter, style=wx.BORDER_THEME)
        self.right_splitter = wx.SplitterWindow(self.right_panel, style=wx.SP_LIVE_UPDATE)

        self.right_main_panel = wx.Panel(self.right_splitter, style=wx.NO_BORDER)
        self.right_main_sizer = wx.BoxSizer(wx.VERTICAL)
        # self.send_panel = wx.Panel(self.splitter1, style=wx.BORDER_THEME)
        # 右侧左上角切换按钮
        self.toggle_button = wx.Button(self.right_main_panel, label="", size=wx.Size(16, 16), style=wx.NO_BORDER)
        self.toggle_button.Bind(wx.EVT_BUTTON, self.on_toggle)
        self.toggle_button.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_toggle_button)
        self.toggle_button.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_toggle_button)
        self.toggle_button.SetCursor(wx.Cursor(wx.CURSOR_HAND))
        self.toggle_button.SetBackgroundColour(wx.NullColour)

        # self.splitter.Initialize(self.right_panel)
        # sys.stdout.write('L28 show_left=' + str(show_left) + '\n')
        if show_left:
            self.main_splitter.SplitVertically(self.left_panel, self.right_panel, sashPosition=left_width)
            self.toggle_button.SetBitmap(wx.BitmapBundle(wx.Bitmap("icons/hide_icon1.png", wx.BITMAP_TYPE_ANY)))
        else:
            self.main_splitter.Initialize(self.right_panel)
            self.main_splitter.Unsplit(self.left_panel)
            self.toggle_button.SetBitmap(wx.BitmapBundle(wx.Bitmap("icons/show_icon1.png", wx.BITMAP_TYPE_ANY)))
            self.left_panel.Hide()

        # 当前会话名称
        self.session_label = wx.StaticText(self.right_main_panel, label=datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                                           style=wx.ALIGN_CENTER)
        self.session_label.Bind(wx.EVT_LEFT_DCLICK, self.on_session_label_dclick)
        # self.session_label.SetMinSize(wx.Size(80, -1))

        # 新增的图标按钮
        self.new_button = wx.Button(self.right_main_panel, label="", size=wx.Size(20, 20), style=wx.NO_BORDER)
        self.new_button.SetBitmap(wx.BitmapBundle(wx.Bitmap("icons/new_icon1.png", wx.BITMAP_TYPE_ANY)))
        self.new_button.Bind(wx.EVT_BUTTON, self.on_new_button_click)
        self.new_button.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_new_button)
        self.new_button.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_new_button)
        self.new_button.SetCursor(wx.Cursor(wx.CURSOR_HAND))

        right_main_toolbar = wx.BoxSizer(wx.HORIZONTAL)
        right_main_toolbar.Add(self.toggle_button, 0, wx.ALL, 1)
        right_main_toolbar.AddStretchSpacer()
        right_main_toolbar.Add(self.session_label, 1, wx.EXPAND | wx.ALL, 1)
        right_main_toolbar.AddStretchSpacer()
        right_main_toolbar.Add(self.new_button, 0, wx.ALL, 1)

        # HTML 显示控件
        self.webview = wx.html2.WebView.New(parent=self.right_main_panel, name="")
        self.load_html_page()

        self.right_main_sizer.Add(right_main_toolbar, 0, wx.EXPAND | wx.ALL, 5)
        self.right_main_sizer.Add(self.webview, 1, wx.EXPAND | wx.ALL, 1)
        self.right_main_panel.SetSizer(self.right_main_sizer)

        # 文本输入框
        self.bottom_panel = wx.Panel(self.right_splitter)
        self.text_input = wx.TextCtrl(self.bottom_panel, style=wx.TE_MULTILINE | wx.BORDER_THEME, size=wx.Size(-1, 100))
        self.text_input.SetMinSize(wx.Size(-1, 100))  # 设置最小高度为5行
        # 发送按钮
        self.send_button = wx.Button(self.bottom_panel, label=self.lang.get("send"))
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_sync)

        right_bottom_sizer = wx.BoxSizer(wx.VERTICAL)
        right_bottom_sizer.Add(self.text_input, 1, wx.EXPAND | wx.ALL, 1)
        right_bottom_sizer.Add(self.send_button, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.bottom_panel.SetSizer(right_bottom_sizer)

        right_panel_sizer = wx.BoxSizer(wx.VERTICAL)
        right_panel_sizer.Add(self.right_splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.right_panel.SetSizer(right_panel_sizer)

        # 分割右侧窗口
        self.right_splitter.SplitHorizontally(self.right_main_panel, self.bottom_panel, sashPosition=550)
        self.right_splitter.SetMinimumPaneSize(150)

        # 设置主面板布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.main_splitter, 1, wx.EXPAND | wx.ALL, 5)
        self.SetSizer(sizer)

        # 缓存保存位置
        self.cache_dir = self.config.get("cache_dir", "./cache")
        # print(f"Cache directory: {self.cache_dir}")

        # 动态调整会话名称 label 的宽度
        self.Bind(wx.EVT_SIZE, self.on_size)
        #self.on_size(None)
        self.Refresh()

        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.kimi_client = KimiChatClient()

        self.session_id = None
        self.current_chat = []

    def onPaint(self, event):
        dc = wx.PaintDC(self)
        rect = self.GetClientRect()
        dc.SetPen(wx.Pen(wx.Colour('#eee'), 5))  # 设置边框颜色和宽度
        dc.DrawRectangle(rect)

    def on_sash_changed(self, event):
        # 获取当前分隔条的位置
        sash_position = self.main_splitter.GetSashPosition()
        # 如果左侧宽度小于224，则自动调整为224
        if sash_position < 224:
            self.main_splitter.SetSashPosition(224)
        if sash_position >= 224:
            self.config["left_width"] = sash_position
        # self.setSessionLabelSize()

    def save_config(self):
        try:
            with open('config.json', 'r', encoding="utf-8") as f:
                current_config = json.load(f)
        except FileNotFoundError:
            current_config = {}
        current_config["position"] = self.GetPosition().Get()
        current_config["size"] = self.GetSize().Get()
        current_config["left_width"] = self.config.get('left_width', 224)
        current_config["show_left"] = self.config.get("show_left", True)
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(current_config, f, indent=4)

    def on_toggle(self, event):
        if self.main_splitter.IsSplit():
            # self.config["left_width"] = self.splitter.GetSashPosition()
            self.main_splitter.Unsplit(self.left_panel)
            self.toggle_button.SetBitmap(wx.BitmapBundle(wx.Bitmap("icons/show_icon1.png", wx.BITMAP_TYPE_ANY)))
            # 更新配置文件中的 show_left 状态
            self.config["show_left"] = False
        else:
            left_width = self.config.get("left_width", 224)
            if left_width < 224:
                left_width = 224

            self.main_splitter.SplitVertically(self.left_panel, self.right_panel, sashPosition=left_width)
            self.toggle_button.SetBitmap(wx.BitmapBundle(wx.Bitmap("icons/hide_icon1.png", wx.BITMAP_TYPE_ANY)))
            # 更新配置文件中的 show_left 状态
            self.config["show_left"] = True
        # self.setSessionLabelSize()

    # def on_check(self, event):
    #     # 复选框选中状态改变时的处理
    #     pass

    def on_save(self, event):
        # 保存按钮点击事件处理
        if self.session_id is None or self.session_id == '':
            wx.MessageBox("还未开始会话，请稍后再保存", "提示")
            return
        self.save_current_chat_data()
        self.session_id = ''
        self.current_chat = []
        load_chat_data()
        self.fill_listbox()
        self.load_html_page()

    def on_load(self, event):
        # 加载按钮点击事件处理
        self.save_current_chat_data()
        self.session_id = ''
        self.session_label.SetLabel(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        self.current_chat = []
        load_chat_data()
        self.fill_listbox()
        self.load_html_page()

    def on_setting(self, event):
        dialog = SettingsDialog(self)
        if dialog.ShowModal() == wx.ID_OK:
            print("Settings saved:")
            self.config = load_config()
            self.Refresh()
        dialog.Destroy()

    def center_on_parent(self, dialog):
        # 计算主窗口的中心位置
        main_x, main_y = self.GetPosition()
        main_width, main_height = self.GetSize()
        dialog_width, dialog_height = dialog.GetSize()

        # 设置对话框的位置
        dialog_x = main_x + (main_width - dialog_width) // 2
        dialog_y = main_y + (main_height - dialog_height) // 2
        dialog.SetPosition((dialog_x, main_y + 100))

    def on_close(self, event):
        # 保存配置
        self.save_config()
        if self.session_id and self.current_chat:
            self.save_current_chat_data()
        # 关闭窗口
        event.Skip()

    def on_size(self, event):
        # 动态调整会话名称 label 的宽度
        # self.setSessionLabelSize()
        self.Refresh()
        if event:
            event.Skip()

    # def setSessionLabelSize(self):
    #     right_panel_size = self.right_panel.GetSize()
    #     toggle_button_size = self.toggle_button.GetSize()
    #     new_button_size = self.new_button.GetSize()
    #     label_width = right_panel_size.width - toggle_button_size.width - new_button_size.width - 40  # 减去一些间距
    #     self.session_label.SetMinSize(wx.Size(label_width, -1))
    #     self.session_label.SetMaxSize(wx.Size(label_width, -1))
    #     self.session_label.Wrap(label_width)
    #     self.right_panel.Layout()
    def on_session_label_dclick(self, event):
        # 弹出包含文本框的对话框
        current_label = self.session_label.GetLabel()
        dialog = wx.TextEntryDialog(self, "编辑会话标题", "编辑", current_label)
        if dialog.ShowModal() == wx.ID_OK:
            new_label = dialog.GetValue()
            self.session_label.SetLabel(new_label)
            #print(self.current_chat)
            #self.current_chat['title'] = new_label
            # 更新左侧会话列表中选中项的条目内容
            selected_index = self.list_box.GetSelection()
            if selected_index != wx.NOT_FOUND:
                self.list_box.SetString(selected_index, new_label)
                # session_id = self.list_box.GetClientData(selected_index)
                # chat = self.find_chat_by_session_id(session_id)
                # if chat:
                #     chat['title'] = new_label
                #     self.list_box.SetString(selected_index, new_label)
                #     self.save_chat_data()  # 保存更新后的会话数据
        dialog.Destroy()

    async def on_send(self):
        # 发送按钮点击事件处理
        text = self.text_input.GetValue().strip()
        if text == '':
            wx.MessageBox("请输入聊天内容", "提示", parent=self)
            return
        print(f"发送内容: {text}")
        createTime = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        if self.htmlFile == 'welcome.html':
            self.htmlFile = 'chat.html'
            self.load_html_page()
        try:
            me_count = len([message for message in self.current_chat if message.get('from') == 'me'])
            self.webview.RunScript("addChatContent('me','" + quote(text) + "'," + str(me_count + 1) + ")")
            self.webview.RunScript("todown()")
            self.send_button.Disable()
            response = await self.kimi_client.chat(text, self.session_id, self.loading_chat, self.current_chat)
            # response = '常规回复'
            print(response)
            print(f"接收内容：{response['content']}")
            markdownStr = parseCode(response['content'])
            # self.webview.RunScript("addChatContent('bot','" + quote(markdown.markdown(response)) + "')")
            print(f"转换后回复：" + markdownStr)
            self.webview.RunScript("addChatContent('bot','" + quote(markdown.markdown(markdownStr)) + "')")
            self.text_input.Clear()
            self.send_button.Enable()
            if self.session_id is None or self.session_id == '':
                self.session_id = response['session_id']
            # if response['title'] is not None:
            #     self.session_label.SetLabel(response['title'])
            self.current_chat.append({
                "from": "me",
                "createTime": createTime,
                "title": self.session_label.GetLabel(),
                "message": text
            })
            self.current_chat.append({
                "from": "bot",
                "createTime": datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                "title": self.session_label.GetLabel(),
                "message": response['content']
            })
            self.webview.RunScript("addMyChatList(" + str(me_count + 1) + ",'" + quote(text) + "')")
            self.webview.RunScript("todown()")

        except Exception as e:
            print(f"发生错误：{e}")
        # self.text_input.Clear()

    def on_send_sync(self, event):
        asyncio.run(self.on_send())

    def on_new_button_click(self, event):
        self.save_current_chat_data()
        self.session_id = ''
        self.session_label.SetLabel(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))
        self.current_chat = []
        load_chat_data()
        self.fill_listbox()
        self.load_html_page()

    def on_enter_toggle_button(self, event):
        # 鼠标悬停时改变背景色
        self.toggle_button.SetBackgroundColour(wx.Colour(173, 216, 230))  # 浅蓝色
        self.toggle_button.Refresh()

    def on_leave_toggle_button(self, event):
        # 鼠标离开时恢复默认背景色
        self.toggle_button.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.toggle_button.Refresh()

    def on_enter_new_button(self, event):
        # 鼠标悬停时改变背景色
        self.new_button.SetBackgroundColour(wx.Colour(173, 216, 230))  # 浅蓝色
        self.new_button.Refresh()

    def on_leave_new_button(self, event):
        # 鼠标离开时恢复默认背景色
        self.new_button.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        self.new_button.Refresh()

    def load_html_page(self):
        try:
            html_file = os.path.join(os.getcwd(), "template", self.htmlFile)
            self.webview.LoadURL(f"file://{html_file}")
        except Exception as e:
            print(f"Error loading HTML file: {e}")
            html_content = """<html> <body style='margin:0;padding:0;display:flex;justify-content:center;align-items
            :center;height:100%;'> <div style='text-align:center;'> <h1>Welcome</h1> </div> </body> </html>"""
            self.webview.SetPage(html_content, "")

    def fill_listbox(self):
        self.list_box.Clear()
        for chat in reversed(self.chat_data):
            self.list_box.Append(chat['title'], chat['session_id'])

    def save_chat_data(self):
        # print("L408 self.chat_data=" + self.chat_data)
        with open("chat.json", "w", encoding="utf-8") as file:
            json.dump(self.chat_data, file, ensure_ascii=False, indent=4)

    def find_chat_by_session_id(self, session_id):
        return next((chat for chat in self.chat_data if chat['session_id'] == session_id), None)

    def on_listbox_select(self, event):
        selected_index = event.GetSelection()
        if selected_index == wx.NOT_FOUND:
            return
        session_id = self.list_box.GetClientData(selected_index)
        if session_id == self.session_id:
            return
        chat = self.find_chat_by_session_id(session_id)
        if chat is None:
            return
        # 如果 self.session_id 不为空，且 self.current_chat 不为空，则保存 self.current_chat 及 self.session_id 到 self.chat_data
        if self.session_id and self.current_chat:
            self.save_current_chat_data()
            self.chat_data = load_chat_data()  # 重新读取 chat.json
        self.display_chat(chat)

    def save_current_chat_data(self):
        if self.session_id is None or self.session_id == '':
            return
        if self.current_chat is None:
            return
        title = self.session_label.GetLabel()
        if title == '':
            title = self.current_chat[0]['createTime']
        if not self.chat_data:
            self.chat_data.append({
                'session_id': self.session_id,
                'title': title,
                'startTime': self.current_chat[0]['createTime'],
                'chats': self.current_chat
            })
        else:
            current_chat_index = next(
                (i for i, c in enumerate(self.chat_data) if c.get('session_id') == self.session_id), None)

            if current_chat_index is not None:
                self.chat_data[current_chat_index]["title"] = self.session_label.GetLabel()
                self.chat_data[current_chat_index]["updateTime"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
                self.chat_data[current_chat_index]["chats"] = self.current_chat
            else:
                self.chat_data.append({
                    'session_id': self.session_id,
                    'title': title,
                    'startTime': self.current_chat[0]['createTime'],
                    'chats': self.current_chat
                })
        self.save_chat_data()  # 保存到 chat.json

    def display_chat(self, chat):
        html_file = os.path.join(os.getcwd(), "template", "chat.html")
        self.webview.LoadURL(f"file://{html_file}")
        # 等待页面加载完成
        self.webview.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.on_webview_loaded)
        self.session_label.SetLabel(chat['title'])
        self.session_id = chat['session_id']
        self.current_chat = chat['chats']
        self.loading_chat = True

    def on_webview_loaded(self, event):
        if self.current_chat:
            self.update_chat_content(self.current_chat)
        self.webview.Unbind(wx.html2.EVT_WEBVIEW_LOADED, handler=self.on_webview_loaded)

    def update_chat_content(self, chats):
        i = 0
        # print("L483 before put chats to webview")
        for chat in chats:
            message = parseCode(chat['message'])
            # message = quote(markdown.markdown(parseCode(chat['message'])))
            if chat['from'] == 'me':
                i = i + 1
                self.webview.RunScript("addMyChatList(" + str(i) + ",'" + quote(message.replace('\n','')) + "')")
            message = markdown.markdown(message)
            self.webview.RunScript("addChatContent('" + chat['from'] + "','" + quote(message) + "'," + str(i) + ")")
        self.webview.RunScript("todown()")

    def update_language(self):
        self.config = load_config()
        newlang = self.config.get("lang", "en")
        if newlang == self.selectedlang:
            return
        self.selectedlang = newlang
        self.lang = load_lang(self.selectedlang)
        self.save_button.SetLabelText(text=self.lang.get("save"))
        self.load_button.SetLabelText(text=self.lang.get("reload"))
        self.setting_button.SetLabelText(text=self.lang.get("settings"))
        self.send_button.SetLabelText(text=self.lang.get("send"))
def load_chat_data():
    chat_file = "chat.json"
    if os.path.exists(chat_file):
        with open(chat_file, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    return []


def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "position": (100, 100),
            "size": (800, 600),
            "left_width": 160,
            "show_left": True,
            "lang": "en"
        }

def load_lang(selectedlang):
    try:
        with open("./lang/"+selectedlang+".json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "save": "save",
            "reload": "reload",
            "settings": "settings",
            "send": "send",
            "lang": "language",
            "langoptions": [
                {
                    "value": "en",
                    "text": "English"
                },
                {
                    "value": "zh",
                    "text": "Chinese"
                },
            ],
            "cachedir": "cache dir",
            "browser": "browser",
            "selectcachedir": "Select dir for Cache",
            "kimikey": "Kimi Key",
            "kimiurl": "Kimi Url",
            "canccel": "Cancel"
        }


def parseCode(content):
    # 定义正则表达式模式，匹配 ``` 开始和结束的代码块
    pattern = re.compile(
        r'```(html|css|js|python|javascript|java|hpp|h|cpp|c|php|swift|kotlin|typescript|go|ruby|bash|sql|json'
        r'|xml|yaml|markdown|text)(.*?)```',
        re.DOTALL)

    # 替换匹配到的代码块
    def replace_code(match):
        language = match.group(1).strip()
        code = match.group(2).strip()
        # 替换代码块为 HTML 格式
        html_code = f'<div class="markdown-code">\n'
        html_code += f'  <div class="markdown-title">\n'
        html_code += f'      <div class="toggle-div arrowUp" onclick="toggleCode(this)"></div><div>{language}</div>\n'
        html_code += f'  </div>\n'
        html_code += f'  <pre style="display: block;"><code>\n{code}\n'
        html_code += f'  </code></pre>\n'
        html_code += f'</div>\n'
        return html_code

    # 使用正则表达式替换所有匹配的代码块
    result = re.sub(pattern, replace_code, content)

    return result


if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame()
    frame.Show()
    app.MainLoop()
