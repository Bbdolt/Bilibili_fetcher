import tkinter as tk
from common import is_vlc_path
from tkinter import messagebox, filedialog, ttk
from common import *
from aria2p import Client, Stats


class ListDownloadFrame(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side=tk.LEFT, anchor=tk.NW)
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, anchor=tk.E)
        
        self.import_file_frame = tk.Frame(self.left_frame)
        self.import_file_frame.pack(side=tk.TOP, anchor=tk.NW)
        self.import_file_button = tk.Button(self.import_file_frame, text="导入文件", command=self.import_file)
        self.import_file_button.config(background="lightgreen")
        self.import_file_button.pack(side=tk.LEFT, padx=(10, 20), pady=(25, 10))
        self.download_button = tk.Button(self.import_file_frame, text="确认下载", command=self.download_start_thread)
        self.download_button.config(background="lightblue")
        self.download_button.pack(side=tk.LEFT, padx=(0,), pady=(25, 10))

        self.selected_format = tk.StringVar(self.import_file_frame)
        self.selected_format.set("MP3")
        self.format_menu = tk.OptionMenu(self.import_file_frame, self.selected_format, "MP3", "MP4", command=self.on_format_change)
        self.format_menu.pack(side = tk.LEFT,padx=(40, 100), pady=(25, 10))

        # 下载信息
        self.download_info_frame = tk.Frame(self.left_frame)
        self.download_info_frame.pack(side=tk.TOP, fill=tk.X)
        self.download_info_frame = tk.Frame(self.download_info_frame)
        self.download_info_frame.pack(side=tk.TOP, fill=tk.X)
        self.info_label = tk.Label(self.download_info_frame, text="")
        self.info_label.pack(side=tk.TOP, anchor=tk.W, padx=(5, ), pady=5)

        self.downloan_controle_frame = tk.Frame(self.left_frame)
        self.downloan_controle_frame.pack(side=tk.TOP, fill=tk.X)
        self.pause_button = tk.Button(self.downloan_controle_frame, text="暂停下载", command=self.pause_download)
        self.pause_button.config(background="orange")
        # self.pause_button.pack(side=tk.LEFT, padx=(10, 20), pady=(20, 10))
        self.stop_button = tk.Button(self.downloan_controle_frame, text="取消下载", command=self.stop_download)
        self.stop_button.config(background="red")
        # self.stop_button.pack(side=tk.LEFT, padx=(0,), pady=(20, 10))
        self.stop = False
        self.pause = False
        self.shutdown = False


        # 创建表格
        self.download_list_frame = tk.Frame(self.right_frame)
        self.download_list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.E)
        self.num_label_fram = tk.Frame(self.download_list_frame)
        self.num_label_fram.pack(side=tk.BOTTOM, fill=tk.X)

        self.total_width = 800

        self.download_list_tree = ttk.Treeview(self.download_list_frame, columns=('No', 'title', 'url'), show='headings', height=25)
        self.download_list_tree.column('No', width=int(self.total_width * 1 / 10), anchor='center')
        self.download_list_tree.column('title', width=int(self.total_width * 4 / 10), anchor='w')
        self.download_list_tree.column('url', width=int(self.total_width * 5 / 10), anchor='w')
        self.download_list_tree.heading('No', text='No')
        self.download_list_tree.heading('title', text='标题')
        self.download_list_tree.heading('url', text='链接')
        self.download_list_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.E, padx=(0,10), pady=(10,0))
        # 创建垂直滚动条
        self.vsb = ttk.Scrollbar(self.download_list_frame, orient="vertical", command=self.download_list_tree.yview)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # 配置表格的滚动条
        self.download_list_tree.configure(yscrollcommand=self.vsb.set)
        # 绑定双击事件
        self.download_list_tree.bind('<Double-1>', self.download_list_double_click)
        # 防止连续点击
        self.being = False

        self.num_label = tk.Label(self.num_label_fram, text="当前共有0个元素")
        self.num_label.pack(side=tk.LEFT, pady=(10, 0))
        self.clean_button = tk.Button(self.num_label_fram, text="清空列表", command=self.clean_list)
        self.clean_button.pack(side=tk.RIGHT, padx=(10, 20), pady=(10, 0))


        # 加载文件
        self.load_file_name = "./history/list_download.txt"
        self.tree_data = []
        self.sure_tree_data = []
        self.load_tree()


        # 下载器
        self.is_aria2 = False
        self.aria2_path = "./aria2/aria2c.exe"
        self.download_list_prepare = None
        self.directory = ""
        self.download_list_info = []
        self.aria2_is_downloading = False
        self.choice = "MP3"
        self.download_speed = None
        self.total_task = None
        self.finish_task = None
        self.aria2 = None

        if is_cookie_old():
            messagebox.showwarning("警告", "Cookie已过期或没有设置，请重新设置！") 
        else:
            headers['Cookie'] = read_config()[0]

        if os.path.exists("./aria2/aria2c.exe"):
           self.is_aria2 = True

    def clean_list(self):
        with open("./history/list_download.txt", "w", encoding="utf-8") as f:
            pass
        self.tree_data = []
        self.update_tree()

    def download_list_double_click(self, event):
        if self.being:
            return
        self.being = True
        selected_item = self.download_list_tree.selection()
        if not selected_item:
            self.being = False
            return
        item_data = self.download_list_tree.item(selected_item[0], "values")
        print(f"选中的行数据：No={item_data[0]}, title={item_data[1]}, url={item_data[2]}")
        index = int(item_data[0]) - 1
        self.tree_data.pop(index)
        for i in range(len(self.tree_data)):
            self.tree_data[i].No = i+1
        self.update_tree()
        self.being = False
        
    def load_tree(self):
        self.tree_data = []
        with open(self.load_file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line == "":
                    continue
                self.tree_data.append(List_DownloadInfo(line.split("|")[0], line.split("|")[1]))
        self.update_tree()

    def update_tree(self):
        self.download_list_tree.delete(*self.download_list_tree.get_children())
        for i, item in enumerate(self.tree_data):
            self.download_list_tree.insert('', tk.END, values=(i+1, item.title, item.url))
        self.num_label.config(text=f"当前共有{len(self.tree_data)}个元素")

    def import_file(self):
        file_path = filedialog.askopenfilename(title="选择文件", filetypes=[("txt文件", "*.txt")])
        if not file_path:
            return
        self.tree_data = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    self.tree_data.append(List_DownloadInfo(line.split("|")[0], line.split("|")[1]))
            self.update_tree()
        except:
            messagebox.showerror("错误", "文件格式错误！")

    def download_start_thread(self):
        if self.is_aria2 == False:
            messagebox.showerror("错误", "aria2下载器未配置，请配置后重试！")
            return
        self.download_list_prepare = threading.Thread(target=self.download_prepare)
        self.download_list_prepare.start()
    
    def download_prepare(self):
        self.sure_tree_data = self.tree_data
        if len(self.sure_tree_data) == 0:
            messagebox.showerror("错误", "无可下载资源！")
            return
        else:
            self.download_button.config(state=tk.DISABLED)
            self.directory = filedialog.askdirectory(title="选择下载目录")
            if not self.directory:
                self.download_button.config(state=tk.NORMAL)
                return
            self.download_list_info = []
            self.aria2_is_downloading = True
            self.begin_download()

    def begin_download(self):
        print("开始下载")
        asyncio.run(get_download_resource_start(self.sure_tree_data, self.directory, self.download_list_info))
        # 启动 aria2 RPC 服务
        complex = []
        self.aria2_server = subprocess.Popen([self.aria2_path, "--enable-rpc", "--rpc-listen-all", "--rpc-allow-origin-all", "--rpc-secret", "bbdolt"])
        time.sleep(2)  # 等待aria2服务启动

        # 创建客户端连接
        self.aria2 = Client(
            host='http://localhost',  # aria2的RPC地址
            port=6800,                # aria2的RPC端口``
            secret='bbdolt',          # aria2的RPC密钥（如果有）
            timeout=5,               # 连接超时时间
        )
        if self.choice == "MP3":
            self.download_list_info = [i for i in self.download_list_info if ".m4a" in i.save_path]
        
        # print(self.download_list_info)
        
        for item in self.download_list_info:
            complex.append(os.path.splitext(item.save_path)[0])
            if os.path.exists(item.save_path):
                print(f"文件已存在，跳过下载：{item.save_path}")
                continue
            dir_path = os.path.dirname(item.save_path)
            filename = os.path.basename(item.save_path)
            print(f"开始下载:{dir_path} | {filename}")
            self.aria2.add_uri([item.link], options={
                    'dir': dir_path,
                    'max-concurrent-downloads': 5,
                    'max-connection-per-server': 5,
                    'continue': True,
                    'split': 5,
                    'out': filename,
                    'header': [
                        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                        'Referer: https://www.bilibili.com/'
                    ],
                    'force': True
            })
        self.pause_button.pack(side=tk.LEFT, padx=(10, 20), pady=(20, 10))
        self.stop_button.pack(side=tk.LEFT, padx=(0,), pady=(20, 10))
        while True:
            if self.stop:
                self.shutdown_aria2(self.aria2)
                return
            while self.pause:
                if self.stop:
                    self.shutdown_aria2(self.aria2)
                    return
                else:
                    time.sleep(1)
            global_stat = self.aria2.get_global_stat()
            stats = Stats(global_stat)
            self.download_speed = stats.download_speed_string()
            num_active = stats.num_active
            self.total_task = stats.num_waiting + stats.num_active + stats.num_stopped
            self.finish_task = stats.num_stopped
            print(f"下载速度：{self.download_speed} | 总任务数：{self.total_task} | 已完成任务数：{self.finish_task}")
            self.info_label.config(text=f"下载速度：{self.download_speed}  已完成：{self.finish_task}/{self.total_task}")
            if num_active == 0:
                break
            time.sleep(1)

        if self.choice == "MP4":
            self.complex_files(complex)
        self.shutdown_aria2(self.aria2)

    def shutdown_aria2(self, aria2):
        try:
            aria2.shutdown()
        except Exception as e:
            print(f"关闭aria2失败：{e}")
        
        if self.aria2_server:
            self.aria2_server.terminate()
            self.aria2_server.wait(timeout=3)
            self.aria2_server.kill()
        
        if not self.stop or not self.shutdown:
            if not self.stop:
                messagebox.showinfo("提示", "下载完成！")
                with open("./history/list_download.txt", "w") as file:
                    pass  # 什么都不写，文件内容被清空
            self.info_label.config(text="")
            self.download_button.config(state=tk.NORMAL)
            self.stop_button.pack_forget()
            self.pause_button.pack_forget()

        self.aria2_is_downloading = False
        self.finish_task = None
        self.total_task = None
        self.download_speed = None
        self.pause = False
        self.stop = False

    def complex_files(self,complex):
        self.info_label.config(text=f"下载已完成：正在合并文件，请稍候...")
        complex = list(set(complex))
        print(complex)
        num = len(complex)
        for i,file in enumerate(complex):
            print(file)
            if os.path.exists(f"{file}.mp4") and os.path.exists(f"{file}.m4a") and not os.path.exists(f"{file}.mkv"):
                subprocess.run([
                    "./ffmpeg/ffmpeg.exe", 
                    "-i", f"{file}.mp4", 
                    "-i", f"{file}.m4a", 
                    "-c", "copy", 
                    f"{file}.mkv"
                ])
                os.remove(f"{file}.mp4")
                os.remove(f"{file}.m4a")
                # self.info_label.config(text=f"下载已完成：正在合并文件，进度 {i+1}/{num}")

    def on_format_change(self,selected_format):
        self.choice = selected_format
        print(f"选择的格式：{self.choice}")

    def pause_download(self):
        self.pause = not self.pause
        self.pause_button.config(text="继续下载" if self.pause else "暂停下载")
        self.pause_button.config(background="lightgreen" if self.pause else "orange")
        if self.pause:
            self.aria2.pause_all()
        else:
            self.aria2.unpause_all()

    def stop_download(self):
        self.stop = True
    
    def fresh_list(self):
        self.load_tree()
