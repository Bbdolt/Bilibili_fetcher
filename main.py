import tkinter as tk
from Views import *
from main_view import MainFrame
from common import *
from CollectionDownloadFrame import *
from ListDownloadFrame import *
import psutil

class MainPage:
    def __init__(self, master):
        self.root = master
        self.root.title("B站资源下载器_Bbdolt")
        self.root.geometry("1200x600")

        self.root.iconbitmap("ico/favicon.ico")
        # self.root.resizable(False, False)
        # 初始化 Frame 引用为 None
        self.main_frame = None
        # self.local_music_frame = None
        self.config_frame = None
        self.about_frame = None
        self.collection_download_frame = None
        self.list_download_frame = None
        self.proxy_thread = None  # 代理线程
        self.proxy_process = None

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        # 在启动时利用线程启动代理子程序
        self.set_vlc_config()
        self.kill_process_on_port(49152)
        self.start_proxy()

    def create_page(self):
        # 菜单栏
        menubar = tk.Menu(self.root)
        menubar.add_command(label="主界面", command=self.show_main)
        menubar.add_separator()
        # 创建批量下载的子菜单
        batch_download_menu = tk.Menu(menubar, tearoff=0)
        batch_download_menu.add_command(label="合集下载", command=self.show_collection_download)
        batch_download_menu.add_command(label="列表下载", command=self.show_list_download)
        menubar.add_cascade(label="批量下载", menu=batch_download_menu)  # 使用 add_cascade 添加子菜单
        menubar.add_separator()
        menubar.add_command(label="本地播放库", command=self.show_local_music)
        menubar.add_separator()
        menubar.add_command(label="配置", command=self.show_config)
        menubar.add_separator()
        menubar.add_command(label="关于", command=self.show_about)
        self.root.config(menu=menubar)

        self.show_about()

    def show_collection_download(self):
        if self.collection_download_frame is None:
            self.collection_download_frame = CollectionDownloadFrame(self.root)
        self.collection_download_frame.pack()
        # 隐藏其他页面
        if self.main_frame:
            self.main_frame.pack_forget()
        # if self.local_music_frame:
        #     self.local_music_frame.pack_forget()
        if self.config_frame:
            self.config_frame.pack_forget()
        if self.about_frame:
            self.about_frame.pack_forget()
        if self.list_download_frame:
            self.list_download_frame.pack_forget()
    
    def show_list_download(self):
        if self.list_download_frame is None:
            self.list_download_frame = ListDownloadFrame(self.root)
        self.list_download_frame.pack()
        self.list_download_frame.fresh_list()
        # 隐藏其他页面
        if self.main_frame:
            self.main_frame.pack_forget()
        # if self.local_music_frame:
        #     self.local_music_frame.pack_forget()
        if self.config_frame:
            self.config_frame.pack_forget()
        if self.about_frame:
            self.about_frame.pack_forget()
        if self.collection_download_frame:
            self.collection_download_frame.pack_forget()

    def show_main(self):
        # 延迟创建 MainFrame
        if self.main_frame is None:
            self.main_frame = MainFrame(self.root)
        self.main_frame.pack()

        # 隐藏其他页面
        # if self.local_music_frame:
        #     self.local_music_frame.pack_forget()
        if self.config_frame:
            self.config_frame.pack_forget()
        if self.about_frame:
            self.about_frame.pack_forget()
        if self.collection_download_frame:
            self.collection_download_frame.pack_forget()
        if self.list_download_frame:
            self.list_download_frame.pack_forget()

    def show_local_music(self):
        media_start_thread()

    def show_config(self):
        # 延迟创建 ConfigFrame
        if self.config_frame is None:
            self.config_frame = ConfigFrame(self.root)
        self.config_frame.pack()

        # 隐藏其他页面
        if self.main_frame:
            self.main_frame.pack_forget()
        # if self.local_music_frame:
        #     self.local_music_frame.pack_forget()
        if self.about_frame:
            self.about_frame.pack_forget()
        if self.collection_download_frame:
            self.collection_download_frame.pack_forget()
        if self.list_download_frame:
            self.list_download_frame.pack_forget()

    def show_about(self):
        # 延迟创建 AboutFrame
        if self.about_frame is None:
            self.about_frame = AboutFrame(self.root)
        self.about_frame.pack()

        # 隐藏其他页面
        if self.main_frame:
            self.main_frame.pack_forget()
        # if self.local_music_frame:
        #     self.local_music_frame.pack_forget()
        if self.config_frame:
            self.config_frame.pack_forget()
        if self.collection_download_frame:
            self.collection_download_frame.pack_forget()
        if self.list_download_frame:
            self.list_download_frame.pack_forget()

    def start_proxy(self):
        def run_proxy():
            proxy_command = [
                "mitmdump",
                "-p",
                "49152",
                "-s",
                "addons.py",
            ]
            try:
                self.proxy_process = subprocess.Popen(proxy_command)
                print("代理子进程已启动")
            except Exception as e:
                print("代理启动失败:", e)
        
        # 创建并启动代理线程
        self.proxy_thread = threading.Thread(target=run_proxy, daemon=True)
        self.proxy_thread.start()

    def on_closing(self):
        if self.main_frame is not None:
            if self.main_frame.is_downloading:
                if messagebox.askokcancel("关闭", "正在下载，是否退出？"):
                    self.main_frame.stop_download = True
                    self.main_frame.is_paused = True
                    messagebox.showinfo("提示", "正在关闭，请稍后...")
                    self.main_frame.download_thread.join()
                else:
                    return
        if self.collection_download_frame is not None:
            if self.collection_download_frame.aria2_downloading:
                if messagebox.askokcancel("关闭", "正在下载，是否退出"):
                    self.collection_download_frame.stop = True
                    self.collection_download_frame.shutdown = True
                    self.collection_download_frame.aria2_download_thread.join()
                    print("合集下载已经退出")
                else:
                    return
                
        if self.list_download_frame is not None:
            if self.list_download_frame.aria2_is_downloading:
                if messagebox.askokcancel("关闭", "正在下载，是否退出"):
                    self.list_download_frame.stop = True
                    self.list_download_frame.shutdown = True
                    self.list_download_frame.download_list_prepare.join()
                    print("列表下载已经退出")
                else:
                    return

        # 尝试关闭代理子进程
        if hasattr(self, 'proxy_process') and self.proxy_process is not None:
            try:
                print("正在关闭代理子进程...")
                self.proxy_process.terminate()  # 发送终止信号
                self.proxy_process.wait(timeout=2)  # 等待子进程退出
                print("代理子进程已正常关闭")
            except subprocess.TimeoutExpired:
                print("代理子进程未在 5 秒内关闭，强制终止...")
                self.proxy_process.kill()  # 强制终止子进程
                self.proxy_process.wait()  # 确保进程资源被回收
            except Exception as e:
                print("关闭代理子进程时发生错误:", e)
            finally:
                self.proxy_process = None  # 清理子进程引用
        self.kill_process_on_port(49152)
        self.clean_vlc_config()
        self.root.destroy()

    def set_vlc_config(self):
        def run_vlc_config():
            try:
                # 获取 APPDATA 路径并拼接 VLC 配置路径
                appdata_path = os.getenv("APPDATA")
                vlc_config_path = os.path.join(appdata_path, "vlc", "vlcrc")

                # 修改配置文件
                with open(vlc_config_path, "r+", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if line.startswith("http-proxy"):
                            lines[i] = "http-proxy=http://127.0.0.1:49152\n"

                    # 确保添加 http-proxy 配置
                    if not any(line.startswith("http-proxy") for line in lines):
                        lines.append("http-proxy=http://127.0.0.1:49152\n")

                    # 回写配置文件
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()

                print("VLC 配置更新成功")
            except Exception as e:
                print(f"配置 VLC 时出错: {e}")
        
        threading.Thread(target=run_vlc_config, daemon=True).start()
    
    def clean_vlc_config(self):
        def run_vlc_config():
            try:
                # 获取 APPDATA 路径并拼接 VLC 配置路径
                appdata_path = os.getenv("APPDATA")
                vlc_config_path = os.path.join(appdata_path, "vlc", "vlcrc")
                # 修改配置文件
                with open(vlc_config_path, "r+", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if line.startswith("http-proxy"):
                            lines[i] = "http-proxy=\n"
                    # 回写配置文件
                    f.seek(0)
                    f.writelines(lines)
                    f.truncate()

                print("VLC 代理清除成功")
            except Exception as e:
                print(f"配置 VLC 时出错: {e}")
        threading.Thread(target=run_vlc_config, daemon=True).start()

    def kill_process_on_port(self, port):
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                for conn in proc.connections(kind='inet'):
                    if conn.status == 'LISTEN' and conn.laddr.port == port:
                        pid = proc.info['pid']
                        print(f"Found process {proc.info['name']} with PID {pid} listening on port {port}")
                        proc.terminate()
                        # 检查进程是否已被终止
                        if proc.is_running():
                            proc.kill()
                            print(f"Force killed process with PID {pid}")
                        else:
                            print(f"Terminated process with PID {pid}")
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                print(f"Error accessing process {proc.info['pid']}: {e}")
                continue
        print(f"No process found listening on port {port}")
        return False
    
if __name__ == '__main__':
    root = tk.Tk()
    main_page = MainPage(root)
    main_page.create_page()
    root.mainloop()
