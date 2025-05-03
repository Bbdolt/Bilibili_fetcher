# Bilibili_fetcher
B站资源免费获取、提供在线播放音乐、本地播放音乐
功能
```
- 支持下载B站资源
- 支持在线播放 视频、音频
- 支持列表下载、合集下载
- 本地播放
```
前置配置
```
1、配置 vlc 安装路径
	安装vlc找到vlc.exe的路径
	打开软件在配置文件中进行配置
2、配置 mitmproxy 证书
	打开文件资源管理器输入地址 %Userprofile%\.mitmproxy
	双击 mitmproxy-ca.p12
	当前用户 -> 下一步 -> 下一步 -> 下一步 -> 将所有证书都放入下列存储 -> 浏览 -> 受信任的
	根证书颁发机构 -> 下一步 -> 完成
3、配置 Cookie（可选）
	打开登录 bilibili
	F12 -> 控制台 -> 输入 console.log(document.cookie) -> 复制 Cookie
	打开软件进行配置
```
#### 功能
主界面
![PixPin_2025-01-04_18-17-11](https://github.com/user-attachments/assets/fe438303-4bf0-445a-8e7f-e049e0419adf)
列表下载
![PixPin_2025-01-04_18-20-18](https://github.com/user-attachments/assets/82427ece-893a-4245-b0d5-c7b11d6054e0)
合集下载
![PixPin_2025-01-04_18-24-05](https://github.com/user-attachments/assets/2993c413-ff5e-4e0d-b2c5-71d82964e63f)
本地播放库
![PixPin_2025-01-04_18-26-20](https://github.com/user-attachments/assets/641abe35-c024-4620-87f1-11232fca5c87)
配置
![PixPin_2025-01-04_18-27-30](https://github.com/user-attachments/assets/0c1e3968-5b0b-4f4b-90ef-43cd95e95fb8)



