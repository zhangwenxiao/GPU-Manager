import re
import pwd
import time
import json
import psutil
import argparse
import requests
import subprocess

def get_owner(pid):
    try:
        for line in open('/proc/%d/status' % pid):
            if line.startswith('Uid:'):
                uid = int(line.split()[1])
                return pwd.getpwuid(uid).pw_name
    except:
        return None

def get_info():
    info = { 'gpu': [], 'process': [] }
    msg = subprocess.Popen('nvidia-smi', stdout = subprocess.PIPE).stdout.read().decode()
    msg = msg.strip().split('\n')

    lino = 8
    while True:
        status = re.findall('.*\d+%.*\d+C.*\d+W / +\d+W.* +(\d+)MiB / +(\d+)MiB.* +\d+%.*', msg[lino])
        if status == []: break
        mem_usage, mem_total = status[0]
        info['gpu'].append({
            'mem_usage': float(mem_usage),
            'mem_total': float(mem_total),
        })
        lino += 3

    lino = -1
    while True:
        lino -= 1
        status = re.findall('\| +(\d+) +(\d+) +\w+ +([^ ]*) +(\d+)MiB \|', msg[lino])
        if status == []: break
        gpuid, pid, program, mem_usage = status[0]
        username = get_owner(int(pid))
        if username is None:
            print('进程已经不存在')
            continue
        try:
            p = psutil.Process(int(pid))
            p.cpu_percent()
            time.sleep(0.5)
            cpu_percent = p.cpu_percent()
        except psutil.NoSuchProcess:
            print('进程已经不存在')
            continue
        info['process'].append({
            'gpuid': int(gpuid),
            'pid': int(pid),
            'program': program,
            'cpu_percent': cpu_percent,
            'mem_usage': float(mem_usage),
            'username': username,
        })
    info['process'].reverse()

    return info

parser = argparse.ArgumentParser()
parser.add_argument('--address', required = True, help = 'master服务器IP地址')
parser.add_argument('--port', default = '5678', help = 'master服务器端口，默认5678')
parser.add_argument('--persecond', default = 20, help = '多少秒获取一次显卡信息，默认20s')
opt = parser.parse_args()

url = 'http://%s:%s' % (opt.address, opt.port)

while True:
    mean_info = get_info()
    data = json.dumps(mean_info)
    # print(data)
    try:
        response = requests.get(url, data = data)
        print('HTTP状态码:', response.status_code)
    except Exception as e:
        print(e)
    time.sleep(opt.persecond)
