<div align="center">

# Dynamic Bot

_使用go-cqhttp自动推送微博/哔哩哔哩动态/哔哩哔哩直播状态更新的QQ频道Bot_  

</div>

功能暂未测试完全，有什么Bug，功能建议或是疑问欢迎提[Issues](https://github.com/Cloud-wish/Dynamic-Bot/issues)

## 使用
- 本Bot设计为配合[Dynamic-Crawler](https://github.com/Cloud-wish/Dynamic-Crawler)使用，请事先部署好Crawler服务！
- 如果B站动态/微博截图出现字体显示出错/显示奇怪的情况，是因为系统中未安装font文件夹下的字体，安装后即可正常显示
### 启动
Python版本为3.8

`python main.py`
### 命令列表
`main.py`中的`BOT_HELP`
## 配置
配置文件应命名为`config.ini`，配置项参考[config_sample.ini](https://github.com/Cloud-wish/Dynamic-Bot/blob/main/config_sample.ini)
