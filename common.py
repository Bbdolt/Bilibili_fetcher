import re
import os
from tkinter import messagebox, filedialog
from lxml import etree
import requests
import json
import aiohttp
import asyncio
import time
import threading
import subprocess

# proxy_process = None

# def set_proxy_pid(pid):
#     global proxy_process
#     proxy_process = pid

# def get_proxy_pid():
#     global proxy_process
#     return proxy_process

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "referer": "https://www.bilibili.com/",
    "Cookie": ""
}

class VideoInfo:
    def __init__(self, name, view, length, author, url):
        self.name = name
        self.view = view
        self.length = length
        self.author = author
        self.url = url

class DownloadInfo:
    def __init__(self, no, title, length, author, url):
        self.no = no
        self.title = title
        self.length = length
        self.author = author
        self.url = url
class List_DownloadInfo:
    def __init__(self, title, url):
        self.title = title
        self.url = url

class Downloaditem:
    def __init__(self, link, save_path):
        self.link = link
        self.save_path = save_path
        
def filter_filename(filename):
    filtered_filename = re.sub(r'[^a-zA-Z0-9_.\u4e00-\u9fa5-]', '', filename)
    return filtered_filename


def update_ui_after_download(message):
    messagebox.showinfo("下载状态", message)

# 满足下载功能
def get_resource(url):
    print(headers)
    with requests.get(url, headers=headers, verify=False) as r:
        html = etree.HTML(r.text)
        img = html.xpath("/html/body/div[2]/script/text()")
        img_dict = json.loads(img[0])
        img_link = img_dict['thumbnailUrl'][0].split('@')[0]
        end = img_link.split('.')[-1]
        base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
        base_dict = json.loads(base_info)
        # print(base_dict["data"]["dash"]['video'])
        video_url = base_dict["data"]["dash"]['video'][0]["baseUrl"]
        audio_url = base_dict["data"]["dash"]['audio'][0]["baseUrl"]
        name = html.xpath("/html/head/title/text()")[0]
        name = filter_filename(name)
        print(audio_url)
        return img_link, end, video_url, audio_url, name
    
# 满足在线听歌功能
def get_resource_can(url):
    with requests.get(url, headers=headers, verify=False) as r:
        html = etree.HTML(r.text)
    base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
    base_dict = json.loads(base_info)
    audio_array= base_dict["data"]["dash"]['audio']
    name = html.xpath("/html/head/title/text()")[0]
    audio_len = len(audio_array)
    is_be = False
    i = 0
    audio_url = ""
    size = 0
    while not is_be and i < audio_len:
        a_url = audio_array[i]["baseUrl"]
        size = get_file_size(a_url, headers)
        if "/v1/resource/" in a_url:
            is_be = True
            audio_url = a_url
        i += 1
    # if "upgcxcode" in audio_url or audio_url == "":
    #     pattern = r'https://[^\s"]+/v1/resource/[^\s"]+'
    #     matches = re.findall(pattern, str(audio_array))
    #     if matches:
    #         audio_url = matches[0]
    return audio_url,size,name

# 满足在线tv功能
def get_resource_tv(url):
    with requests.get(url, headers=headers, verify=False) as r:
        html = etree.HTML(r.text)
    base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
    base_dict = json.loads(base_info)
    video_array= base_dict["data"]["dash"]['video']
    audio_array= base_dict["data"]["dash"]['audio']
    audio_len = len(audio_array)
    video_len = len(video_array)
    is_be_a = False
    is_be_v = False
    i = 0
    audio_url = ""
    video_url = ""
    name = html.xpath("/html/head/title/text()")[0]
    while not is_be_a and i < audio_len:
        a_url = audio_array[i]["baseUrl"]
        if "/v1/resource/" in a_url:
            is_be_a = True
            audio_url = a_url
        i += 1
    j = 0
    while not is_be_v and j < video_len:
        v_url = video_array[j]["baseUrl"]
        if "/v1/resource/" in v_url:
            is_be_v = True
            video_url = v_url
        j += 1
    return audio_url, video_url, name


async def get_resource_can_list(session, url, size1, can_list, lock):
    try:
        async with session.get(url, headers=headers) as r:
            if r.status != 200:
                raise ValueError(f"Request failed with status code {r.status}")
            text = await r.text()
            html = etree.HTML(text)
            base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
            base_dict = json.loads(base_info)
            audio_array = base_dict["data"]["dash"]['audio']
            name = html.xpath("/html/head/title/text()")[0]
            
            for audio in audio_array:
                a_url = audio["baseUrl"]
                if "/v1/resource/" in a_url:
                    size2 = await get_file_size_async(a_url, headers)
                    if size2 - size1 < 8388608:
                        async with lock:  # 使用锁来保护共享资源
                            can_list.append({'audio_stream': a_url, 'title': name})
                            return  # 直接返回，不继续查找
    except Exception as e:
        print(f"处理 URL {url} 时出错: {e}")

async def get_audio_can_list(video_list, size1):
    can_list = []
    lock = asyncio.Lock()  # 创建一个锁来保护共享资源
    async with aiohttp.ClientSession() as session:  # 确保 session 在这里创建并可用于所有任务
        tasks = [get_resource_can_list(session, "https:" + video.url[0], size1, can_list, lock) for video in video_list]
        await asyncio.gather(*tasks)  # 等待所有任务完成
    return can_list if can_list else None

def get_audio_can(video_list, size1):
    return asyncio.run(get_audio_can_list(video_list, size1))

async def get_file_size_async(url, headers):
    headers_range = {'Range': 'bytes=0-5'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={**headers, **headers_range}) as r:
                content_range = r.headers.get('Content-Range', '')
                if not content_range:
                    raise ValueError("Failed to fetch Content-Range header")
                filesize = content_range.split('/')[-1]
                return int(filesize)
    except Exception as e:
        print(f"获取文件大小时出错: {e}")
        return 0  # 返回 0 作为默认值，避免程序崩溃

def get_file_size(url, head):
    headers_range = {'Range': f"bytes=0-5"}
    with requests.get(url, headers={**head, **headers_range}, stream=True, verify=False) as r_filesize:
        filesize = r_filesize.headers['Content-Range'].split('/')[-1]
    return int(filesize)


def check_dir(folder_name):
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name)


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)

def read_config():
    filename = './config/config.ini'
    config = {}
    if not os.path.exists(filename):
        messagebox.showerror("错误", "配置文件不存在！")
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                # 去除行尾的换行符并分割键和值
                parts = line.strip().split(': ', 1)
                if len(parts) == 2:  # 确保分割成功
                    key, value = parts
                    config[key] = value
    except Exception as e:
        messagebox.showerror("错误", f"读取配置文件失败: {e}")
        return None
    # 返回需要的配置
    return config.get('Cookie', 'Not found'), config.get('vlc_path', 'Not found'), config.get('idm_path', 'Not found')


# 保存配置信息
def write_config(new_cookie, new_vlc_path, new_idm_path):
    filename = './config/config.ini'
    # 读取配置文件
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    # 校验条件
    can_c = cookie_invalid(new_cookie)
    can_v = os.path.exists(new_vlc_path)
    can_i = os.path.exists(new_idm_path)
    # 修改内容
    modified_lines = []
    for line in lines:
        if line.startswith('Cookie: '):
            if not can_c:  # 只有新 Cookie 有效时才修改
                modified_lines.append(f'Cookie: {new_cookie}\n')
            else:
                modified_lines.append(line)
        elif line.startswith('vlc_path: '):
            if can_v:  # 只有路径存在时才修改
                modified_lines.append(f'vlc_path: {new_vlc_path}\n')
            else:
                modified_lines.append(line)
        elif line.startswith('idm_path: '):
            if can_i:  # 只有路径存在时才修改
                modified_lines.append(f'idm_path: {new_idm_path}\n')
            else:
                modified_lines.append(line)
        else:
            modified_lines.append(line)

    # 将修改后的内容写回文件
    with open(filename, 'w', encoding='utf-8') as file:
        file.writelines(modified_lines)
    messagebox.showinfo("提示", "配置保存成功！")

# Cookie 操作
# 获取 Cookie 中的时间戳
def get_bili_ticket_expires(cookies):
    # 使用正则表达式查找bili_ticket_expires字段
    match = re.search(r'bili_ticket_expires=(\d+);', cookies)
    if match:
        return int(match.group(1))  # 返回时间戳
    return None

# 判断cookie是否过期
def is_cookie_expired(expiration_timestamp):
    current_timestamp = int(time.time())  # 获取当前的UNIX时间戳
    return current_timestamp > expiration_timestamp

# 判断配置文件中的 cookie 是否过期
def is_cookie_old():
    cookies = read_config()[0]
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

# 判断输入框中的 cookie 是否有效
def cookie_invalid(cookie):
    # 获取bili_ticket_expires字段的值
    expiration_timestamp = get_bili_ticket_expires(cookie)
    if expiration_timestamp is None:
        return True
    else:
        # 判断Cookie是否过期
        if is_cookie_expired(expiration_timestamp):
            return True
        else:
            return False
        

# vlc_path 操作
# 判断vlc_path是否存在
def is_vlc_path():
    vlc_path = read_config()[1]
    if vlc_path == 'Not found' and not os.path.exists("./vlc/vlc.exe"):
        return False, None
    elif os.path.exists(vlc_path):
        return True, vlc_path
    elif os.path.exists("vlc/vlc.exe"):
        return True, "vlc/vlc.exe"
    else:
        return False, None
    
def is_idm_path():
    idm_path = read_config()[2]
    if idm_path == 'Not found' and not os.path.exists("./IDM/IDMan.exe"):
        return False, None
    elif os.path.exists(idm_path):
        return True, idm_path
    elif os.path.exists("IDM/IDMan.exe"):
        return True, "IDM/IDMan.exe"

def media_start_thread():
    info = is_vlc_path()
    
    if not info[0]:
        messagebox.showerror("错误", "vlc.exe路径不存在！")
        return
    else:
        threading.Thread(target=media_start,args=(info[1],), daemon=True).start()
    
def media_start(vlc_path):
    Media = filedialog.askdirectory(title="请选择播放目录")
    Media = Media.replace('/', '\\')
    
    if Media:
        vlc_command = [
            vlc_path,
            "--rate=1.0",
            Media
        ]
        print(vlc_command)
        subprocess.Popen(vlc_command)
    else:
        return


async def get_download_resource_start(download_list, dir_path, DownloadInfo_list):
    # 启动下载任务
    lock = asyncio.Lock()  # 创建一个锁
    async with aiohttp.ClientSession() as session:
        tasks = [get_download_resource_run(session, x.url, x.title, dir_path, DownloadInfo_list, lock) for x in download_list]
        await asyncio.gather(*tasks)

async def get_download_resource_run(session, url, title, dir_path, DownloadInfo_list, lock):
    sem = asyncio.Semaphore(33)
    # 先发起请求，获取数据
    try:
        async with sem:
            async with session.get(url, headers=headers) as r:
                # 如果请求失败，返回
                if r.status != 200:
                    print(f"请求失败: {url}")
                    return
                
                html = etree.HTML(await r.text())
                base_info = "".join(html.xpath("/html/head/script[4]/text()"))[20:]
                base_dict = json.loads(base_info)
                # print(headers)
                # print(base_dict["data"]["dash"]['video'])
                video_url = base_dict["data"]["dash"]['video'][0]["baseUrl"]
                audio_url = base_dict["data"]["dash"]['audio'][0]["baseUrl"]

                title = filter_filename(title)
                save_path_mp4 = (dir_path + '/' + title + '.mp4').replace('/', '\\')
                save_path_mp3 = (dir_path + '/' + title + '.m4a').replace('/', '\\')

                # 在访问 DownloadInfo_list 时加锁，确保线程安全
                async with lock:
                    DownloadInfo_list.append(Downloaditem(video_url, save_path_mp4))
                    DownloadInfo_list.append(Downloaditem(audio_url, save_path_mp3))

    except Exception as e:
        print(f"下载资源时发生错误: {e}")




