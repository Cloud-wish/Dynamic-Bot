# Dynamic Bot

多平台，多Bot实例的动态推送Bot框架

## 使用
### 环境配置
推荐使用Python 3.8
```shell
pip install -r requirements.txt
playwright install --with-deps chromium
```

### Crawler配置
本Bot设计为配合[Dynamic-Crawler](https://github.com/Cloud-wish/Dynamic-Crawler)使用，请事先部署好Crawler服务

### 修改配置文件
配置文件应命名为config.yaml，参考config_sample.yaml修改为想要的配置后启动

### 启动
`python main.py`

## 功能扩展
参考[架构设计](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/docs/design.md)

## 问题
### 指令列表
- Bot启动后，群主/管理员在群聊内发送“帮助”即可显示指令列表与使用方法
- [command.py](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/bot/constants/command.py)中的`BOT_HELP`

### 动态图片字体显示异常
如果B站动态/微博截图出现字体显示出错/缺失的情况，是因为系统中未安装font文件夹下的字体，安装后即可正常显示

### 其它Bug
Bug，功能建议或疑问，欢迎提[Issues](https://github.com/Cloud-wish/Dynamic-Bot/issues)