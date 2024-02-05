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


class InvitesAutoSignIn(_IPluginModule):
    # 插件名称
    module_name = "药丸签到"
    # 插件描述
    module_desc = "药丸论坛签到,赚点药丸吃吃!"
    # 插件图标
    module_icon = "invites.png"
    # 主题色
    module_color = "#314974"
    # 插件版本
    module_version = "1.2"
    # 插件作者
    module_author = "none"
    # 作者主页
    author_url = "none"
    # 插件配置项ID前缀
    module_config_prefix = "invitessignin_"
    # 加载顺序
    module_order = 24
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    eventmanager = None
    _scheduler = None

    # 设置开关
    _enabled = False
    # 任务执行间隔
    _site_schema = []
    _cookie = None
    _cron = None
    _queue_cnt = None
    _retry_keyword = None
    _onlyonce = False
    _notify = False
    _clean = False
    _auto_cf = None
    # 退出事件
    _event = Event()

    @staticmethod
    def get_fields():
        return [
            {
                'type': 'div',
                'content': [
                    # 同一行
                    [
                        {
                            'title': '开启定时签到',
                            'required': "",
                            'tooltip': '开启后会根据周期定时签到指定站点。',
                            'type': 'switch',
                            'id': 'enabled',
                        },
                        {
                            'title': '运行时通知',
                            'required': "",
                            'tooltip': '运行签到任务后会发送通知（需要打开插件消息通知）',
                            'type': 'switch',
                            'id': 'notify',
                        },
                        {
                            'title': '立即运行一次',
                            'required': "",
                            'tooltip': '打开后立即运行一次',
                            'type': 'switch',
                            'id': 'onlyonce',
                        }
                    ]
                ]
            },
            {
                'type': 'div',
                'content': [
                    # 同一行
                    [
                        {
                            'title': '签到周期',
                            'required': "",
                            'tooltip': '自动签到时间，四种配置方法：1、配置间隔，单位小时，比如23.5；2、配置固定时间，如08:00；3、配置时间范围，如08:00-09:00，表示在该时间范围内随机执行一次；4、配置5位cron表达式，如：0 */6 * * *；配置为空则不启用自动签到功能。',
                            'type': 'text',
                            'content': [
                                {
                                    'id': 'cron',
                                    'placeholder': '0 0 0 ? *',
                                }
                            ]
                        },
                    ]
                ]
            },
            {
                'type': 'div',
                'content': [
                    # 同一行
                    [
                        {
                            'title': 'cookie',
                            'required': "",
                            'tooltip': 'invites.fun cookies',
                            'type': 'text',
                            'content': [
                                {
                                    'id': 'cookie',
                                    'placeholder': 'cookie',
                                }
                            ]
                        },
                    ]
                ]
            },
        ]

    def get_page(self):
        """
        插件的额外页面，返回页面标题和页面内容
        :return: 标题，页面内容，确定按钮响应函数
        """

        template = """
          <div class="table-responsive table-modal-body">
            <table class="table table-vcenter card-table table-hover table-striped">
              <thead>
              <tr>
                <th>签到时间</th>
                <th>签到结果</th>
                <th>药丸</th>
                <th>连续签到次数</th>
              </tr>
              </thead>
              <tbody>
              {% if ResultsCount > 0 %}
                {% for Item in Results %}
                  <tr id="indexer">
                    <td>{{ Item["date"] }}</td>
                    <td>{{ Item["result"] }}</td>
                    {% if Item["money"] %}
                    <td>{{ Item["money"] }}</td>
                    {% else %}
                    <td>0</td>
                    {% endif %}
                    {% if Item["money"] %}
                    <td>{{ Item["continuousCheckIn"] }}</td>
                    {% else %}
                    <td>0</td>
                    {% endif %}
                  </tr>
                {% endfor %}
              {% endif %}
              </tbody>
            </table>
          </div>
        """
        signin_history = self.get_history('history') or []
        return "签到记录", Template(template).render(
            ResultsCount=len(signin_history), Results=signin_history), None

    def init_config(self, config=None):

        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._cookie = config.get("cookie")
            self._notify = config.get("notify")
            self._onlyonce = config.get("onlyonce")

        # 遍历列表并删除日期超过7天的字典项
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)

        # 停止现有任务
        self.stop_service()

        # 启动服务
        if self._enabled or self._onlyonce:
            self.debug(f"开始药丸签到任务")
            # 定时服务
            self._scheduler = BackgroundScheduler(timezone=Config().get_timezone())


            if self._onlyonce:
                log.info(f"药丸签到服务启动，立即运行一次")
                self._scheduler.add_job(self.signin, 'date',
                                        run_date=datetime.now(tz=pytz.timezone(Config().get_timezone())) + timedelta(
                                            seconds=3))
                # 关闭一次性开关
                self._onlyonce = False
                self.update_config({
                    "enabled": self._enabled,
                    "cron": self._cron,
                    "enabled": self._enabled,
                    "cookie": self._cookie,
                    "onlyonce": self._onlyonce,
                    "notify": self._notify,
                })

            # 周期运行
            if self._cron:
                self.info(f"药丸定时签到服务启动，周期：{self._cron}")
                SchedulerUtils.start_job(scheduler=self._scheduler,
                                         func=self.signin,
                                         func_desc="药丸自动签到",
                                         cron=str(self._cron))

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

    @staticmethod
    def get_command():
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附带数据
        """
        return {
            "cmd": "/pts",
            "event": EventType.SiteSignin,
            "desc": "站点签到",
            "data": {}
        }


    @EventHandler.register(EventType.InvitesSiteSignin)
    def signin(self, event=None):
        """
        药丸签到
        """
        today = datetime.now()
        # 删除7天以前的签到记录
        sevenday_before = today - timedelta(days=7)
        sevenday_before = sevenday_before.strftime('%Y-%m-%d %H:%M:%S')
        # 删除昨天历史
        self.delete_history(sevenday_before)

        # 读取历史记录
        history = self.get_history('history') or []

        res = RequestUtils(cookies=self._cookie,
                           proxies=Config().get_proxies()).get_res(url="https://invites.fun")
        if not res or res.status_code != 200:
            log.error(f"请求药丸错误 {res}")

            # 发送通知
            if self._notify:
                self.send_message(
                    title="【药丸签到任务完成】",
                    text="签到失败，请求药丸错误")
            return

        # 获取csrfToken
        pattern = r'"csrfToken":"(.*?)"'
        csrfToken = re.findall(pattern, res.text)
        if not csrfToken:
            log.error("请求csrfToken失败")

            # 发送通知
            if self._notify:
                self.send_message(
                    title="【药丸签到任务完成】",
                    text="签到失败，请求csrfToken失败")
            return

        csrfToken = csrfToken[0]
        log.info(f"获取csrfToken成功 {csrfToken}")

        # 获取userid
        pattern = r'"userId":(\d+)'
        match = re.search(pattern, res.text)

        if match:
            userId = match.group(1)
            log.info(f"获取userid成功 {userId}")
        else:
            log.error("未找到userId")

            # 发送通知
            if self._notify:
                self.send_message(
                    title="【药丸签到任务完成】",
                    text="签到失败，未找到userId")
            return

        headers = {
            "X-Csrf-Token": csrfToken,
            "X-Http-Method-Override": "PATCH",
            "Cookie": self._cookie
        }

        data = {
            "data": {
                "type": "users",
                "attributes": {
                    "canCheckin": False,
                    "totalContinuousCheckIn": 2
                },
                "id": userId
            }
        }

        # 开始签到
        res = RequestUtils(headers=headers).post_res(url=f"https://invites.fun/api/users/{userId}", json=data)

        if not res or res.status_code != 200:
            log.error(f"药丸签到失败 {res}")

            # 发送通知
            if self._notify:
                self.send_message(
                    title="【药丸签到任务完成】",
                    text="签到失败，请检查cookie是否失效")
            return

        sign_dict = json.loads(res.text)
        money = sign_dict['data']['attributes']['money']
        totalContinuousCheckIn = sign_dict['data']['attributes']['totalContinuousCheckIn']

        # 发送通知
        if self._notify:
            self.send_message(
                title="【药丸签到任务完成】",
                text=f"累计签到 {totalContinuousCheckIn} \n"
                     f"剩余药丸 {money}")

        history.append({
            "date": datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            "results": "签到成功",
            "totalContinuousCheckIn": totalContinuousCheckIn,
            "money": money
        })

        # 保存签到历史
        self.history(key=today.strftime('%Y-%m-%d %H:%M:%S'), value=history)


    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._event.set()
                    self._scheduler.shutdown()
                    self._event.clear()
                self._scheduler = None
        except Exception as e:
            print(str(e))

    def get_state(self):
        return self._enabled and self._cron
