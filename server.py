import re
import time
import json
import argparse
from threading import Thread, Lock
from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler

class CustomHandler(BaseHTTPRequestHandler):
    alert_record = { }

    def do_GET(self):
        length = int(self.headers['content-length'])
        info = json.loads(self.rfile.read(length).decode())
        slaver_address, _ = self.client_address
        lock.acquire()
        if slaver_address not in info_record:
            info_record[slaver_address] = {}
        info_record[slaver_address]['info'] = info
        info_record[slaver_address]['timestamp'] = time.time()
        lock.release()
        report_user()
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        return


def http_func():
    server = HTTPServer((opt.address, opt.port), CustomHandler)
    print("监听服务开启，按<Ctrl-C>退出")
    server.serve_forever()


def isExpire(timestamp):
    if time.time() - timestamp > opt.expiretime:
        return True
    return False


def report_user():
    usage_dict = { }
    usage_num = { }
    lock.acquire()
    for slaver_address in sorted(info_record.keys()):
        if isExpire(info_record[slaver_address]['timestamp']):
            continue
        pi_list = info_record[slaver_address]['info']['process']
        for pi in pi_list:
            username = pi['username']
            mem_usage = pi['mem_usage']
            gpu_id = pi['gpuid']
            usage_dict[username] = usage_dict.get(username, 0) + mem_usage
            if username in usage_num:
                usage_num[username].add(slaver_address + ':' + str(gpu_id))
            else:
                s = set()
                s.add(slaver_address + ':' + str(gpu_id))
                usage_num[username] = s
    lock.release()

    print('=' * 60)
    print(time.strftime('%Y-%m-%d %H:%M:%S\n', time.localtime(time.time())))
    usage_list = sorted(usage_dict.items(), key = lambda x: x[1], reverse=True)
    print('用户显存占用排序：')
    print('<用户ID> : <占用显存(MB)>')
    for username, usagememory in usage_list:
        print('%s : %dM' % (username, usagememory))
    # report1 = ['%s : %dM' % (n, u) for n, u in usage_list]
    # report1 = '\n'.join(report1)
    print()

    usage_num_list = sorted(usage_num.items(), key = lambda x: len(x[1]), reverse=True)
    print('用户显卡占用排序：')
    print('<用户ID> : <占用显卡数量> : <显卡IP地址和ID>')
    for username, gpuset in usage_num_list:
        print('%s : %d : ' % (username, len(gpuset)), end='')
        for gpuaddr in gpuset:
            print('%s, ' % gpuaddr, end='')
        print()
    print('=' * 60)

    return


parser = argparse.ArgumentParser()
parser.add_argument('--address', required = True, help = 'master服务器IP地址')
parser.add_argument('--port', type = int, default = '5678', help = 'master服务器端口，默认5678')
parser.add_argument('--expiretime', type = int, default = 100, help = '客户端显卡信息过期时间')
opt = parser.parse_args()

info_record = { }
lock = Lock()

http_thread = Thread(target = http_func)
http_thread.start()

