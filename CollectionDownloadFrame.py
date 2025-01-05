import tkinter as tk
from tkinter import ttk
import threading
from common import *
import requests
from bs4 import BeautifulSoup
from tkinter import messagebox
from urllib.parse import urlparse, parse_qs
from aria2p import Client, Stats

class CollectionDownloadFrame(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        # 配置关闭窗口
        # root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # IDM下载器路径
        # self.idm_path = "IDM/IDMan.exe"
        # self.is_idm = False
        # self.idm_download_thread = None

        self.aria2_path = "./aria2/aria2c.exe"
        self.is_aria2 = False
        self.aria2_download_thread = None
        self.aria2_server = None
        self.aria2_downloading = False
        self.download_thread = None
        self.stop = False
        self.pause = False
        self.finish_task = None
        self.download_speed = None
        self.total_task = None
        self.shutdown = False
        self.aria2 = None

        self.headers = headers
        self.search_thread = None
        self.download_list = []
        self.sure_download_list = [] 

        # 下载信息列表
        self.DownloadInfo_list = []

        # 合集下载目录
        self.directory = ""

        # 线程
        self.download_prepare_thread = None

        self.left_frame = tk.Frame(self)
        self.left_frame.pack(side=tk.LEFT, anchor=tk.NW)
        self.right_frame = tk.Frame(self)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.search_frame = tk.Frame(self.left_frame)
        self.search_frame.pack(side=tk.TOP, fill=tk.X)
        self.total_frame = tk.Frame(self.left_frame)
        self.total_frame.pack(side=tk.TOP, anchor= tk.NW)
        self.download_info_frame = tk.Frame(self.left_frame)
        self.download_info_frame.pack(side=tk.TOP, fill=tk.X)

        self.default_search = "请输入合集链接（只要能看到合集视频的链接即可）"
        self.search_entry = tk.Entry(self.search_frame, width=44)
        self.search_entry.pack(side=tk.LEFT)
        self.search_entry.bind("<FocusIn>", lambda e: self.on_focus_in(e, self.search_entry, self.default_search))
        self.search_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e, self.search_entry, self.default_search))
        self.search_entry.bind("<Return>", lambda e: self.search_button_click(e))

        self.search_button = tk.Button(self.search_frame, text="搜索", command=self.search_button_click)
        self.search_button.pack(side=tk.LEFT, padx=5)
        self.total_label = tk.Label(self.total_frame, text=f"共0个结果")
        self.total_label.pack(side=tk.LEFT,anchor=tk.W, padx=5, pady=5)

        self.download_button = tk.Button(self.total_frame, text="确认下载", command=self.download_button_thread)
        self.download_button.config(background="lightgreen")
        self.download_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # self.check_button = tk.Button(self.total_frame, text="全选", command=self.check_all)
        # self.check_button.pack(side=tk.RIGHT, padx=5, pady=5)
        self.info_label = tk.Label(self.download_info_frame, text="")
        self.info_label.pack(side=tk.TOP, anchor=tk.W, padx=(5, ), pady=5)

        self.pause_button = tk.Button(self.download_info_frame, text="暂停", command=self.pause_download)
        self.pause_button.config(background="orange")
        # self.pause_button.pack(side=tk.LEFT, padx=(5,10), pady=5)
        self.stop_button = tk.Button(self.download_info_frame, text="取消", command=self.stop_download)
        self.stop_button.config(background="red")
        # self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.result_frame = tk.Frame(self.right_frame)
        self.result_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.total_width = 800

        # 创建表格
        self.tree = ttk.Treeview(self.result_frame, show="headings",columns=("No", "title", "length", "author"), height=25)
        self.tree.column("No", width=int(self.total_width * 1 / 10), anchor="center")
        self.tree.column("title", width=int(self.total_width * 5 / 10), anchor="w")
        self.tree.column("length", width=int(self.total_width * 2 / 10), anchor="center")
        self.tree.column("author", width=int(self.total_width * 2 / 10), anchor="center")
        self.tree.heading("No", text="序号")
        self.tree.heading("title", text="标题")
        self.tree.heading("length", text="时长")
        self.tree.heading("author", text="作者")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 创建垂直滚动条
        self.vsb = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.tree.yview)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # 配置表格的滚动条
        self.tree.configure(yscrollcommand=self.vsb.set)
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.double_click)
        # 防止多次连续点击
        self.being = False

        if is_cookie_old():
            messagebox.showwarning("警告", "Cookie已过期或没有设置，请重新设置！") 
        else:
            headers['Cookie'] = read_config()[0]

        if os.path.exists("./aria2/aria2c.exe"):
           self.is_aria2 = True

    def double_click(self, event):
        if self.being:
            return
        self.being = True
        # 获取选中行的ID
        selected_item = self.tree.selection()
        if not selected_item:
            self.being = False
            return
        # 获取该行的数据
        item_data = self.tree.item(selected_item[0], "values")
        # 打印出该行的数据
        print(f"选中的行数据: No: {item_data[0]}, 标题: {item_data[1]}, 时长: {item_data[2]}, 作者: {item_data[3]}")
        index = int(item_data[0]) - 1
        self.download_list.pop(index)
        for i in range(len(self.download_list)):
            self.download_list[i].no = i + 1
        self.update_tree_view()
        l = self.total_label.cget("text")
        l = int(l[1]) - 1
        self.total_label.config(text=f"共{l}个结果")
        self.being = False

    def search_button_click(self, event=None):
        if self.search_thread is None or not self.search_thread.is_alive():
            # 创建并启动新的线程
            self.search_thread = threading.Thread(target=self.search_thread_run, daemon=True)
            self.search_thread.start()
        else:
            # 如果线程已经存在且活跃，你可以在这里处理这种情况
            print("Search is already running.")
    
    def search_thread_run(self):
        self.url = self.search_entry.get()
        try:
            with requests.get(self.url, headers=self.headers, verify=False) as r:
                page = BeautifulSoup(r.text, "html.parser")
                result_p_active = page.find_all("div", attrs={"class": "simple-base-item video-pod__item active normal"})
                result_p = page.find_all("div", attrs={"class": "simple-base-item video-pod__item normal"})
                result_video = page.find_all("div", attrs={"class": "pod-item video-pod__item simple"})
                result_chanel = "channel" in self.url

                if result_p:
                    # 获得作者名称
                    author = page.find("a", attrs={"class": "up-name"}).get_text(strip=True)
                    # 获得参数p的值
                    parsed_url = urlparse(self.url)
                    query_params = parse_qs(parsed_url.query)
                    p_value = query_params.get('p', [None])[0]
                    # 如果有值，则将active的结果插入到p的结果列表中，反之就插入到第一个位置
                    if p_value:
                        result_p.insert(int(p_value) - 1, result_p_active[0])
                    else:
                        result_p.insert(0, result_p_active[0])
                    # 获得总数，并显示
                    num = len(result_p)
                    self.total_label.config(text=f"共{num}个结果")
                    # 视频前缀
                    video_url = self.url.split("?")[0] + "?p="
                    # 创建下载信息列表
                    download_list_p = []
                    for i in range(num):
                        no = i + 1
                        title = result_p[i].find("div", attrs={"class": "title-txt"}).get_text(strip=True)
                        length = result_p[i].find("div", attrs={"class": "stat-item duration"}).get_text(strip=True)
                        url = video_url + str(no)
                        download_list_p.append(DownloadInfo(no, title, length, author, url))
                    self.download_list = download_list_p
                    self.update_tree_view()
                
                elif result_video:
                    author = page.find("a", attrs={"class": "up-name"}).get_text(strip=True)
                    num = len(result_video)
                    self.total_label.config(text=f"共{num}个结果")
                    download_list_v = []
                    for i in range(num):
                        no = i + 1
                        title = result_video[i].find("div", attrs={"class": "title-txt"}).get_text(strip=True)
                        length = result_video[i].find("div", attrs={"class": "stat-item duration"}).get_text(strip=True)
                        video_url = "https://www.bilibili.com/video/" + result_video[i].get("data-key") + "/"
                        download_list_v.append(DownloadInfo(no, title, length, author, video_url))
                    self.download_list = download_list_v
                    self.update_tree_view()
                    
                elif result_chanel:
                    author = page.find("title").get_text(strip=True)
                    author = author.split("的个人空间")[0]
                    # 获取参数
                    parsed_url = urlparse(self.url)
                    query_params = parse_qs(parsed_url.query)
                    sid_value = query_params.get('sid', [None])[0]
                    x = 1 
                    bvid_list = []
                    title_list = []
                    length_list = []
                    download_list_c = []
                    while True:
                        api_url = f"https://api.bilibili.com/x/polymer/web-space/seasons_archives_list?season_id={sid_value}&page_num={x}&page_size=30"
                        with requests.get(api_url, headers=self.headers, verify=False) as r:
                            parsed_data = json.loads(r.text)
                            if [archive['bvid'] for archive in parsed_data['data']['archives']] == []:
                                break
                            bvid_list += [archive['bvid'] for archive in parsed_data['data']['archives']]
                            title_list += [archive['title'] for archive in parsed_data['data']['archives']]
                            length_list += [archive['duration'] for archive in parsed_data['data']['archives']]
                            x += 1

                    num = len(bvid_list)
                    self.total_label.config(text=f"共{num}个结果")    
                    for i in range(num):
                        no = i + 1
                        title = title_list[i]
                        hours = int(length_list[i]) // 3600
                        minutes = int(length_list[i]) // 60
                        seconds = int(length_list[i]) % 60
                        length = f"{hours:02}:{minutes:02}:{seconds:02}"
                        video_url = f"https://www.bilibili.com/video/{bvid_list[i]}"
                        download_list_c.append(DownloadInfo(no, title, length, author, video_url))
                    self.download_list = download_list_c
                    self.update_tree_view()

                else:
                    self.total_label.config(text="没有搜索到结果")
        
        except Exception as e:
            messagebox.showerror("错误", f"搜索失败：{e}")
        
        finally:
            return
    
    def update_tree_view(self):
        self.tree.delete(*self.tree.get_children())
        for item in self.download_list:
            self.tree.insert('', tk.END, values=(item.no, item.title, item.length, item.author))

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

    def download_button_thread(self):
        if self.is_aria2 == False:
            messagebox.showerror("错误", "aria2下载器未配置，请配置后在下载")
            return
        self.download_prepare_thread = threading.Thread(target=self.download_button_click)
        self.download_prepare_thread.start()

    def download_button_click(self):
        self.sure_download_list = self.download_list
        if self.sure_download_list == []:
            messagebox.showerror("错误", "请先输入合集链接点击搜索确认无误后点击确认下载！")
            return
        else:
            self.download_button.config(state=tk.DISABLED)
            self.directory = filedialog.askdirectory(title="请选择合集下载的目录")
            if not self.directory:
                self.download_button.config(state=tk.NORMAL)
                return 
            task_filename = f"history/{len(self.sure_download_list)}_{self.sure_download_list[0].author}.txt"
            self.DownloadInfo_list = []
            self.aria2_downloading = True
            # 使用线程来运行异步代码
            self.download_thread = threading.Thread(target=self.run_download_task, args=(task_filename,))
            self.download_thread.start()

    def run_download_task(self, task_filename):
        # 在此线程中运行异步代码
        asyncio.run(get_download_resource_start(self.sure_download_list, self.directory, self.DownloadInfo_list))

        # 任务完成后更新GUI
        self.after(0, self.on_download_complete, task_filename)

    def on_download_complete(self, task_filename):
        # 下载任务已保存至文件
        with open(task_filename, "w", encoding="utf-8") as f:
            for item in self.DownloadInfo_list:
                f.write(f'{item.link} {item.save_path}\n')
        print(f"下载任务已保存至{task_filename}")
        self.aria2_download_thread = threading.Thread(target=self.download_with_idm, args=(task_filename,))
        self.aria2_download_thread.start()

    def download_with_idm(self, task_filename):
        complex = []
        # 启动 aria2 RPC 服务
        self.aria2_server = subprocess.Popen([self.aria2_path, "--enable-rpc", "--rpc-listen-all", "--rpc-allow-origin-all", "--rpc-secret", "bbdolt"])
        time.sleep(2)  # 等待aria2服务启动

        # 创建客户端连接
        self.aria2 = Client(
            host='http://localhost',  # aria2的RPC地址
            port=6800,                # aria2的RPC端口
            secret='bbdolt',          # aria2的RPC密钥（如果有）
            timeout=5,               # 连接超时时间
        )

        # 从文件中读取下载任务
        with open(task_filename, 'r', encoding='utf-8') as file:
            for line in file:
                # 按空格分隔 URL 和保存路径
                if line.strip() == '':
                    continue
                url, save_path = line.split(maxsplit=1)
                save_path = save_path.strip()  # 去除首尾空格
                complex.append(os.path.splitext(save_path)[0])
                if os.path.exists(save_path):
                    continue
                file_name = save_path.split('\\')[-1]
                save_path = save_path.split('\\')[:-1]  # 去除文件名
                save_path = '\\'.join(save_path)  # 路径拼接

                # 调用 aria2 的 add_uri 方法添加下载任务
                self.aria2.add_uri([url], options={
                    'dir': save_path,
                    'max-concurrent-downloads': 5,
                    'max-connection-per-server': 5,
                    'continue': True,
                    'split': 5,
                    'out': file_name,
                    'header': [
                        'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
                        'Referer: https://www.bilibili.com/'
                    ],
                    'force': True
                })
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_button.pack(side=tk.LEFT, padx=5, pady=5)
        while True:
            if self.stop:
                self.graceful_shutdown_aria2(self.aria2)
                return

            while self.pause:
                if self.stop:
                    self.graceful_shutdown_aria2(self.aria2)
                    return
                else:
                    time.sleep(1)

            # 获取全局统计信息
            global_stat = self.aria2.get_global_stat()

            # 创建 Stats 实例，处理获取到的全局信息
            stats = Stats(global_stat)

            # 获取当前下载和上传速度
            self.download_speed = stats.download_speed_string()
            # 获取活动、等待和停止的下载任务数量
            num_active = stats.num_active
            self.total_task = stats.num_active + stats.num_waiting + stats.num_stopped
            self.finish_task = stats.num_stopped
            # num_stopped_total = stats.num_stopped_total()
            # 输出当前统计信息
            print(f"下载速度: {self.download_speed}")
            print(f"停止的下载任务: {self.finish_task}")
            self.info_label.config(text=f"下载速度：{self.download_speed}  已完成：{self.finish_task}/{self.total_task}")
            # 如果没有活动下载任务，则退出循环
            if num_active == 0:
                break
            # 每隔 1 秒更新一次状态
            time.sleep(1)

        self.complex_files(complex)
        self.graceful_shutdown_aria2(self.aria2)
    
    def graceful_shutdown_aria2(self, aria2):
        try:
            print("正在优雅地关闭 aria2 服务...")
            aria2.shutdown()  # 使用 RPC 命令优雅关闭 aria2 服务
            print("aria2 服务已成功关闭.")
        except Exception as e:
            print(f"关闭 aria2 服务时出错: {e}")

        # 关闭 aria2 进程
        if self.aria2_server:
            print("正在终止 aria2 进程...")
            self.aria2_server.terminate()  # 强制终止 aria2 进程
            self.aria2_server.wait(timeout=3)
            self.aria2_server.kill()
            print("aria2 进程已强制终止.")

            if not self.stop or not self.shutdown:
                if not self.stop:
                    messagebox.showinfo("提示", "下载完成！")
                self.download_button.config(state=tk.NORMAL)
                self.info_label.config(text='')
                self.stop_button.pack_forget()
                self.pause_button.pack_forget()

            self.aria2_downloading = False
            self.stop = False
            self.pause = False
            self.finish_task = None
            self.download_speed = None
            self.total_task = None

    def complex_files(self,complex):
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
                self.info_label.config(text=f"下载已完成：正在合并文件，进度 {i+1}/{num}")
            

    def check_all(self):
        print(self.download_prepare_thread.is_alive())
        print(self.aria2_download_thread.is_alive())

    def stop_download(self):
        self.stop = True

    def pause_download(self):
        self.pause = not self.pause
        self.pause_button.config(text="继续" if self.pause else "暂停")
        self.pause_button.config(background="lightgreen" if self.pause else "orange")