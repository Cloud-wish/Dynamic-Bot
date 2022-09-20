command_dict = {
    "add": {
        "weibo": "/添加微博推送",
        "weibo_comment": "/添加微博评论推送",
        "bili_dyn": "/添加动态推送",
        "bili_live": "/添加直播推送",
        "bili_dyn_top_comment": "/添加动态置顶评论推送",
        "bili_dyn_latest_comment": "/添加动态评论推送"
    },
    "remove": {
        "weibo": "/删除微博推送",
        "weibo_comment": "/删除微博评论推送",
        "bili_dyn": "/删除动态推送",
        "bili_live": "/删除直播推送",
        "bili_dyn_top_comment": "/删除动态置顶评论推送",
        "bili_dyn_latest_comment": "/删除动态评论推送"
    },
    "disable": {
        "channel": "/关闭推送"
    },
    "enable": {
        "channel": "/开启推送"
    },
    "config": {
        "channel": "/查询配置"
    },
    "help": "/帮助"
}

type_dict = {
    "weibo": "微博",
    "bili_dyn": "动态",
    "bili_live": "直播"
}

sub_type_dict = {
    "weibo": {
        "comment": "微博评论"
    },
    "bili_dyn": {
        "comment": "动态评论"
    }
}