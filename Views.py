import tkinter as tk
import tkinter.filedialog as filedialog
from common import write_config, read_config
import threading
import webbrowser
import os

class AboutFrame(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        title_frame = tk.Frame(self)
        title_frame.pack(side=tk.TOP)
        under_frame = tk.Frame(self)
        under_frame.pack(side=tk.BOTTOM)
        animal_art_frame = tk.Frame(under_frame)
        animal_art_frame.pack(side=tk.RIGHT)
        button_frame = tk.Frame(under_frame)
        button_frame.pack(side=tk.LEFT)

        ascii_art = """                                                                                                 
   ____   ____  _         _       _ _          _ _   _           _      _       
  / __ \ | __ )| |__   __| | ___ | | |_   __ _(_| |_| |__  _   _| |__  (_) ___  
 / / _` ||  _ \| '_ \ / _` |/ _ \| | __| / _` | | __| '_ \| | | | '_ \ | |/ _ \ 
| | (_| || |_) | |_) | (_| | (_) | | |_ | (_| | | |_| | | | |_| | |_) _| | (_) |
 \ \__,_||____/|_.__/ \__,_|\___/|_|\__(_\__, |_|\__|_| |_|\__,_|_.__(_|_|\___/ 
  \____/                                 |___/                                                                                                               
        """
        # 创建Label以显示字符画
        self.label = tk.Label(
            self, 
            text=ascii_art, 
            font=("Courier", 8),  # 使用等宽字体
            justify="left",       # 左对齐
            anchor="nw"           # 左上角对齐
        )
        self.label.pack(fill="both", expand=True)

        animal_art = """
              *         *      *         *
          ***          **********          ***
       *****           **********           *****
     *******           **********           *******
   **********         ************         **********
  ****************************************************
 ******************************************************
********************************************************
********************************************************
********************************************************
 ******************************************************
  ********      ************************      ********
   *******       *     *********      *       *******
     ******             *******              ******
       *****             *****              *****
          ***             ***              ***
            **             *              **
"""
        self.label = tk.Label(
            animal_art_frame, 
            text=animal_art, 
            font=("Courier", 8),  # 使用等宽字体
            justify="left",       # 左对齐
            anchor="nw"           # 左上角对齐
        )
        self.label.pack(side=tk.RIGHT,padx=(0,50))

        # 按钮
        self.blog_button = tk.Button(button_frame, text="Welcome to Myblog", command=self.open_blog_thread)
        self.blog_button.config(background="lightblue", foreground="black")
        self.blog_button.pack(side=tk.BOTTOM, padx=(0, 500))
        self.readme_button = tk.Button(button_frame, text="使用手册介绍", command=self.open_readme_thread)
        self.readme_button.config(background="gray", foreground="black")
        self.readme_button.pack(side=tk.BOTTOM, padx=(0, 500), pady=10)

    def open_blog_thread(self):
        threading.Thread(target=self.welcome_blog, daemon=True).start()

    def welcome_blog(self):
        webbrowser.open("https://Bbdolt.github.io/")

    def open_readme_thread(self):
        threading.Thread(target=self.show_message, daemon=True).start()

    def show_message(self):
        readme_path = "README.txt"
        if os.path.exists(readme_path):
            # 使用 webbrowser 打开 README.md 文件（在浏览器或默认应用中查看）
            webbrowser.open('file://' + readme_path)

class ConfigFrame(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        label1_frame = tk.Frame(self)
        label1_frame.pack(side=tk.TOP, fill=tk.X, pady=(10, 0), padx=0, anchor="w")
        path_frame = tk.Frame(self)
        path_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,10), padx=0, anchor="w")
        label3_frame = tk.Frame(self)
        label3_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,0), padx=0, anchor="w")
        path1_frame = tk.Frame(self)
        path1_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,10), padx=0, anchor="w")
        label2_frame = tk.Frame(self)
        label2_frame.pack(side=tk.TOP, fill=tk.X, pady=(0,0), padx=0, anchor="w")
        cookie_frame = tk.Frame(self)
        cookie_frame.pack(side=tk.TOP, pady=0, anchor="w", fill=tk.X)
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.TOP, pady=20)

        # 路径设置
        # vlc路径
        self.path_label = tk.Label(label1_frame, text="vlc.exe路径：")
        self.path_label.pack(side=tk.LEFT, padx=(0, 750))
        default_path = "请输入vlc.exe的路径（默认:./vlc/vlc.exe）"
        self.path_entry = tk.Entry(path_frame, width=100)
        self.path_entry.pack(side=tk.LEFT, padx=(0, 10), anchor="w") 
        self.path_entry.insert(0, default_path)
        self.path_entry.config(fg="gray")
        self.path_button = tk.Button(path_frame,text="...", command=self.select_path)
        self.path_button.pack(side=tk.LEFT, padx=(0, 400))
        self.path_button.config(width=2,height=1)
        self.path_entry.bind("<FocusIn>", lambda e: self.on_focus_in(e, self.path_entry, default_path))
        self.path_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e, self.path_entry, default_path))
        # IDMan.exe路径
        # self.idman_path_label = tk.Label(label3_frame, text="IDMan.exe路径：")
        # self.idman_path_label.pack(side=tk.LEFT, padx=(0, 750))
        # default_idman_path = "请输入IDMan.exe的路径（默认:./IDMan/IDMan.exe）"
        # self.idman_path_entry = tk.Entry(path1_frame, width=100)
        # self.idman_path_entry.pack(side=tk.LEFT, padx=(0, 10), anchor="w")
        # self.idman_path_entry.insert(0, default_idman_path)
        # self.idman_path_entry.config(fg="gray")
        # self.idman_path_button = tk.Button(path1_frame, text="...", command=self.select_idman_path)
        # self.idman_path_button.pack(side=tk.LEFT, padx=(0, 400))
        # self.idman_path_button.config(width=2, height=1)
        # self.idman_path_entry.bind("<FocusIn>", lambda e: self.on_focus_in(e, self.idman_path_entry, default_idman_path))
        # self.idman_path_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e, self.idman_path_entry, default_idman_path))

        # Cookie 设置
        self.cookie_label = tk.Label(label2_frame, text="Bilibili Cookie：")
        self.cookie_label.pack(side=tk.LEFT, padx=(0, 750))
        default_cookie = "请输入你的Bilibili Cookie"
        self.cookie_text = tk.Text(cookie_frame, width=100, height=20, wrap=tk.WORD)
        self.cookie_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # 占满窗口宽度
        self.cookie_text.insert("1.0", default_cookie)
        self.cookie_text.config(fg="gray")
        self.cookie_text.bind("<FocusIn>", lambda e: self.on_focus_in_text(e, self.cookie_text, default_cookie))
        self.cookie_text.bind("<FocusOut>", lambda e: self.on_focus_out_text(e, self.cookie_text, default_cookie))

        # 提示信息
        self.info_text_visible = True
        self.info_text = tk.Label(self, text=
        """
        # 如果问题可以直接去 config.ini 文件修改配置（注意: 后有个空格）
        Cookie: bilibili_cookie
        vlc_path: ./vlc/vlc.exe
        """,
        justify=tk.LEFT,  # 使得文本左对齐
        highlightthickness=1,  # 设置边框的厚度
        highlightbackground="blue"  # 设置边框的颜色为蓝色
        )
        # self.info_text.pack(side=tk.BOTTOM, pady=10)

        # save 按钮
        self.save_button = tk.Button(button_frame, text="保存", command=self.save_config)
        self.save_button.pack(side=tk.LEFT, pady=10)

        # 帮助按钮
        self.help_button = tk.Button(button_frame, text="帮助", command=self.help_info)
        self.help_button.pack(side=tk.LEFT, pady=10, padx=(30, 0))

    def help_info(self):
        if not self.info_text_visible:
            self.info_text.pack_forget()
            self.info_text_visible = True
        else:  
            self.info_text.pack(side=tk.BOTTOM, pady=10)
            self.info_text_visible = False

    def on_focus_in_text(self, event, widget, default_text):
        if widget.get("1.0", "end-1c") == default_text:
            widget.delete("1.0", "end")
            widget.config(fg="black")

    def on_focus_out_text(self, event, widget, default_text):
        if not widget.get("1.0", "end-1c").strip():
            widget.insert("1.0", default_text)
            widget.config(fg="gray")

    # 通用事件处理函数，支持多个输入框和占位符文本
    def on_focus_in(self, event, entry, default_text):
        if entry.get() == default_text:
            entry.delete(0, tk.END)  # 清空占位符
            entry.config(fg='black')  # 设置字体为黑色

    def on_focus_out(self, event, entry, default_text):
        if entry.get() == "":  # 当输入框为空时，显示占位符
            entry.insert(0, default_text)
            entry.config(fg='grey')
        elif entry.get() != default_text:  # 当输入框不为空且内容不等于占位符时，设为黑色
            entry.config(fg='black')
    def select_path(self):
        file_path = filedialog.askopenfilename(
            title="选择vlc.exe路径",
            filetypes=[("Executable files", "*.exe")]
        )
        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)
            self.path_entry.config(fg='black')
    def select_idman_path(self):
        file_path = filedialog.askopenfilename(
            title="选择IDMan.exe路径",
            filetypes=[("Executable files", "*.exe")]
        )
        if file_path:
            self.idman_path_entry.delete(0, tk.END)
            self.idman_path_entry.insert(0, file_path)
            self.idman_path_entry.config(fg='black')
    def save_config(self):
        path = self.path_entry.get().strip()
        cookie = self.cookie_text.get("1.0", "end-1c").strip()
        idman_path = ""
        write_config(cookie, path, idman_path)
