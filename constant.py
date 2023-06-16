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
        "all": "/关闭推送",
        "weibo": "/关闭微博推送",
        "bili_dyn": "/关闭动态推送",
        "bili_live_start": "/关闭开播推送",
        "bili_live_end": "/关闭下播推送",
        "bili_live_title": "/关闭直播标题推送",
        "bili_live_cover": "/关闭直播封面推送",
    },
    "enable": {
        "all": "/开启推送",
        "weibo": "/开启微博推送",
        "bili_dyn": "/开启动态推送",
        "bili_live_start": "/开启开播推送",
        "bili_live_end": "/开启下播推送",
        "bili_live_title": "/开启直播标题推送",
        "bili_live_cover": "/开启直播封面推送",
    },
    "at_all": {
        "enable": "/开启全体成员提醒",
        "disable": "/关闭全体成员提醒"
    },
    "config": {
        "channel": "/查询配置"
    },
    "permission": {
        "grant": "/设置管理员",
        "revoke": "/删除管理员"
    },
    "help": "/帮助"
}

type_dict = {
    "weibo": "微博",
    "bili_dyn": "动态",
    "bili_live": "直播",
    "all": ""
}

sub_type_dict = {
    "weibo": {
        "comment": "微博评论"
    },
    "bili_dyn": {
        "comment": "动态评论"
    },
    "bili_live": {
        "live_start": "开播",
        "live_end": "下播",
        "title": "直播间标题",
        "cover": "直播间封面"
    }
}