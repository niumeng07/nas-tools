from datetime import datetime

from app.db import MainDb, DbPersist
from app.db.models import MONITORHISTORY
from app.utils import RssTitleUtils, StringUtils, RequestUtils, ExceptionUtils, DomUtils
from config import Config


class MonitorHelper:
    _db = MainDb()

    @DbPersist(_db)
    def insert_monitor_torrents(self, monitor_info):
        """
        将RSS的记录插入数据库
        """
        now = datetime.now()
        self._db.insert(
            MONITORHISTORY(
                DATE = now.strftime('%Y%m%d'),
                TIME = now.strftime('%H:%M:%S'),
                MEMORYPERCENT = monitor_info['MemoryUsedPercent'],
                MEMORYAVAIABLE = monitor_info['AvaiableMemory'],
                MEMORYTOTAL = monitor_info['TotalMemory'],
                CPUPERCENT = monitor_info['CpuUsedPercent'],
                SPACEPERCENT = monitor_info['SpaceUsedPercent'],
                SPACEPFREE = monitor_info['UsedSapce'],
                SPACEPUSED = monitor_info['UsedSapce'],
                SPACETOTAL = monitor_info['TotalSpace'],
                FINISH_TIME = int(now.timestamp())
            ))
