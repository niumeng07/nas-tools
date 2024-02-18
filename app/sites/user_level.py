import log

USER_LEVEL_ALIAS = {
    "跑龙套": "Power User",
    "配角": "Elite User",
    "主演": "Crazy User",
    "领衔主演": "Insane User",
    "明星": "Veteran User",
    "国际大腕": "Extreme User",
    "影帝": "Ultimate User",
    "终身影帝": "Nexus Master",
    "零冻": "Peasant",
    "新手": "User",
    "入门": "Power User",
    "发烧": "Elite User",
    "着迷": "Crazy User",
    "狂热": "Insane User",
    "资深": "Veteran User",
    "大师": "Extreme User",
    "宗师": "Ultimate User",
    "骨灰": "Nexus Master",
    "神仙": "NexusGod",
    "神王": "Immortal",
    "叛徒": "Peasant",
    "平民": "User",
    "正兵": "Power User",
    "军士": "Elite User",
    "副军校": "Crazy User",
    "正军校": "Insane User",
    "副参领": "Veteran User",
    "正参领": "Extreme User",
    "副都统": "Ultimate User",
    "大将军": "Nexus Master",
    "惊蛰": "Peasant",
    "萌动": "User",
    "易形": "Power User",
    "化蛹": "Elite User",
    "破茧": "Crazy User",
    "恋风": "Insane User",
    "翩跹": "Veteran User",
    "归尘": "Extreme User",
    "幻梦": "Ultimate User",
    "逍遥": "Nexus Master",
    "庶民": "Peasant",
    "列兵": "User",
    "士官": "Power User",
    "尉官": "Elite User",
    "少校": "Crazy User",
    "中校": "Insane User",
    "上校": "Veteran User",
    "少将": "Extreme User",
    "中将": "Ultimate User",
    "上将": "Nexus Master",
    "堕落者": "Peasant",
    "天使": "User",
    "大天使": "Power User",
    "权天使": "Elite User",
    "能天使": "Crazy User",
    "力天使": "Insane User",
    "主天使": "Veteran User",
    "座天使": "Extreme User",
    "智天使": "Ultimate User",
    "炽天使": "Nexus Master",
    "斗者": "User",
    "斗师": "Power User",
    "大斗师": "Crazy User",
    "斗皇": "Insane User",
    "斗宗": "Veteran User",
    "斗尊": "Extreme User",
    "斗圣": "Ultimate User",
    "斗帝": "Nexus Master",
    "走火入魔": "Peasant",
    "筑基": "User",
    "结丹": "Power User",
    "元婴": "Elite User",
    "出窍": "Crazy User",
    "炼虚": "Insane User",
    "合体": "Veteran User",
    "大乘": "Extreme User",
    "真仙": "Ultimate User",
}

def get_user_level(user_level):
    if not user_level:
        return user_level
    if user_level in USER_LEVEL_ALIAS:
        alias_name = USER_LEVEL_ALIAS.get(user_level, "")
        return "{} ({})".format(user_level, alias_name)
    return user_level
