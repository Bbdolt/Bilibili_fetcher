from mitmproxy import http
from mitmproxy.tools.main import mitmdump

class Filter:
    def __init__(self):
        # 设置默认的 User-Agent 和 Referer
        self.new_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
        self.referer = "https://www.bilibili.com"
        # self.max = 0

    def request(self, flow: http.HTTPFlow):
        # 检查请求域名是否包含 "bilivideo"
        if "bilivideo" in flow.request.pretty_url:
            ua = flow.request.headers.get("User-Agent")
            if "VLC" in ua:
                range_header = flow.request.headers.get("range")
                range_header = range_header.replace("bytes=", "")
                range_header = range_header.split("-")
                start = int(range_header[0])
                flow.request.headers["range"] = "bytes=" + str(start) + "-" + str(start + 524288 - 1)
                # 修改 User-Agent
                flow.request.headers["User-Agent"] = self.new_user_agent 
                # 添加 Referer 头部
                flow.request.headers["referer"] = self.referer
            else:
                print("非VLC播放器")
                flow.request.headers["User-Agent"] = self.new_user_agent 
                flow.request.headers["referer"] = self.referer

# 创建一个代理处理器
addons = [
    Filter()
]

