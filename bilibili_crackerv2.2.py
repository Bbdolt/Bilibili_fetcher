import requests
from lxml import etree
import json
import tkinter as tk
from tkinter import filedialog, ttk, scrolledtext, messagebox
import webbrowser
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO
import vlc
import threading
import time
import re
import os

# 用来控制暂停/继续下载的标志
is_paused = False
is_downloading = False
download_thread = None
stop_download = False  # 用于标识是否取消下载

headers = {
    "Cookie": "",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Referer": "https://www.bilibili.com/"
}


def update_ui_after_download(result):
    messagebox.showinfo("下载完成", result)


# 创建VLC播放器实例
instance = vlc.Instance()
player = instance.media_player_new()

# 音频播放状态
is_playing = False
play_thread = None  # 存储音频播放线程


# 格式化时间
def format_time(seconds):
    minutes = int(seconds) // 60
    seconds = int(seconds) % 60
    return f"{minutes:02}:{seconds:02}"


# 更新音频进度
def update_progress():
    if player.is_playing():
        current_time = player.get_time() / 1000  # 转换为秒
        total_time = player.get_length() / 1000  # 总时长，单位秒
        current_time_label.config(text=f"{format_time(current_time)} / {format_time(total_time)}")
    if is_playing:
        play_window.after(1000, update_progress)  # 每秒更新


# 播放/暂停功能
def toggle_play_pause():
    global is_playing
    if is_playing:
        player.pause()
        play_pause_button.config(text="播放")
        status_label.config(text="状态：暂停播放")
    else:
        player.play()
        play_pause_button.config(text="暂停")
        status_label.config(text="状态：正在播放")
    is_playing = not is_playing


# 播放音频的子线程
def play_audio_thread():
    global is_playing, play_window

    try:
        # 获取 URL 并验证
        url = url_entry.get()
        # 请求音频资源并解析
        response = requests.get(url, headers=headers)
        if response.status_code == 403:
            raise Exception("HTTP 403 错误：访问被拒绝")
        response.raise_for_status()

        # 解析 HTML 获取音频 URL
        html = etree.HTML(response.text)
        base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
        base_dict = json.loads(base_info)
        audio_array= base_dict["data"]["dash"]['audio']
        audio_len = len(audio_array)
        is_be = False
        i = 0
        audio_url = ""
        while not is_be and i < audio_len:
            a_url = audio_array[i]["baseUrl"]
            print(a_url)
            if "resource" in a_url:
                is_be = True
                audio_url = a_url
            i += 1
        

        if "upgcxcode" in audio_url or audio_url == "":
            pattern = r'https://[^\s"]+/v1/resource/[^\s"]+'
            matches = re.findall(pattern, response.text)
            if matches:
                audio_url = matches[0]

        if "upgcxcode" in audio_url or audio_url == "":
            s_status_label = tk.Label(play_window, text="提示：该音频可能不支持在线播放，请自行下载")
            s_status_label.pack(pady=10)


        # 使用 VLC 播放音频流
        media = instance.media_new(audio_url)
        player.set_media(media)
        player.play()

        # 更新 UI 状态
        status_label.config(text="状态：正在播放")
        is_playing = True
        play_pause_button.config(text="暂停")
        update_progress()

    except Exception as e:
        print(f"播放失败: {e}")
        messagebox.showerror("错误", f"无法播放音频：{e}")
        status_label.config(text="音频播放失败")
        play_pause_button.config(text="播放")


# 子窗口关闭时停止播放
def on_close_play_window():
    global is_playing

    if player.is_playing():
        player.stop()  # 停止播放
    is_playing = False
    play_window.destroy()  # 关闭子窗口
    status_label.config(text="状态：等待播放")


# 点击“导入音频”按钮时打开新窗口并创建子线程
def play_audio_from_url():
    url = url_entry.get()
    if url == "输入视频链接(必要)" or url == "":
        messagebox.showwarning("警告", "请输入视频链接！")
        return
    global play_window, current_time_label, play_pause_button, play_thread

    # 创建子窗口
    play_window = tk.Toplevel(root)
    play_window.title("音乐盒子")
    play_window.iconbitmap('ico/favicon.ico')
    play_window.geometry("300x150")
    root.update_idletasks()  # 确保获取到窗口更新后的宽高
    root_x = root.winfo_x()
    root_y = root.winfo_y()
    root_width = root.winfo_width()
    root_height = root.winfo_height()

    # 在子窗口显示提示
    # s_status_label = tk.Label(play_window, text="提示：有些音频不支持，请自行下载")
    # s_status_label.pack(pady=10)

    # 播放/暂停按钮
    play_pause_button = tk.Button(play_window, text="播放", command=toggle_play_pause)
    play_pause_button.pack(pady=10)

    # 当前时间标签
    current_time_label = tk.Label(play_window, text="00:00 / 00:00", width=20)
    current_time_label.pack(pady=10)

    # 启动音频播放的子线程
    play_thread = threading.Thread(target=play_audio_thread)
    play_thread.daemon = True
    play_thread.start()

    # 子窗口关闭事件绑定
    play_window.protocol("WM_DELETE_WINDOW", on_close_play_window)


class VideoInfo:
    def __init__(self, name, view, length, author, url):
        self.name = name
        self.view = view
        self.length = length
        self.author = author
        self.url = url


def clear_tree():
    for i in tree.get_children():
        tree.delete(i)


# 更新表格内容
def update_tree(video_list):
    clear_tree()
    for video in video_list:
        tree.insert('', tk.END, values=(video.name, video.view, video.length, video.author, video.url))


def search_in_thread():
    # 启动一个子线程来运行 search 函数
    search_thread = threading.Thread(target=search)
    search_thread.start()


def search():
    keyword = search_entry.get()
    names = []
    views = []
    lengths = []
    authors = []
    urls = []
    try:
        with requests.get(f'https://search.bilibili.com/video?keyword={keyword}', headers=headers) as r:
            html_element = etree.HTML(r.text)
            parent_div = html_element.xpath('/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]')
            if parent_div:
                div_count = len(parent_div[0].xpath('div'))
                for i in range(1, div_count + 1):
                    names.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/div/div/a/h3/@title'))
                    views.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/a/div/div[2]/div/div/span[1]/span/text()'))
                    lengths.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/a/div/div[2]/div/span/text()'))
                    authors.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/div/div/p/a/span[1]/text()'))
                    urls.append(html_element.xpath(f'/html/body/div[3]/div/div[2]/div[2]/div/div/div[1]/div[{i}]/div/div[2]/a/@href'))
                video_list = [VideoInfo(names[i], views[i], lengths[i], authors[i], urls[i]) for i in range(len(names))]
                update_tree(video_list)
            else:
                messagebox.showwarning("警告", "未找到相关视频！")
    except Exception as e:
        messagebox.showerror("错误", f"搜索过程中发生错误：{e}")
    finally:
        pass


def filter_filename(filename):
    filtered_filename = re.sub(r'[^a-zA-Z0-9_.\u4e00-\u9fa5-]', '', filename)
    return filtered_filename


def is_having(file_path):
    # 检查文件是否存在
    if os.path.exists(file_path):
        # 弹出确认框询问是否覆盖
        overwrite = messagebox.askyesno("确认覆盖", f"文件 '{file_path}' 已经存在，是否要覆盖？")
        if not overwrite:
            return False  # 如果用户选择不覆盖，则返回
        else:
            return True  # 如果用户选择覆盖，则返回
    else:
        return True


def save_file_with_confirmation(file_path, content):
    if is_having(file_path):
        with open(file_path, "wb") as f:
            f.write(content)


def get_resource_mp4():
    url = url_entry.get()
    file_save_path = save_path_entry.get()
    with requests.get(url, headers=headers) as r:
        html = etree.HTML(r.text)
        base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
        base_dict = json.loads(base_info)
        video_url = base_dict["data"]["dash"]['video'][0]["baseUrl"]
        audio_url = base_dict["data"]["dash"]['audio'][0]["baseUrl"]
        name = html.xpath("/html/head/title/text()")[0]
        name = filter_filename(name)
        with requests.get(video_url, headers=headers) as p:
            with open('./mp4/video.mp4', "wb") as f:
                f.write(p.content)
        if file_save_path != "请输入保存路径(非必要)" and file_save_path != "":
            with requests.get(audio_url, headers=headers) as p:
                save_file_with_confirmation(f"{file_save_path}/{name}.mp3", p.content)
        else:
            with requests.get(audio_url, headers=headers) as p:

                save_file_with_confirmation(f"./mp3/{name}.mp3", p.content)
    if file_save_path != "请输入保存路径(非必要)" and file_save_path != "":
        os.system(f"ffmpeg\\ffmpeg.exe -y -i ./mp4/video.mp4 -i {file_save_path}/{name}.mp3 -c copy {file_save_path}/{name}.mp4")
    else:
        os.system(f"ffmpeg\\ffmpeg.exe -y -i ./mp4/video.mp4 -i ./mp3/{name}.mp3 -c copy ./mp4/{name}.mp4")
    print(name + "已经下载完成了！")
    os.remove("./mp4/video.mp4")
    if mp3_var.get():
        pass
    else:
        if file_save_path != "请输入保存路径(非必要)" and file_save_path != "":
            os.remove(f"{file_save_path}/{name}.mp3")
        else:
            os.remove(f"./mp3/{name}.mp3")


def get_resource_mp3():
    url = url_entry.get()
    file_save_path = save_path_entry.get()
    with requests.get(url, headers=headers) as r:
        html = etree.HTML(r.text)
        base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
        base_dict = json.loads(base_info)
        video_url = base_dict["data"]["dash"]['video'][0]["baseUrl"]
        audio_url = base_dict["data"]["dash"]['audio'][0]["baseUrl"]
        name = html.xpath("/html/head/title/text()")[0]
        name = filter_filename(name)
        with requests.get(audio_url, headers=headers) as p:
            if file_save_path != "请输入保存路径(非必要)" and file_save_path != "":
                save_file_with_confirmation(f"{file_save_path}/{name}.mp3", p.content)
            else:
                save_file_with_confirmation(f"./mp3/{name}.mp3", p.content)
    print(name + "已经下载完成了！")


def get_resource_img():
    url = url_entry.get()
    file_save_path = save_path_entry.get()
    with requests.get(url, headers=headers) as r:
        html = etree.HTML(r.text)
        img = html.xpath("/html/body/div[2]/script/text()")
        img_dict = json.loads(img[0])
        img_link = img_dict['thumbnailUrl'][0].split('@')[0]
        end = img_link.split('.')[-1]
        name = html.xpath("/html/head/title/text()")[0]
        name = filter_filename(name)
        with requests.get(img_link, headers=headers) as p:
            if file_save_path != "请输入保存路径(非必要)" and file_save_path != "":
                save_file_with_confirmation(f"{file_save_path}/{name}.{end}", p.content)
            else:
                save_file_with_confirmation(f"./img/{name}.{end}", p.content)
    print(name + "已经下载完成了！")


def select_default_path():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        save_path_entry.delete(0, tk.END)
        save_path_entry.insert(0, folder_selected)


def download_both():
    global is_downloading, download_thread
    if not is_downloading:
        # 开始下载时修改按钮文字和颜色
        download_button.config(text="正在下载", background="orange", state=tk.DISABLED)
        is_downloading = True
        download_thread = threading.Thread(target=download_both_thread)
        download_thread.daemon = True  # 确保主窗口关闭时线程会退出
        download_thread.start()
    else:
        # 如果正在下载，点击按钮暂停或继续
        global is_paused
        is_paused = not is_paused
        if is_paused:
            download_button.config(text="继续下载", background="lightgreen")
        else:
            download_button.config(text="暂停下载", background="orange")


def download_both_thread():
    global stop_download  # 使用 stop_download 标志来控制下载
    try:
        url = url_entry.get()
        if url == "输入视频链接(必要)" or url_entry.get() == "":
            messagebox.showwarning("警告", "请输入视频链接！")
            return
        if not (mp4_var.get() or mp3_var.get() or img_var.get()):
            messagebox.showwarning("警告", "请选择下载资源类型！")
            return

        if img_var.get():
            if stop_download:
                return
            get_resource_img()
            if stop_download:
                return
            if mp4_var.get() or mp3_var.get():
                pass
            else:
                update_ui_after_download("图片下载成功!")
        if mp4_var.get():
            if stop_download:
                return
            get_resource_mp4()
            if stop_download:
                return
            update_ui_after_download("视频下载成功!")
            return
        if mp3_var.get():
            if stop_download:
                return
            get_resource_mp3()
            if stop_download:
                return
            update_ui_after_download("音频下载成功!")
    except Exception as e:
        messagebox.showerror("错误", f"下载过程中发生错误：{e}")
    finally:
        global is_downloading
        is_downloading = False
        stop_download = False  # 重置标志
        download_button.config(text="开始下载", background="lightblue", state=tk.NORMAL)


# 关闭窗口时取消下载
def on_close():
    global is_downloading, stop_download
    if is_downloading:
        stop_download = True  # 设置停止下载标志
        if download_thread and download_thread.is_alive():
            # 在这里可以通过某种机制（例如设置标志）停止下载线程
            pass
        download_button.config(text="开始下载", background="lightblue", state=tk.NORMAL)
    root.destroy()


def update_ui_after_download(message):
    messagebox.showinfo("下载状态", message)


# 通用事件处理函数，支持多个输入框和占位符文本
def on_focus_in(event, entry, default_text):
    if entry.get() == default_text:
        entry.delete(0, tk.END)  # 清空占位符
        entry.config(fg='black')  # 设置字体为黑色


def on_focus_out(event, entry, default_text):
    if entry.get() == "":  # 当输入框为空时，显示占位符
        entry.insert(0, default_text)
        entry.config(fg='grey')
    elif entry.get() != default_text:  # 当输入框不为空且内容不等于占位符时，设为黑色
        entry.config(fg='black')


def on_double_click(event):
    # 获取当前选中的 item
    item_id = tree.selection()
    if item_id:
        # 获取选中行的所有数据 (一个元组)
        row_data = tree.item(item_id, "values")
        # 确保访问 "values" 返回的是一个元组
        if len(row_data) >= 5:
            url = row_data[4]  # 第5列是 URL
            # 清空并插入 URL 到输入框
            url_entry.delete(0, tk.END)
            if url.startswith('//'):
                url = 'https:' + url
            url_entry.insert(0, url)
            url_entry.config(fg='black')  # 将文本颜色设置为黑色
            video_name = row_data[0]  # 第1列是名称
            video_name = filter_filename(video_name)
            


def Online_player():
    url = url_entry.get()
    if url == "输入视频链接(必要)" or url_entry.get() == "":
        messagebox.showwarning("警告", "请输入视频链接！")
        return
    with requests.get(url, headers=headers) as r:
        html = etree.HTML(r.text)
        base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
        base_dict = json.loads(base_info)
        audio_url = base_dict["data"]["dash"]['audio'][0]["baseUrl"]
        name = html.xpath("/html/head/title/text()")[0]
        name = filter_filename(name)
    with requests.get(url, headers=headers, stream=True) as p:
        if p.status_code == 200:
            audio_data = BytesIO(p.content)
            audio = AudioSegment.from_file(audio_data, format="mp3")
            play(audio)
        else:
            print("无法获取音频文件")


def read_cookie_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        cookies = file.read()
    return cookies


def get_bili_ticket_expires(cookies):
    # 使用正则表达式查找bili_ticket_expires字段
    match = re.search(r'bili_ticket_expires=(\d+);', cookies)
    if match:
        return int(match.group(1))  # 返回时间戳
    return None


def is_cookie_expired(expiration_timestamp):
    current_timestamp = int(time.time())  # 获取当前的UNIX时间戳
    return current_timestamp > expiration_timestamp


def is_cookie_old():
    cookie_file_path = 'Cookie/Cookie.txt'

    # 读取Cookie文件
    cookies = read_cookie_file(cookie_file_path)

    # 获取bili_ticket_expires字段的值
    expiration_timestamp = get_bili_ticket_expires(cookies)

    if expiration_timestamp is None:
        return True
    else:
        # 判断Cookie是否过期
        if is_cookie_expired(expiration_timestamp):
            return True
        else:
            return False


def cookie_invalid():
    ck = cookie_entry.get()
    # 获取bili_ticket_expires字段的值
    expiration_timestamp = get_bili_ticket_expires(ck)
    if expiration_timestamp is None:
        return True
    else:
        # 判断Cookie是否过期
        if is_cookie_expired(expiration_timestamp):
            return True
        else:
            return False


def insert_cookie():
    if cookie_invalid():
        messagebox.showwarning("警告", "Cookie已过期，请重新输入！")
        return
    cookie_file_path = 'Cookie/Cookie.txt'
    with open(cookie_file_path, 'w', encoding='utf-8') as file:
        file.write(cookie_entry.get())
    messagebox.showinfo("提示", "Cookie保存成功！")
    headers['Cookie'] = cookie_entry.get()


def open_blog():
    webbrowser.open("https://Bbdolt.github.io/")


def open_blog_thread():
    threading.Thread(target=open_blog, daemon=True).start()

def open_readme_thread():
    threading.Thread(target=show_message, daemon=True).start()

def show_message():
    current_directory = os.getcwd()
    readme_path = os.path.join(current_directory, 'README.txt')
    
    # 检查 README.md 文件是否存在
    if os.path.exists(readme_path):
        # 使用 webbrowser 打开 README.md 文件（在浏览器或默认应用中查看）
        webbrowser.open('file://' + readme_path)
    else:
        print("README.md 文件未找到！")

class MusicPlayerApp:
    def __init__(self, play_frame):
        self.is_loop = False  # 是否循环播放
        self.play_frame = play_frame
        # 添加按钮，点击后弹出子窗口
        self.open_button = tk.Button(play_frame, text="本地播放", command=self.v_open_child_window)
        self.open_button.pack(pady=20)

        # 创建VLC播放器实例
        self.player = vlc.MediaPlayer()

        # 当前播放的索引和音频文件列表
        self.current_index = -1
        self.mp3_files = []

    def v_open_child_window(self):
        # 选择歌单
        # 弹出窗口让用户选择歌单路径
        folder_path = filedialog.askdirectory(initialdir="./mp3", title="选择歌单目录")
        
        # 如果没有选择路径，直接返回
        if not folder_path:
            return

        # 检查路径是否存在且是否包含MP3文件
        if not os.path.exists(folder_path):
            messagebox.showerror("错误", "所选路径不存在！")
            return

        # 获取MP3文件列表
        mp3_files = [f for f in os.listdir(folder_path) if f.endswith('.mp3')]
        
        if not mp3_files:
            messagebox.showerror("错误", "所选目录下没有MP3文件！")
            return

        # 记录歌单路径
        self.music_folder = folder_path
        self.mp3_files = mp3_files

        # 创建子窗口
        child_window = tk.Toplevel(self.play_frame)
        child_window.title("音乐盒子")
        child_window.iconbitmap('./ico/favicon.ico')

        child_window.geometry("400x300")

        # 创建列表框，显示./mp3目录下的文件
        file_listbox = tk.Listbox(child_window)
        file_listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 使用线程来加载文件
        def load_mp3_files():
            try:
                self.mp3_files = [f for f in os.listdir(self.music_folder) if f.endswith('.mp3')]
                for mp3 in self.mp3_files:
                    file_listbox.insert(tk.END, mp3)
            except FileNotFoundError:
                messagebox.showerror("错误", f"{self.music_folder}目录不存在")
                return

        # 创建并启动线程
        threading.Thread(target=load_mp3_files, daemon=True).start()

        # 创建暂停/播放按钮
        self.play_pause_button = tk.Button(child_window, text="播放", command=lambda: self.v_toggle_play_pause())
        self.play_pause_button.pack(side=tk.LEFT, padx=20, pady=20)

        # 设置播放模式
        self.loop_button = tk.Button(child_window, text="顺序播放ing", command=lambda: self.v_toggle_loop())
        self.loop_button.pack(side=tk.LEFT, padx=20, pady=20)

        # 创建播放进度标签
        self.progress_label = tk.Label(child_window, text="00:00 / 00:00")
        self.progress_label.pack(side=tk.LEFT, padx=20, pady=20)

        # 绑定双击事件，播放音频
        file_listbox.bind("<Double-1>", lambda event: self.v_play_audio(file_listbox.curselection()[0]))

        # 保存子窗口引用，用于关闭时停止播放
        child_window.protocol("WM_DELETE_WINDOW", lambda: self.v_on_child_window_close(child_window))

    def v_toggle_loop(self):
        self.is_loop = not self.is_loop
        if self.is_loop:
            self.loop_button.config(text="循环播放ing")
        else:
            self.loop_button.config(text="单曲循环ing")

    def v_play_audio(self, index):
        if index < 0 or index >= len(self.mp3_files):
            return

        self.current_index = index  # 更新当前索引
        filename = self.mp3_files[self.current_index]
        file_path = os.path.join(self.music_folder, filename)
        
        if os.path.exists(file_path):
            media = vlc.Media(file_path)
            self.player.set_media(media)
            self.player.play()
            self.current_media = media
            self.is_playing = True
            self.is_paused = False
            self.v_update_progress()

            # 更新按钮文本为“暂停”
            self.play_pause_button.config(text="暂停")
        else:
            messagebox.showerror("错误", f"文件 {filename} 不存在")

    def v_toggle_play_pause(self):
        if self.is_playing:
            if self.is_paused:
                self.player.play()  # 继续播放
                self.play_pause_button.config(text="暂停")
                self.is_paused = False
            else:
                self.player.pause()  # 暂停
                self.play_pause_button.config(text="播放")
                self.is_paused = True

    def v_update_progress(self):
        """更新播放进度标签"""
        if self.is_playing and self.current_media:
            length = self.player.get_length() / 1000  # 总时长，单位为秒
            current_time = self.player.get_time() / 1000  # 当前播放时间，单位为秒
            current_time_str = self.v_format_time(current_time)
            length_str = self.v_format_time(length)
            self.progress_label.config(text=f"{current_time_str} / {length_str}")

            # 检查是否播放完毕
            if self.player.get_state() == vlc.State.Ended:
                self.is_playing = False
                self.is_paused = False
                self.play_pause_button.config(text="播放")
                self.progress_label.config(text=f"00:00 / {length_str}")
                
                # 播放下一首歌曲
                self.play_next_song()

            # 每100毫秒更新一次进度
            if self.is_playing:
                self.play_frame.after(100, self.v_update_progress)

    def play_next_song(self):
        """播放下一首歌曲"""
        if self.is_loop:
            self.v_play_audio(self.current_index)
            return
        if self.current_index < len(self.mp3_files) - 1:
            self.current_index += 1
            self.v_play_audio(self.current_index)
        else:
            messagebox.showinfo("播放完毕", "已播放所有歌曲")

    def v_format_time(self, seconds):
        """将秒数格式化为mm:ss格式"""
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02}:{seconds:02}"

    def v_on_child_window_close(self, child_window):
        """子窗口关闭时停止播放音乐"""
        if self.is_playing:
            self.player.stop()
            self.is_playing = False
            self.is_paused = False
        child_window.destroy()



root = tk.Tk()
root.protocol("WM_DELETE_WINDOW", on_close)
root.title("B站资源下载器_Bbdolt")
root.geometry("1200x600")

icon_path = 'ico/favicon.ico'
root.iconbitmap(icon_path)

left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, anchor=tk.NW, padx=10, pady=5)

# 整体布局
####################################################

blogss_frame = tk.Frame(left_frame)
blogss_frame.pack(side=tk.BOTTOM, anchor=tk.NW, padx=10, pady=20)

blogs_frame = tk.Frame(left_frame)
blogs_frame.pack(side=tk.BOTTOM, anchor=tk.NW, padx=10, pady=20)

blog_frame = tk.Frame(blogs_frame)
blog_frame.pack(side=tk.LEFT, anchor=tk.NW, padx=5, pady=10)

md_button = tk.Button(blogss_frame, text="使用手册介绍", command=open_readme_thread)
md_button.config(background="green", foreground="black")  # 设置颜色
md_button.pack(side=tk.BOTTOM, padx=5, pady=5)

author_button = tk.Button(blogss_frame, text="Welcome to Myblog", command=open_blog_thread)
author_button.config(background="grey", foreground="black")
author_button.pack(side=tk.BOTTOM, padx=5, pady=5)

# 控制按钮
download_button = tk.Button(blog_frame, text="开始下载", command=download_both)
download_button.config(background="lightblue", foreground="black")  # 设置颜色
download_button.pack(side=tk.TOP, padx=0, pady=0)

# 当前时间/总时间标签

play_frame = tk.Frame(blogs_frame)
play_frame.pack(side=tk.RIGHT, anchor=tk.NW, padx=10, pady=5)

# current_time_label = tk.Label(play_frame, text="00:00 / 00:00", width=20)
# current_time_label.pack(side=tk.BOTTOM, pady=10)
# 状态标签
status_label = tk.Label(play_frame, text="状态：等待播放", width=40)
status_label.pack(side=tk.BOTTOM, pady=10)

# # 播放/暂停按钮
# play_pause_button = tk.Button(play_frame, text="在线播放", command=toggle_play_pause)
# play_pause_button.pack(side=tk.BOTTOM, padx=30, pady=5)

# 播放按钮
play_button = tk.Button(play_frame, text="在线播放", command=play_audio_from_url)
play_button.pack(side=tk.BOTTOM, padx=30, pady=5)

app = MusicPlayerApp(play_frame)
#################################################################


# 右边的表格
#################################################################

frame = tk.Frame(root)
frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
total_width = 800
# 创建表格
tree = ttk.Treeview(frame, columns=("Name", "View", "Length", "Author", "url"), show='headings')
tree.column("Name", width=int(total_width * 4 / 10), anchor="w")  # 4份
tree.column("View", width=int(total_width * 1 / 10), anchor="center")  # 1份
tree.column("Length", width=int(total_width * 1 / 10), anchor="center")  # 1份
tree.column("Author", width=int(total_width * 1 / 10), anchor="center")  # 1份
tree.column("url", width=int(total_width * 3 / 10), anchor="w")  # 3份
tree.heading("Name", text="标题")
tree.heading("View", text="观看量")
tree.heading("Length", text="视频长度")
tree.heading("Author", text="作者")
tree.heading("url", text="链接")
tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
# 创建垂直滚动条
vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
vsb.pack(side=tk.RIGHT, fill=tk.Y)
# 配置表格的滚动条
tree.configure(yscrollcommand=vsb.set)
# 绑定双击事件
tree.bind("<Double-1>", on_double_click)
####################################################################

# 搜索布局
####################################################################
default_search = '输入搜索关键词'
path_frame1 = tk.Frame(left_frame)  # 创建一个框架用于包含路径输入框和按钮
path_frame1.pack(pady=5)
search_entry = tk.Entry(path_frame1, width=44)
search_entry.pack(side=tk.LEFT)
search_button = tk.Button(path_frame1, text="搜索", command=search_in_thread)
search_button.pack(side=tk.RIGHT, padx=5)
search_entry.insert(0, default_search)
search_entry.config(fg='grey')  # 设置占位符文本颜色为灰色
search_entry.bind("<FocusIn>", lambda e: on_focus_in(e, search_entry, default_search))
search_entry.bind("<FocusOut>", lambda e: on_focus_out(e, search_entry, default_search))
####################################################################

# 视频链接布局
###################################################################
default_url = '输入视频链接(必要)'
url_entry = tk.Entry(left_frame, width=50)
url_entry.pack()
url_entry.pack(pady=5)
url_entry.insert(0, default_url)
url_entry.config(fg='grey')  # 设置占位符文本颜色为灰色
url_entry.bind("<FocusIn>", lambda e: on_focus_in(e, url_entry, default_url))
url_entry.bind("<FocusOut>", lambda e: on_focus_out(e, url_entry, default_url))
####################################################################


####################################################################
default_cookie = '输入B站Cookie(建议)'
path_frame2 = tk.Frame(left_frame)  # 创建一个框架用于包含路径输入框和按钮
path_frame2.pack(pady=5)
cookie_entry = tk.Entry(path_frame2, width=44)
cookie_entry.pack(side=tk.LEFT)
cookie_button = tk.Button(path_frame2, text="插入", command=insert_cookie)
cookie_button.pack(side=tk.RIGHT, padx=5)
cookie_entry.insert(0, default_cookie)
cookie_entry.config(fg='grey')  # 设置占位符文本颜色为灰色
cookie_entry.bind("<FocusIn>", lambda e: on_focus_in(e, cookie_entry, default_cookie))
cookie_entry.bind("<FocusOut>", lambda e: on_focus_out(e, cookie_entry, default_cookie))

default_path = '请输入保存路径(非必要)'
path_frame = tk.Frame(left_frame)  # 创建一个框架用于包含路径输入框和按钮
path_frame.pack(pady=5)
save_path_entry = tk.Entry(path_frame, width=47)
save_path_entry.pack(side=tk.LEFT, padx=5)
save_path_entry.insert(0, default_path)
save_path_entry.config(fg='grey')  # 设置占位符文本颜色为灰色
default_path_button = tk.Button(path_frame, text="...", command=select_default_path)
default_path_button.pack(side=tk.RIGHT)
default_path_button.config(width=2, height=1)
save_path_entry.bind("<FocusIn>", lambda e: on_focus_in(e, save_path_entry, default_path))
save_path_entry.bind("<FocusOut>", lambda e: on_focus_out(e, save_path_entry, default_path))

checkbox_frame = tk.Frame(left_frame)
checkbox_frame.pack(pady=5)
mp4_var = tk.BooleanVar()
mp3_var = tk.BooleanVar()
img_var = tk.BooleanVar()
mp3_var.set(True)
mp4_checkbutton = tk.Checkbutton(checkbox_frame, text="MP4", variable=mp4_var, onvalue=True, offvalue=False)
mp4_checkbutton.pack(side=tk.LEFT)
mp3_checkbutton = tk.Checkbutton(checkbox_frame, text="MP3", variable=mp3_var, onvalue=True, offvalue=False)
mp3_checkbutton.pack(side=tk.LEFT)
img_checkbutton = tk.Checkbutton(checkbox_frame, text="封面", variable=img_var, onvalue=True, offvalue=False)
img_checkbutton.pack(side=tk.LEFT)

if is_cookie_old():
    messagebox.showwarning("警告", "Cookie已过期或没有设置，请重新设置！")
else:
    cookie_entry.config(state='disabled')
    cookie_button.config(state='disabled')
    headers['Cookie'] = read_cookie_file('Cookie/Cookie.txt')



# download_button = tk.Button(left_frame, text="下载", command=download_both)
# download_button.pack()

root.mainloop()