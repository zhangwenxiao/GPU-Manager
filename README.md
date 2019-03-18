# 监控多个服务器的GPU占用情况

## 使用方法：

1. 切换到Python 3环境

2. 安装依赖：

```shell
pip3 install --user psutil
```

3. 选择一个服务器作为master服务器，运行

```shell
python3 server.py --address <主服务器IP地址>
```

4. 在需要监控的GPU服务器上运行

```shell
python3 client.py --address <主服务器IP地址>
```

5. 查看其它命令行选项

```shell
python3 server.py --help
python3 client.py --help
```

