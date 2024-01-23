import json
import re
import time
from datetime import datetime, timedelta
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.pool import ThreadPool
from threading import Event

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from lxml import etree
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as es
from selenium.webdriver.support.wait import WebDriverWait

import sys
sys.path.append("/nas-tools/")
from app.helper import ChromeHelper, SubmoduleHelper, SiteHelper
from app.helper.cloudflare_helper import under_challenge
from app.message import Message
from app.plugins import EventHandler, EventManager
from app.plugins.modules._base import _IPluginModule
from app.utils import RequestUtils, ExceptionUtils, StringUtils, SchedulerUtils
from app.utils.types import EventType
from config import Config
from jinja2 import Template
import random
import log

from app.plugins.modules.invitesautosignin import InvitesAutoSignIn

runner = InvitesAutoSignIn()
runner._scheduler = BackgroundScheduler(timezone=Config().get_timezone())
print(runner._scheduler, runner._cron)

runner.info(f"药丸定时签到服务启动，周期：{runner._cron}")
SchedulerUtils.start_job(scheduler=runner._scheduler,
		     func=runner.signin,
		     func_desc="药丸自动签到",
		     cron=str("57 14 * * *"))

SchedulerUtils.start_job(scheduler=runner._scheduler,
		     func=runner.signin,
		     func_desc="药丸自动签到",
		     cron=str("58 14 * * *"))
# 启动任务
print(runner._scheduler.get_jobs(), runner._scheduler.print_jobs())
if runner._scheduler.get_jobs():
    runner._scheduler.print_jobs()
    runner._scheduler.start()

