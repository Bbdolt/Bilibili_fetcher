import tkinter as tk
from tkinter import ttk
import threading
from common import *
import subprocess
import os
import psutil

class MainFrame(tk.Frame):
    def __init__(self, root):
        super().__init__(root)
        # # 配置关闭窗口
        # root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 记录到列表的数据
        self.list_download_info = None

        # vlc播放器路径
        self.vlc_path = './vlc/vlc.exe'
        # 在线播放线程
        self.play_thread = None
        self.video_thread = None
        # 搜索结果列表
        self.video_list = []
        # 分段下载大小
        self.chunk_size = 1024*1024
        # 当前下载
        self.downloaded_size = 0
        self.total_size = 0
        # 搜索控制
        self.search_thread_event = threading.Event()
        self.page = 1
        # 控制暂停、取消和下载状态的全局变量
        self.is_paused = False
        self.is_downloading = False
        self.stop_download = False
        self.download_thread = None
        # 左侧框架
        left_frame = tk.Frame(self)
        left_frame.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=5)
        # 左侧搜索框
        default_search = '输入搜索关键词'
        path_frame1 = tk.Frame(left_frame)  # 创建一个框架用于包含路径输入框和按钮
        path_frame1.pack(pady=5)
        self.search_entry = tk.Entry(path_frame1, width=44)
        self.search_entry.pack(side=tk.LEFT)
        self.search_button = tk.Button(path_frame1, text="搜索", command=self.reset_and_search)
        self.search_button.pack(side=tk.RIGHT, padx=5)
        self.search_entry.insert(0, default_search)
        self.search_entry.config(fg='grey')  # 设置占位符文本颜色为灰色
        self.search_entry.bind("<FocusIn>", lambda e: self.on_focus_in(e, self.search_entry, default_search))
        self.search_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e, self.search_entry, default_search))
        self.search_entry.bind("<Return>", lambda e: self.reset_and_search(e))  # 绑定回车键事件
        # 视频链接输入框
        default_url = '输入视频链接(必要)'
        self.url_entry = tk.Entry(left_frame, width=50)
        self.url_entry.pack()
        self.url_entry.pack(pady=5)
        self.url_entry.insert(0, default_url)
        self.url_entry.config(fg='grey')  # 设置占位符文本颜色为灰色
        self.url_entry.bind("<FocusIn>", lambda e: self.on_focus_in(e, self.url_entry, default_url))
        self.url_entry.bind("<FocusOut>", lambda e: self.on_focus_out(e, self.url_entry, default_url))
        # 选择下载类型
        checkbox_frame = tk.Frame(left_frame)
        checkbox_frame.pack(pady=5)
        self.mp4_var = tk.BooleanVar()
        self.mp3_var = tk.BooleanVar()
        self.img_var = tk.BooleanVar()
        self.mp3_var.set(True)
        mp4_checkbutton = tk.Checkbutton(checkbox_frame, text="MP4", variable=self.mp4_var, onvalue=True, offvalue=False)
        mp4_checkbutton.pack(side=tk.LEFT)
        mp3_checkbutton = tk.Checkbutton(checkbox_frame, text="MP3", variable=self.mp3_var, onvalue=True, offvalue=False)
        mp3_checkbutton.pack(side=tk.LEFT)
        img_checkbutton = tk.Checkbutton(checkbox_frame, text="封面", variable=self.img_var, onvalue=True, offvalue=False)
        img_checkbutton.pack(side=tk.LEFT)
        # 进度条
        progress_frame = tk.Frame(left_frame)
        progress_frame.pack(side=tk.BOTTOM, pady=10)
        self.progress = ttk.Progressbar(progress_frame, length=350, mode='determinate')
        # self.progress.pack(side=tk.LEFT, pady=5, padx=0)
        # 按钮框架
        button_frame = tk.Frame(left_frame)
        button_frame.pack(side=tk.BOTTOM, pady=5, fill=tk.X)
        self.download_button = tk.Button(button_frame, text="开始下载", command=self.download_both)
        self.download_button.config(background="lightblue", foreground="black")  # 设置颜色
        self.download_button.pack(side=tk.LEFT, padx=0, pady=0)
        self.kill_button = tk.Button(button_frame, text="取消下载", command=self.kill_download)
        self.kill_button.config(background="red", foreground="black")
        # self.kill_button.pack(side=tk.LEFT, padx=5, pady=0)

        self.listen_button = tk.Button(button_frame, text="在线听歌", command=self.start_play_audio_thread)
        self.listen_button.config(background="light green", foreground="black")
        self.listen_button.pack(side=tk.RIGHT, padx=5, pady=0)
        self.check_button = tk.Button(button_frame, text="在线TV", command=self.start_play_video_thread)
        self.check_button.config(background="light blue", foreground="black")
        self.check_button.pack(side=tk.RIGHT, padx=5, pady=0)
        self.check_button = tk.Button(button_frame, text="添加到下载列表", command=self.check)
        self.check_button.config(background="light blue", foreground="black")
        self.check_button.pack(side=tk.RIGHT, padx=5, pady=0)
        
        # 右侧结果列表
        right_frame = tk.Frame(self)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        result_list_frame = tk.Frame(right_frame)
        result_list_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        button_frame = tk.Frame(right_frame)
        button_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        total_width = 800
        # 创建表格
        self.tree = ttk.Treeview(result_list_frame, columns=("Name", "View", "Length", "Author", "url"), show='headings', height=25)
        self.tree.column("Name", width=int(total_width * 4 / 10), anchor="w")  # 4份
        self.tree.column("View", width=int(total_width * 1 / 10), anchor="center")  # 1份
        self.tree.column("Length", width=int(total_width * 1 / 10), anchor="center")  # 1份
        self.tree.column("Author", width=int(total_width * 1 / 10), anchor="center")  # 1份
        self.tree.column("url", width=int(total_width * 3 / 10), anchor="w")  # 3份
        self.tree.heading("Name", text="标题")
        self.tree.heading("View", text="观看量")
        self.tree.heading("Length", text="视频长度")
        self.tree.heading("Author", text="作者")
        self.tree.heading("url", text="链接")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 创建垂直滚动条
        self.vsb = ttk.Scrollbar(result_list_frame, orient="vertical", command=self.tree.yview)
        self.vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # 配置表格的滚动条
        self.tree.configure(yscrollcommand=self.vsb.set)
        # 绑定双击事件
        self.tree.bind("<Double-1>", self.on_double_click)
        self.next_button = tk.Button(button_frame, text="下一页", command=self.next_page)
        self.next_button.pack(side=tk.RIGHT, padx=15, pady=15)
        self.page_label = tk.Label(button_frame, text=f"")
        self.page_label.pack(side=tk.RIGHT, padx=15, pady=15)
        self.front_button = tk.Button(button_frame, text="上一页", command=self.previous_page)
        self.front_button.pack(side=tk.RIGHT, padx=15, pady=15)
        if is_cookie_old():
            messagebox.showwarning("警告", "Cookie已过期或没有设置，请重新设置！") 
        else:
            headers['Cookie'] = read_config()[0]
        if not is_vlc_path()[0]:
            messagebox.showwarning("警告", "vlc.exe路径未设置，部分功能将无法使用！")
        else:
            self.vlc_path = is_vlc_path()[1]

    def reset_and_search(self, event=None):
        self.page = 1  # 重置页码
        self.search_in_thread()
        self.page_label.config(text=f"{self.page}")

    def next_page(self):
        self.page += 1
        self.search_in_thread()
        self.page_label.config(text=f"{self.page}")

    def previous_page(self):
        if self.page > 1:
            self.page -= 1
        self.search_in_thread()
        self.page_label.config(text=f"{self.page}")

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

    def search_in_thread(self):
        if self.search_thread_event.is_set():
            self.search_thread_event.clear()
        # 启动一个子线程来运行 search 函数
        search_thread = threading.Thread(target=self.search)
        search_thread.start()

    def clear_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    # 更新表格内容
    def update_tree(self):
        self.clear_tree()
        for video in self.video_list:
            self.tree.insert('', tk.END, values=(video.name, video.view, video.length, video.author, video.url))

    def search(self):
        keyword = self.search_entry.get()
        names = []
        views = []
        lengths = []
        authors = []
        urls = []
        try:
            with requests.get(f'https://search.bilibili.com/video?keyword={keyword}&page={self.page}', headers=headers, verify=False) as r:
                html_element = etree.HTML(r.text)
                parent_div = html_element.xpath('/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]')
                if parent_div:
                    for i in range(1, len(parent_div[0].xpath('div')) + 1):
                        names.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/div/div/a/h3/@title'))
                        views.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/a/div/div[2]/div/div/span[1]/span/text()'))
                        lengths.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/a/div/div[2]/div/span/text()'))
                        authors.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/div/div/p/a/span[1]/text()'))
                        urls.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/a/@href'))
                    self.video_list = [VideoInfo(names[i], views[i], lengths[i], authors[i], urls[i]) for i in range(len(names))]
                    self.update_tree()
                else:
                    messagebox.showwarning("警告", "未找到相关视频！")
        except Exception as e:
            messagebox.showerror("错误", f"搜索过程中发生错误：{e}")
        finally:
            pass

    def on_double_click(self, event):
        # 获取当前选中的 item
        item_id = self.tree.selection()
        if item_id:
            # 获取选中行的所有数据 (一个元组)
            row_data = self.tree.item(item_id, "values")
            # 确保访问 "values" 返回的是一个元组
            if len(row_data) >= 5:
                url = row_data[4]  # 第5列是 URL
                # 清空并插入 URL 到输入框
                self.url_entry.delete(0, tk.END)
                if url.startswith('//'):
                    url = 'https:' + url
                self.url_entry.insert(0, url)
                self.url_entry.config(fg='black')  # 将文本颜色设置为黑色
                self.list_download_info = List_DownloadInfo(row_data[0], row_data[4])
                # video_name = row_data[0]  # 第1列是名称
                # video_name = filter_filename(video_name)

    # 下载功能
    def get_resource_mp4(self, video_url, audio_url, name):
        start = 0
        check_dir("mp4")
        with open(f"mp4/video.mp4", "wb") as f:
            while True:
                while self.is_paused:
                    if self.stop_download:
                        f.close()
                        delete_file("./mp4/video.mp4")
                        delete_file(f"./mp3/{name}.mp3")
                        return

                end_byte = start + self.chunk_size - 1
                headers_range = {'Range': f"bytes={start}-{end_byte}"}
                with requests.get(video_url, headers={**headers, **headers_range}, stream=True, verify=False) as r_download:
                    if r_download.status_code == 206:
                        f.write(r_download.content)
                        start += self.chunk_size
                        self.downloaded_size += self.chunk_size
                        self.update_progress()
                    else:
                        break
        if self.mp3_var.get():
            pass
        else:
            start = 0
            with open(f"./mp3/{name}.mp3", "wb") as f:
                while True:
                    while self.is_paused:
                        if self.stop_download:
                            return
                    end_byte = start + self.chunk_size - 1
                    headers_range = {'Range': f"bytes={start}-{end_byte}"}
                    with requests.get(audio_url, headers={**headers, **headers_range}, stream=True, verify=False) as r_download:
                        if r_download.status_code == 206:
                            f.write(r_download.content)
                            start += self.chunk_size
                            self.downloaded_size += self.chunk_size
                            self.update_progress()
                        else:
                            break
        # 合并音频和视频
        os.system(f"ffmpeg\\ffmpeg.exe -y -i ./mp4/video.mp4 -i ./mp3/{name}.mp3 -c copy ./mp4/{name}.mp4")
        # 删除临时文件
        os.remove(f"./mp4/video.mp4")
        if self.mp3_var.get():
            pass
        else:
            os.remove(f"./mp3/{name}.mp3")
        if self.stop_download:
            os.remove(f"./mp4/{name}.mp4")

    def get_resource_mp3(self, audio_url, name):
        start = 0
        file_save_path = "./mp3"
        check_dir(file_save_path)
        file_path = f"{file_save_path}/{name}.mp3"
        with open(file_path, "wb") as f:
            while True:
                while self.is_paused:
                    if self.stop_download:
                        f.close()
                        delete_file(f"./mp3/{name}.mp3")
                        return
                end_byte = start + self.chunk_size - 1
                headers_range = {'Range': f"bytes={start}-{end_byte}"}
                with requests.get(audio_url, headers={**headers, **headers_range}, stream=True, verify=False) as r_download:
                    if r_download.status_code == 206:
                        f.write(r_download.content)
                        start += self.chunk_size
                        self.downloaded_size += self.chunk_size
                        self.update_progress()
                    else:
                        break

    def get_resource_img(self, img_link, end, name):
        start = 0
        file_save_path = "./img"
        check_dir(file_save_path)
        file_path = f"{file_save_path}/{name}.{end}"
        with open(file_path, "wb") as f:
            while True:
                while self.is_paused:
                    if self.stop_download:
                        f.close()
                        delete_file(f"./img/{name}.{end}")
                        return
                end_byte = start + self.chunk_size - 1
                headers_range = {'Range': f"bytes={start}-{end_byte}"}
                with requests.get(img_link, headers={**headers, **headers_range}, stream=True, verify=False) as r_download:
                    if r_download.status_code == 206:
                        f.write(r_download.content)
                        start += self.chunk_size
                        self.downloaded_size += self.chunk_size
                        self.update_progress()
                    else:
                        break

    def download_both(self):
        if not self.is_downloading:
            self.start_download()
        else:
            # 切换暂停/继续状态
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.download_button.config(text="继续下载", background="lightgreen")
            else:
                self.download_button.config(text="暂停下载", background="orange")

    def kill_download(self):
        if self.is_downloading:
            self.stop_download = True
            self.is_paused = True

    def start_download(self):
        url = self.url_entry.get()
        if url == "输入视频链接(必要)" or not url.strip():
            messagebox.showwarning("警告", "请输入视频链接！")
            return

        if not (self.mp4_var.get() or self.mp3_var.get() or self.img_var.get()):
            messagebox.showwarning("警告", "请选择下载资源类型！")
            return

        # 重置标志并更新按钮状态
        self.is_downloading = True
        self.stop_download = False
        self.is_paused = False
        self.download_button.config(text="暂停下载", background="orange")
        self.progress.pack(side=tk.LEFT, pady=5, padx=0)
        self.kill_button.pack(side=tk.LEFT, padx=5, pady=0)

        # 创建并启动下载线程
        self.download_thread = threading.Thread(target=self.download_both_thread)
        self.download_thread.daemon = True
        self.download_thread.start()

    def download_both_thread(self):
        url = self.url_entry.get()
        img_link, end, video_url, audio_url, name = get_resource(url)
        if self.mp4_var.get():
            self.total_size += get_file_size(video_url, headers)
        if self.mp3_var.get():
            if self.mp4_var.get():
                pass
            else:
                self.total_size += get_file_size(audio_url, headers)
        if self.img_var.get():
            self.total_size += get_file_size(img_link, headers)

        if self.img_var.get():
            self.get_resource_img(img_link, end, name)
        if self.mp3_var.get():
            self.get_resource_mp3(audio_url, name)
        if self.mp4_var.get():
            self.get_resource_mp4(video_url, audio_url, name)
        if not self.stop_download:
            messagebox.showinfo("提示", "下载完成！")
        self.is_downloading = False
        self.stop_download = False
        self.is_paused = False
        self.download_button.config(text="开始下载", background="lightblue")
        self.kill_button.pack_forget()
        self.progress.pack_forget()
        self.downloaded_size = 0
        self.update_progress()
        self.total_size = 0

    # def on_closing(self):
    #     if self.is_downloading:
    #         if messagebox.askyesno("确认退出", "当前有下载任务正在进行，是否退出？"):
    #             # 通知下载线程停止
    #             self.stop_download = True
    #             # 提示用户等待
    #             messagebox.showinfo("提示", "正在关闭，请稍候…")
    #             self.download_thread.join()  # 等待线程结束
    #             self.is_downloading = False
    #             self.master.destroy()  # 销毁整个窗口
    #         else:
    #             return  # 用户取消关闭，直接返回
    #     else:
    #         pid = get_proxy_pid()
    #         self.kill_process(pid)
    #         self.master.destroy()  # 无任务时直接销毁窗口

    # def kill_process(self, pid):
    #     try:
    #         process = psutil.Process(pid)
    #         process.terminate()  # 优雅终止
    #         process.wait(timeout=5)  # 等待最多5秒
    #         print(f"Process {pid} terminated.")
    #     except psutil.NoSuchProcess:
    #         print(f"No process with PID {pid} exists.")
    #     except psutil.AccessDenied:
    #         print(f"Permission denied to terminate process {pid}.")
    #     except psutil.TimeoutExpired:
    #         print(f"Process {pid} did not terminate in time. Forcing...")
    #         process.kill()  # 强制杀死
    #         print(f"Process {pid} killed.")

    # def get_is_downloading(self):
    #     return self.is_downloading
    
    # def set_stop_download(self):
    #     self.stop_download = True

    # def set_is_downloading(self):
    #     self.is_downloading = False

    # 进度条
    def update_progress(self):
        self.progress['value'] = (self.downloaded_size / self.total_size) * 100
        self.update_idletasks()

    # 在线试听功能实现
    def start_play_audio_thread(self):
        if not is_vlc_path()[0]:
            messagebox.showwarning("警告", "vlc.exe路径未设置，部分功能将无法使用！")
            return
        else:
            self.vlc_path = is_vlc_path()[1]
        self.play_thread = threading.Thread(target=self.play_audio)
        # self.play_thread.daemon = True 
        self.play_thread.start()
    # 异步协程实现   
    def play_audio(self):
        url = self.url_entry.get()
        title = "null"
        if url == "输入视频链接(必要)" or not url.strip():
            messagebox.showwarning("警告", "请输入视频链接！")
            return
        # audio_stream,size1,title= get_resource_can(url)
        _, _, _, audio_stream, title = get_resource(url)
        # if audio_stream:
        self.play_audio_process(audio_stream, title)
        # else:
        #     result = get_audio_can(self.video_list, size1)
        #     if result == "null":
        #         messagebox.showwarning("警告", "该页面暂无可用音频流，可选择其他页面，或自行下载！")
        #         return
        #     for dict in result:
        #         audio_stream = dict.get("audio_stream")
        #         title = dict.get("title")
        #         # print(title)
        #         self.play_audio_process(audio_stream, title)
        
    def play_audio_process(self, audio_stream, title):
        vlc_command = [
            self.vlc_path,
            "--one-instance",
            "--playlist-enqueue",
            "--rate=1.0",
            "--meta-title=" + title,
            audio_stream
        ]
        try:
            subprocess.Popen(vlc_command)  # 使用 Popen 启动 VLC 子进程，不会阻塞子线程
        except FileNotFoundError:
            print("找不到 VLC 程序，请确保 VLC 已安装并在系统路径中")

    # 在线观影
    def start_play_video_thread(self):
        if not is_vlc_path()[0]:
            messagebox.showwarning("警告", "vlc.exe路径未设置，部分功能将无法使用！")
            return
        else:
            self.vlc_path = is_vlc_path()[1]
        self.video_thread = threading.Thread(target=self.play_video)
        self.video_thread.start()
    
    def play_video(self):
        # video_url, audio_url, title= get_resource_tv(self.url_entry.get())
        _, _, video_url, audio_url, title = get_resource(self.url_entry.get())
        # if video_url == "" or audio_url == "":
        #     messagebox.showwarning("警告", "该视频不支持在线观看！")
        #     return
        vlc_command = [
            self.vlc_path,
            "--rate=1.0",
            "--no-video-title-show",
            "--input-title-format",
            title,
            "--input-slave=" + audio_url,
            video_url
        ]
        # print(video_url)
        # print(audio_url)
        try:
            subprocess.Popen(vlc_command)  # 使用 Popen 启动 VLC 子进程，不会阻塞子线程
        except FileNotFoundError:
            print("找不到 VLC 程序，请确保 VLC 已安装并在系统路径中")
    
    def check(self):
        if self.list_download_info is not None:
            content = filter_filename(self.list_download_info.title) + "|https:" + self.list_download_info.url + "\n"
            # 检查文件是否已经存在相同的内容
            with open("./history/list_download.txt", "r", encoding="utf-8") as f:
                existing_content = f.readlines()  # 读取所有行
            # 如果相同内容不在文件中，才追加
            if content not in existing_content:
                with open("./history/list_download.txt", "a", encoding="utf-8") as f:
                    f.write(content)
                    print(f"内容已添加：{content}")
            else:
                print("内容已存在，不做重复写入。")