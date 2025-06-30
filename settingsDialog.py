import wx
import json
import os


class SettingsDialog(wx.Dialog):
    def __init__(self, parent):
        size = wx.Size(500, 240)
        super().__init__(parent, title=parent.lang.get("settings"), size=wx.Size(500, 260))

        parent.center_on_parent(self)
        self.settings_file = "config.json"
        self.settings = self.load_settings()

        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.lang_label = wx.StaticText(self.panel, label=parent.lang.get("lang") + ":", size=wx.Size(60, 25),
                                        style=wx.ALIGN_RIGHT)
        self.selectedlang = parent.selectedlang
        self.langoptions = parent.lang.get("langoptions")
        choices1 = [option["text"] for option in self.langoptions]
        lang_dict = {option["value"]: option["text"] for option in self.langoptions}
        # 获取初始值对应的文本
        initial_value_text = lang_dict.get(self.selectedlang, choices1[0])
        self.lang_select = wx.ComboBox(self.panel, choices=choices1, style=wx.CB_DROPDOWN, value=initial_value_text)
        self.lang_select.Bind(wx.EVT_COMBOBOX, self.on_langselect)
        lang_sizer = wx.BoxSizer(wx.HORIZONTAL)
        lang_sizer.Add(self.lang_label, 0, wx.ALL, 5)
        lang_sizer.Add(self.lang_select, 1, wx.ALL | wx.EXPAND, 5)

        # 缓存目录设置
        self.cache_dir_label = wx.StaticText(self.panel, label=parent.lang.get("cachedir")+":", size=wx.Size(60, 25), style=wx.ALIGN_RIGHT)
        self.cache_dir_text = wx.TextCtrl(self.panel, value=self.settings.get("cache_dir", ""))
        self.cache_dir_button = wx.Button(self.panel, label=parent.lang.get("browser"))
        self.cache_dir_button.Bind(wx.EVT_BUTTON, self.on_browse_cache_dir)
        self.selectcachedir = parent.lang.get("selectcachedir")

        cache_dir_sizer = wx.BoxSizer(wx.HORIZONTAL)
        cache_dir_sizer.Add(self.cache_dir_label, 0, wx.ALL, 5)
        cache_dir_sizer.Add(self.cache_dir_text, 1, wx.ALL | wx.EXPAND, 5)
        cache_dir_sizer.Add(self.cache_dir_button, 0, wx.ALL, 5)

        # AI Key 设置
        self.ai_key_label = wx.StaticText(self.panel, label="AI Key:", size=wx.Size(60, 25), style=wx.ALIGN_RIGHT)
        self.ai_key_text = wx.TextCtrl(self.panel, value=self.settings.get("ai_key", ""))

        ai_key_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ai_key_sizer.Add(self.ai_key_label, 0, wx.ALL, 5)
        ai_key_sizer.Add(self.ai_key_text, 1, wx.ALL | wx.EXPAND, 5)

        # AI URL 设置
        self.ai_url_label = wx.StaticText(self.panel, label="AI URL:", size=wx.Size(60, 25), style=wx.ALIGN_RIGHT)
        self.ai_url_text = wx.TextCtrl(self.panel, value=self.settings.get("ai_url", ""))

        ai_url_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ai_url_sizer.Add(self.ai_url_label, 0, wx.ALL, 5)
        ai_url_sizer.Add(self.ai_url_text, 1, wx.ALL | wx.EXPAND, 5)

        # 按钮
        self.save_button = wx.Button(self.panel, label=parent.lang.get("save"))
        self.cancel_button = wx.Button(self.panel, label=parent.lang.get("cancel"))
        self.save_button.Bind(wx.EVT_BUTTON, lambda event: self.on_save(parent, event))
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_sizer.Add(self.save_button, 0, wx.ALL, 5)
        button_sizer.Add(self.cancel_button, 0, wx.ALL, 5)

        # 布局
        self.sizer.Add(lang_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(cache_dir_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(ai_key_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(ai_url_sizer, 0, wx.EXPAND | wx.ALL, 5)
        self.sizer.Add(button_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.panel.SetSizer(self.sizer)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r", encoding="utf-8") as file:
                return json.load(file)
        return {
            "cache_dir": "./cache",
            "ai_key": "",
            "ai_url": "",
            "lang": "en"
        }

    def on_langselect(self, event):
        # 获取用户选择的文本
        selection_text = self.lang_select.GetValue()
        # 获取用户选择的索引
        selection_index = self.lang_select.GetSelection()
        # 根据索引获取对应的 value
        self.selectedlang = self.langoptions[selection_index]["value"]
        # wx.MessageBox(f"你选择了：{selection_text} (Value: {self.selectedlang})", "选择结果")

    def save_settings(self,parent):
        self.settings["cache_dir"] = self.cache_dir_text.GetValue()
        self.settings["ai_key"] = self.ai_key_text.GetValue()
        self.settings["ai_url"] = self.ai_url_text.GetValue()
        self.settings["lang"] = self.selectedlang
        print(self.settings)
        with open(self.settings_file, "w", encoding="utf-8") as file:
            json.dump(self.settings, file, indent=4)
        parent.update_language()

    def on_browse_cache_dir(self, event):
        with wx.DirDialog(self, self.selectcachedir, style=wx.DD_DEFAULT_STYLE) as dir_dialog:
            if dir_dialog.ShowModal() == wx.ID_OK:
                self.cache_dir_text.SetValue(dir_dialog.GetPath())

    def on_save(self, parent, event):
        self.save_settings(parent=parent)
        self.EndModal(wx.ID_OK)

    def on_cancel(self, event):
        self.EndModal(wx.ID_CANCEL)
