command_dict = {
    "add": {
        "weibo": "添加微博推送",
        "bili_dyn": "添加动态推送",
        "bili_live": "添加直播推送",
    },
    "remove": {
        "weibo": "删除微博推送",
        "bili_dyn": "删除动态推送",
        "bili_live": "删除直播推送",
    },
    "config": {
        "channel": "查询配置",
    },
    "help": "帮助",
    "roll": r"^[/\.]?r([0-9]+)d([0-9]+)" # ^指定只从字符串开头进行匹配
}

HELP = """1 .rxdy 原因
掷y次x点的骰子
2 帮助
显示帮助信息
3 添加微博/动态/直播推送 UID
添加指定UID用户的微博/B站动态/直播推送
例如：添加直播推送 434334701
4 删除微博/动态/直播推送 UID
删除指定UID用户的微博/B站动态/直播推送
例如：删除直播推送 434334701
5 查询配置
查询本群聊中配置的所有推送"""