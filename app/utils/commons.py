# -*- coding: utf-8 -*-
import threading
import time
from collections import OrderedDict
from enum import Enum
from datetime import timedelta, datetime

# 线程锁
lock = threading.RLock()

# 全局实例
INSTANCES = OrderedDict()


# 单例模式注解
def singleton(cls):
    # 创建字典用来保存类的实例对象
    global INSTANCES

    def _singleton(*args, **kwargs):
        # 先判断这个类有没有对象
        if cls not in INSTANCES:
            with lock:
                if cls not in INSTANCES:
                    INSTANCES[cls] = cls(*args, **kwargs)
                    pass
        # 将实例对象返回
        return INSTANCES[cls]

    return _singleton


def deltatime2str(time1, time2):
    time_delta = time1 - time2
    delta_days = time_delta.days
    delta_seconds = time_delta.seconds
    delta_hours = int(delta_seconds / 3600)
    delta_minutes = int((delta_seconds % 3600) / 60)
    if delta_days or delta_hours or delta_minutes:
        ret_list = [(delta_days, '天'), (delta_hours, '小时'), (delta_minutes, '分')]
        return ''.join([str(item[0]) + item[1] for item in ret_list if item[0] > 0])
    else:
        return '运行中'


# 重试装饰器
def retry(ExceptionToCheck, tries=3, delay=3, backoff=2, logger=None):
    """
    :param ExceptionToCheck: 需要捕获的异常
    :param tries: 重试次数
    :param delay: 延迟时间
    :param backoff: 延迟倍数
    :param logger: 日志对象
    """

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = f"{str(e)}, {mdelay} 秒后重试 ..."
                    if logger:
                        logger.warn(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry

    return deco_retry


class RateUnit(Enum):
    Bs = 'B/s'
    KBs = 'KB/s'
    MBs = 'MB/s'
    GBs = 'GB/s'
    TBs = 'TB/s'


def BytesFormat(SrcRate, unit=RateUnit.Bs):
    Suffix = RateUnit.Bs.value
    if unit == RateUnit.KBs:
        Suffix = RateUnit.Bs.value
        SrcRate = SrcRate * 1024
    if SrcRate >= 1024:
        SrcRate = SrcRate / 1024.
        Suffix = RateUnit.KBs.value
    if SrcRate >= 1024:
        SrcRate = SrcRate / 1024.
        Suffix = RateUnit.MBs.value
    return "{num:.2f} {suff}".format(num=SrcRate, suff=Suffix)
