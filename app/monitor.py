import re
from threading import Lock

import log
from app.downloader import Downloader
from app.filter import Filter
from app.helper import DbHelper, MonitorHelper
from app.media import Media
from app.media.meta import MetaInfo
from app.message import Message
from app.sites import Sites, SiteConf
from app.subscribe import Subscribe
from app.utils import ExceptionUtils, Torrent
from app.utils.commons import singleton
from app.utils.types import MediaType, SearchType
from app.utils import SystemUtils

from config import Config

lock = Lock()


@singleton
class Monitor(object):
    message = None
    dbhelper = None
    monitor_helper = None

    def __init__(self):
        self.init_config()
        self.dbhelper = DbHelper()
        self.monitor_helper = MonitorHelper()

    def init_config(self):
        self.message = Message()

    def monitor(self):
        """
        运行后台监控
        """
        SpacesStatics = self.get_current_library_spacesize()
        SystemStatics = self.get_current_system_statics()

        monitor_info = {}
        monitor_info.update(SpacesStatics)
        monitor_info.update(SystemStatics)

        self.monitor_helper.insert_monitor_torrents(monitor_info)

    
    def get_current_system_statics(self):
        """
        后台执行并插入到db
        """
        TotalMemory, AvailableMemory, MemoryUsedPercent = SystemUtils.get_current_memory_statics()

        if TotalMemory:
            # 已使用空间
            UsedMemory = TotalMemory - AvailableMemory
            # 百分比格式化
            MemoryUsedPercent = "%0.1f" % ((UsedMemory / TotalMemory) * 100)
            # 总剩余空间 格式化
            if AvailableMemory > 1024:
                AvailableMemory = "{:,} TB".format(round(AvailableMemory / 1024, 2))
            else:
                AvailableMemory = "{:,} GB".format(round(AvailableMemory, 2))
            # 总使用空间 格式化
            if UsedMemory > 1024:
                UsedMemory = "{:,} TB".format(round(UsedMemory / 1024, 2))
            else:
                UsedMemory = "{:,} GB".format(round(UsedMemory, 2))
            # 总空间 格式化
            if TotalMemory > 1024:
                TotalMemory = "{:,} TB".format(round(TotalMemory / 1024, 2))
            else:
                TotalMemory = "{:,} GB".format(round(TotalMemory, 2))

        CpuUsedPercent = SystemUtils.get_current_cpu_statics()
        return {
            "code": 0,
            "MemoryUsedPercent": MemoryUsedPercent,
            "AvaiableMemory": AvailableMemory,
            "TotalMemory": TotalMemory,
            "CpuUsedPercent": CpuUsedPercent
        }

    def get_current_library_spacesize(self):
        # 磁盘空间
        UsedSapce = 0
        UsedPercent = 0
        media = Config().get_config('media')
        # 电影目录
        movie_paths = media.get('movie_path')
        if not isinstance(movie_paths, list):
            movie_paths = [movie_paths]
        # 电视目录
        tv_paths = media.get('tv_path')
        if not isinstance(tv_paths, list):
            tv_paths = [tv_paths]
        # 动漫目录
        anime_paths = media.get('anime_path')
        if not isinstance(anime_paths, list):
            anime_paths = [anime_paths]
        # 总空间、剩余空间
        TotalSpace, FreeSpace = SystemUtils.get_space_statics(movie_paths + tv_paths + anime_paths)
        if TotalSpace:
            # 已使用空间
            UsedSapce = TotalSpace - FreeSpace
            # 百分比格式化
            UsedPercent = "%0.1f" % ((UsedSapce / TotalSpace) * 100)
            # 总剩余空间 格式化
            if FreeSpace > 1024:
                FreeSpace = "{:,} TB".format(round(FreeSpace / 1024, 2))
            else:
                FreeSpace = "{:,} GB".format(round(FreeSpace, 2))
            # 总使用空间 格式化
            if UsedSapce > 1024:
                UsedSapce = "{:,} TB".format(round(UsedSapce / 1024, 2))
            else:
                UsedSapce = "{:,} GB".format(round(UsedSapce, 2))
            # 总空间 格式化
            if TotalSpace > 1024:
                TotalSpace = "{:,} TB".format(round(TotalSpace / 1024, 2))
            else:
                TotalSpace = "{:,} GB".format(round(TotalSpace, 2))

        return {"code": 0,
                "SpaceUsedPercent": UsedPercent,
                "FreeSpace": FreeSpace,
                "UsedSapce": UsedSapce,
                "TotalSpace": TotalSpace}

    def delete_monitor_history(self, monitorid):
        """
        删除订阅历史
        """
        self.dbhelper.delete_monitor_history(monitorid=monitorid)

    def get_monitor_history(self, monitorid=None):
        """
        获取订阅历史
        """
        monitor_history = self.dbhelper.get_monitor_history(monitorid=monitorid)

        if monitor_history:
            CpuUsedPercent = [item.CPUPERCENT for item in monitor_history]
            MemoryUsedPercent = [item.MEMORYPERCENT for item in monitor_history]

            MemoryAvaiable = monitor_history[-1].MEMORYAVAIABLE
            MemoryTotal = monitor_history[-1].MEMORYTOTAL
            SpaceUsedPercent = monitor_history[-1].SPACEPERCENT

            SpaceFree = monitor_history[-1].SPACEPFREE
            SpaceUsed = monitor_history[-1].SPACEPUSED
            SpaceTotal = monitor_history[-1].SPACETOTAL

            return {
                "CpuUsedPercent": CpuUsedPercent,
                "MemoryUsedPercent": MemoryUsedPercent,
                "CpuUsedPercentNow": CpuUsedPercent[-1],
                "MemoryUsedPercentNow": MemoryUsedPercent[-1],
                "MemoryAvaiable": MemoryAvaiable,
                "MemoryTotal": MemoryTotal,
                "SpaceUsedPercent": SpaceUsedPercent,
                "SpaceFree": SpaceFree,
                "SpaceUsed": SpaceUsed,
                "SpaceTotal": SpaceTotal,
            }
        else:
            return {
                "CpuUsedPercent": [],
                "MemoryUsedPercent": [],
                "CpuUsedPercentNow": '0.0',
                "MemoryUsedPercentNow": '0.0',
                "MemoryAvaiable": '0.0G',
                "MemoryTotal": '0.0G',
                "SpaceUsedPercent": '0.0',
                "SpaceFree": '0.0G',
                "SpaceUsed": '0.0G',
                "SpaceTotal": '0.0G',
            }
