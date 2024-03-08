import os.path
import re
import time
from datetime import datetime

import transmission_rpc

import log
from app.utils import ExceptionUtils, StringUtils
from app.utils.types import DownloaderType
from app.downloader.client._base import _IDownloadClient
from app.utils.commons import BytesFormat
from app.utils.commons import RateUnit

class Transmission(_IDownloadClient):
    # 下载器ID
    client_id = "transmission"
    # 下载器类型
    client_type = DownloaderType.TR
    # 下载器名称
    client_name = DownloaderType.TR.value

    # 参考transmission web，仅查询需要的参数，加速种子搜索
    _trarg = ["id", "name", "status", "labels", "hashString", "totalSize", "percentDone", "addedDate", "trackerStats",
              "leftUntilDone", "rateDownload", "rateUpload", "recheckProgress", "rateDownload", "rateUpload",
              "peersGettingFromUs", "peersSendingToUs", "uploadRatio", "uploadedEver", "downloadedEver", "downloadDir",
              "error", "errorString", "doneDate", "queuePosition", "activityDate", "trackers"]

    # 私有属性
    _client_config = {}

    trc = None
    host = None
    port = None
    username = None
    password = None
    download_dir = []
    name = "测试"

    def __init__(self, config):
        self._client_config = config
        self.init_config()
        if not self.connect():
            log.error(f"链接 Transmission 出错, 请检查配置, 地址: {self.host}:{self.port}")
            return
        # 设置未完成种子添加!part后缀
        self.trc.set_session(rename_partial_files=True)

    def init_config(self):
        if self._client_config:
            self.host = self._client_config.get('host')
            self.port = int(self._client_config.get('port')) if str(self._client_config.get('port')).isdigit() else 0
            self.username = self._client_config.get('username')
            self.password = self._client_config.get('password')
            self.download_dir = self._client_config.get('download_dir') or []
            self.name = self._client_config.get('name') or ""

    @classmethod
    def match(cls, ctype):
        return True if ctype in [cls.client_id, cls.client_type, cls.client_name] else False

    def get_type(self):
        return self.client_type

    def connect(self):
        if self.host and self.port:
            self.trc = self.__login_transmission()
            return self.trc
        return None

    def downloader_statistics(self):
        if not self.trc:
            log.error(f"下载器未初始化")
            return None
        try:
            info = self.trc.session_stats()
            download_speed = BytesFormat(info.download_speed)
            upload_speed = BytesFormat(info.upload_speed)
            download_rate_limit = BytesFormat(self.trc.get_session().speed_limit_down if self.trc.get_session().speed_limit_down_enabled else 0, RateUnit.KBs)
            upload_rate_limit = BytesFormat(self.trc.get_session().speed_limit_up if self.trc.get_session().speed_limit_up_enabled else 0, RateUnit.KBs)
            return {
                "download_speed": download_speed,
                "upload_speed": upload_speed,
                "download_rate_limit": download_rate_limit,
                "upload_rate_limit": upload_rate_limit,
                "download_size": info.current_stats.downloaded_bytes,
                "upload_size": info.current_stats.uploaded_bytes,
                "torrent_count": info.torrent_count,
                "host": self.host,
                "port": self.port,
                "downloader_type": "TR",
                "logo": """
<svg fill="#FFFFFF" width="800px" height="800px" viewBox="0 0 14 14" role="img" focusable="false" aria-hidden="true"
xmlns="http://www.w3.org/2000/svg">
<path
d="m 1.374945,12.619676 0,-0.3774 0.73582,-3.1461002 c 0.40471,-1.7303 0.74373,-3.1776 0.75339,-3.2163 l 0.0176,-0.07 1.65101,0 c 0.90806,0 1.65716,-0.01 1.66468,-0.023 0.008,-0.013 0.0238,-0.7371 0.0363,-1.6093 l 0.0226,-1.586 -1.261,-2e-4 c -0.72878,-10e-5 -1.30762,-0.013 -1.37146,-0.031 -0.22995,-0.064 -0.39171,-0.1995 -0.49991,-0.4193 -0.0895,-0.1818 -0.0995,-0.2274 -0.0849,-0.3879 0.0204,-0.2246 0.10555,-0.397 0.2693,-0.5449 0.24305,-0.21959997 0.0848,-0.21059997 3.69574,-0.21059997 2.22616,0 3.29266,0.011 3.40191,0.034 0.34612,0.074 0.59989,0.4021 0.59812,0.7727 -4.9e-4,0.103 -0.021,0.2354 -0.0455,0.2941 -0.0628,0.1503 -0.2272,0.3283 -0.3776,0.4088 -0.12503,0.067 -0.15816,0.069 -1.44826,0.078 l -1.32031,0.01 0,1.5924 0,1.5925 -0.77657,0 -0.77656,0 -0.0203,0.286 c -0.0112,0.1574 -0.0203,0.5067 -0.0203,0.7763 0,0.2697 -0.009,0.6821 -0.0204,0.9166 l -0.0204,0.4263 -0.77782,0.01 -0.77781,0.01 1.21234,1.2315 1.21234,1.2315002 1.17185,-1.2105002 c 0.64452,-0.6657 1.17654,-1.2234 1.18227,-1.2393 0.006,-0.017 -0.30712,-0.029 -0.77344,-0.029 l -0.78385,0 0,-1.1875 0,-1.1875 1.68539,0 c 1.57825,0 1.68639,0 1.70126,0.055 0.009,0.03 0.32608,1.4894 0.70523,3.2428 0.66816,3.0900002 0.68935,3.1988002 0.68935,3.5390002 l 0,0.351 -5.62498,0 -5.62497,0 0,-0.3774 z" />
</svg>
                """
            }
        except Exception as err:
            log.error(f"获取信息出错: {str(err)}")
            return None

    def __login_transmission(self):
        """
        连接transmission
        :return: transmission对象
        """
        try:
            # 登录
            trt = transmission_rpc.Client(host=self.host,
                                          port=self.port,
                                          username=self.username,
                                          password=self.password,
                                          timeout=60)
            return trt
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 连接出错：{str(err)}")
            return None

    def get_status(self):
        return True if self.trc else False

    @staticmethod
    def __parse_ids(ids):
        """
        统一处理种子ID
        """
        if isinstance(ids, list) and any([str(x).isdigit() for x in ids]):
            ids = [int(x) for x in ids if str(x).isdigit()]
        elif not isinstance(ids, list) and str(ids).isdigit():
            ids = int(ids)
        return ids

    def get_torrents(self, ids=None, status=None, tag=None):
        """
        获取种子列表
        返回结果 种子列表, 是否有错误
        """
        if not self.trc:
            return [], True
        ids = self.__parse_ids(ids)
        try:
            torrents = self.trc.get_torrents(ids=ids, arguments=self._trarg)
        except Exception as err:
            ExceptionUtils.exception_traceback(err)
            return [], True
        if status and not isinstance(status, list):
            status = [status]
        if tag and not isinstance(tag, list):
            tag = [tag]
        ret_torrents = []
        for torrent in torrents:
            if status and torrent.status not in status:
                continue
            labels = torrent.labels if hasattr(torrent, "labels") else []
            include_flag = True
            if tag:
                for t in tag:
                    if t and t not in labels:
                        include_flag = False
                        break
            if include_flag:
                ret_torrents.append(torrent)
        return ret_torrents, False

    def get_completed_torrents(self, ids=None, tag=None):
        """
        获取已完成的种子列表
        return 种子列表, 发生错误时返回None
        """
        if not self.trc:
            return None
        try:
            torrents, error = self.get_torrents(status=["seeding", "seed_pending"], ids=ids, tag=tag)
            return None if error else torrents or []
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 获取已完成的种子列表出错：{str(err)}")
            return None

    def get_downloading_torrents(self, ids=None, tag=None):
        """
        获取正在下载的种子列表
        return 种子列表, 发生错误时返回None
        """
        if not self.trc:
            return None
        try:
            torrents, error = self.get_torrents(ids=ids,
                                                status=["downloading", "download_pending"],
                                                tag=tag)
            return None if error else torrents or []
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 获取正在下载的种子列表出错：{str(err)}")
            return None

    def set_torrents_status(self, ids, tags=None):
        """
        设置种子为已整理状态
        """
        if not self.trc:
            return
        ids = self.__parse_ids(ids)
        # 合成标签
        if tags:
            if not isinstance(tags, list):
                tags = [tags, "已整理"]
            else:
                tags.append("已整理")
        else:
            tags = ["已整理"]
        # 打标签
        try:
            self.trc.change_torrent(labels=tags, ids=ids)
            log.info(f"【{self.client_name}】{self.name} 设置种子标签成功")
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 设置种子为已整理状态出错：{str(err)}")

    def set_torrent_tag(self, tid, tag):
        """
        设置种子标签
        """
        if not tid or not tag:
            return
        ids = self.__parse_ids(tid)
        try:
            self.trc.change_torrent(labels=tag, ids=ids)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 设置种子标签出错：{str(err)}")

    def change_torrent(self,
                       tid,
                       tag=None,
                       upload_limit=None,
                       download_limit=None,
                       ratio_limit=None,
                       seeding_time_limit=None):
        """
        设置种子
        :param tid: ID
        :param tag: 标签
        :param upload_limit: 上传限速 Kb/s
        :param download_limit: 下载限速 Kb/s
        :param ratio_limit: 分享率限制
        :param seeding_time_limit: 做种时间限制
        :return: bool
        """
        if not tid:
            return
        else:
            ids = self.__parse_ids(tid)
        if tag:
            if isinstance(tag, list):
                labels = tag
            else:
                labels = [tag]
        else:
            labels = []
        if upload_limit:
            uploadLimited = True
            uploadLimit = int(upload_limit)
        else:
            uploadLimited = False
            uploadLimit = 0
        if download_limit:
            downloadLimited = True
            downloadLimit = int(download_limit)
        else:
            downloadLimited = False
            downloadLimit = 0
        if ratio_limit:
            seedRatioMode = 1
            seedRatioLimit = round(float(ratio_limit), 2)
        else:
            seedRatioMode = 2
            seedRatioLimit = 0
        if seeding_time_limit:
            seedIdleMode = 1
            seedIdleLimit = int(seeding_time_limit)
        else:
            seedIdleMode = 2
            seedIdleLimit = 0
        try:
            self.trc.change_torrent(ids=ids,
                                    labels=labels,
                                    uploadLimited=uploadLimited,
                                    uploadLimit=uploadLimit,
                                    downloadLimited=downloadLimited,
                                    downloadLimit=downloadLimit,
                                    seedRatioMode=seedRatioMode,
                                    seedRatioLimit=seedRatioLimit,
                                    seedIdleMode=seedIdleMode,
                                    seedIdleLimit=seedIdleLimit)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 设置种子出错：{str(err)}")

    def get_transfer_task(self, tag=None, match_path=None):
        """
        获取下载文件转移任务种子
        """
        # 处理下载完成的任务
        torrents = self.get_completed_torrents() or []
        trans_tasks = []
        for torrent in torrents:
            # 3.0版本以下的Transmission没有labels
            if not hasattr(torrent, "labels"):
                log.error(f"【{self.client_name}】{self.name} 版本可能过低，无labels属性，请安装3.0以上版本！")
                break
            torrent_tags = torrent.labels or ""
            # 含"已整理"tag的不处理
            if "已整理" in torrent_tags:
                continue
            # 开启标签隔离，未包含指定标签的不处理
            if tag and tag not in torrent_tags:
                log.debug(f"【{self.client_name}】{self.name} 开启标签隔离， {torrent.name} 未包含指定标签：{tag}")
                continue
            path = torrent.download_dir
            # 无法获取下载路径的不处理
            if not path:
                log.debug(f"【{self.client_name}】{self.name} 未获取到 {torrent.name} 下载保存路径")
                continue
            true_path, replace_flag = self.get_replace_path(path, self.download_dir)
            # 开启目录隔离，未进行目录替换的不处理
            if match_path and not replace_flag:
                log.debug(f"【{self.client_name}】{self.name} 开启目录隔离，但 {torrent.name} 未匹配下载目录范围")
                continue
            trans_tasks.append({
                'path': os.path.join(true_path, torrent.name).replace("\\", "/"),
                'id': torrent.hashString,
                'tags': torrent.labels
            })
        return trans_tasks

    def get_remove_torrents(self, config=None):
        """
        获取自动删种任务
        """
        if not config:
            return []
        remove_torrents = []
        remove_torrents_ids = []
        torrents, error_flag = self.get_torrents(tag=config.get("filter_tags"),
                                                 status=config.get("tr_state"))
        if error_flag:
            return []
        ratio = config.get("ratio")
        # 做种时间 单位：小时
        seeding_time = config.get("seeding_time")
        # 大小 单位：GB
        size = config.get("size")
        minsize = size[0] * 1024 * 1024 * 1024 if size else 0
        maxsize = size[-1] * 1024 * 1024 * 1024 if size else 0
        # 平均上传速度 单位 KB/s
        upload_avs = config.get("upload_avs")
        savepath_key = config.get("savepath_key")
        tracker_key = config.get("tracker_key")
        tr_error_key = config.get("tr_error_key")
        for torrent in torrents:
            date_done = torrent.date_done or torrent.date_added
            date_now = int(time.mktime(datetime.now().timetuple()))
            torrent_seeding_time = date_now - int(time.mktime(date_done.timetuple())) if date_done else 0
            torrent_uploaded = torrent.ratio * torrent.total_size
            torrent_upload_avs = torrent_uploaded / torrent_seeding_time if torrent_seeding_time else 0
            if ratio and torrent.ratio <= ratio:
                continue
            if seeding_time and torrent_seeding_time <= seeding_time * 3600:
                continue
            if size and (torrent.total_size >= maxsize or torrent.total_size <= minsize):
                continue
            if upload_avs and torrent_upload_avs >= upload_avs * 1024:
                continue
            if savepath_key and not re.findall(savepath_key, torrent.download_dir, re.I):
                continue
            if tracker_key:
                if not torrent.trackers:
                    continue
                else:
                    tacker_key_flag = False
                    for tracker in torrent.trackers:
                        if re.findall(tracker_key, tracker.get("announce", ""), re.I):
                            tacker_key_flag = True
                            break
                    if not tacker_key_flag:
                        continue
            if tr_error_key:
                announce_results = [x.last_announce_result for x in torrent.tracker_stats]
                announce_results.append(torrent.error_string)

                # 如果announce_results中均不匹配tr_error_key，则跳过
                if not any([re.findall(tr_error_key, x, re.I) for x in announce_results]):
                    continue

            remove_torrents.append({
                "id": torrent.hashString,
                "name": torrent.name,
                "site": torrent.trackers[0].get("sitename") if torrent.trackers else "",
                "size": torrent.total_size
            })
            remove_torrents_ids.append(torrent.hashString)
        if config.get("samedata") and remove_torrents:
            remove_torrents_plus = []
            for remove_torrent in remove_torrents:
                name = remove_torrent.get("name")
                size = remove_torrent.get("size")
                for torrent in torrents:
                    if torrent.name == name and torrent.total_size == size and torrent.hashString not in remove_torrents_ids:
                        remove_torrents_plus.append({
                            "id": torrent.hashString,
                            "name": torrent.name,
                            "site": torrent.trackers[0].get("sitename") if torrent.trackers else "",
                            "size": torrent.total_size
                        })
            remove_torrents_plus += remove_torrents
            return remove_torrents_plus
        return remove_torrents

    def add_torrent(self, content,
                    is_paused=False,
                    download_dir=None,
                    upload_limit=None,
                    download_limit=None,
                    cookie=None,
                    **kwargs):
        try:
            ret = self.trc.add_torrent(torrent=content,
                                       download_dir=download_dir,
                                       paused=is_paused,
                                       cookies=cookie)
            if ret and ret.hashString:
                if upload_limit:
                    self.set_uploadspeed_limit(ret.hashString, int(upload_limit))
                if download_limit:
                    self.set_downloadspeed_limit(ret.hashString, int(download_limit))
            return ret
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 添加种子出错：{str(err)}")
            return False

    def start_torrents(self, ids):
        if not self.trc:
            return False
        ids = self.__parse_ids(ids)
        try:
            return self.trc.start_torrent(ids=ids)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 开始下载出错：{str(err)}")
            return False

    def stop_torrents(self, ids):
        if not self.trc:
            return False
        ids = self.__parse_ids(ids)
        try:
            return self.trc.stop_torrent(ids=ids)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 停止下载出错：{str(err)}")
            return False

    def delete_torrents(self, delete_file, ids):
        if not self.trc:
            return False
        if not ids:
            return False
        ids = self.__parse_ids(ids)
        try:
            return self.trc.remove_torrent(delete_data=delete_file, ids=ids)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 删除下载出错：{str(err)}")
            return False

    def get_files(self, tid):
        """
        获取种子文件列表
        """
        if not tid:
            return None
        try:
            torrent = self.trc.get_torrent(tid)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 获取种子文件列表出错：{str(err)}")
            return None
        if torrent:
            return torrent.files()
        else:
            return None

    def set_files(self, **kwargs):
        """
        设置下载文件的状态
        {
            <torrent id>: {
                <file id>: {
                    'priority': <priority ('high'|'normal'|'low')>,
                    'selected': <selected for download (True|False)>
                },
                ...
            },
            ...
        }
        """
        if not kwargs.get("file_info"):
            return False
        try:
            self.trc.set_files(kwargs.get("file_info"))
            return True
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 设置下载文件的状态出错：{str(err)}")
            return False

    def get_download_dirs(self):
        if not self.trc:
            return []
        try:
            return [self.trc.get_session(timeout=30).download_dir]
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 获取下载文件夹出错：{str(err)}")
            return []

    def set_uploadspeed_limit(self, ids, limit):
        """
        设置上传限速，单位 KB/sec
        """
        if not self.trc:
            return
        if not ids or not limit:
            return
        ids = self.__parse_ids(ids)
        self.trc.change_torrent(ids, uploadLimit=int(limit))

    def set_downloadspeed_limit(self, ids, limit):
        """
        设置下载限速，单位 KB/sec
        """
        if not self.trc:
            return
        if not ids or not limit:
            return
        ids = self.__parse_ids(ids)
        self.trc.change_torrent(ids, downloadLimit=int(limit))

    def get_downloading_progress(self, tag=None, ids=None):
        """
        获取正在下载的种子进度
        """
        Torrents = self.get_downloading_torrents(tag=tag, ids=ids) or []
        DispTorrents = []
        for torrent in Torrents:
            if torrent.status in ['stopped']:
                state = "Stoped"
                speed = "已暂停"
            else:
                state = "Downloading"
                if hasattr(torrent, "rate_download"):
                    _dlspeed = StringUtils.str_filesize(torrent.rate_download)
                else:
                    _dlspeed = StringUtils.str_filesize(torrent.rateDownload)
                if hasattr(torrent, "rate_upload"):
                    _upspeed = StringUtils.str_filesize(torrent.rate_upload)
                else:
                    _upspeed = StringUtils.str_filesize(torrent.rateUpload)
                speed = "%s%sB/s %s%sB/s" % (chr(8595), _dlspeed, chr(8593), _upspeed)
            # 进度
            progress = round(torrent.progress)
            DispTorrents.append({
                'id': torrent.hashString,
                'name': torrent.name,
                'speed': speed,
                'state': state,
                'progress': progress
            })
        return DispTorrents

    def set_speed_limit(self, download_limit=None, upload_limit=None):
        """
        设置速度限制
        :param download_limit: 下载速度限制，单位KB/s
        :param upload_limit: 上传速度限制，单位kB/s
        """
        if not self.trc:
            return
        try:
            session = self.trc.get_session()
            download_limit_enabled = True if download_limit else False
            upload_limit_enabled = True if upload_limit else False
            if download_limit_enabled == session.speed_limit_down_enabled and \
                    upload_limit_enabled == session.speed_limit_up_enabled and \
                    download_limit == session.speed_limit_down and \
                    upload_limit == session.speed_limit_up:
                return
            self.trc.set_session(
                speed_limit_down=download_limit if download_limit != session.speed_limit_down
                else session.speed_limit_down,
                speed_limit_up=upload_limit if upload_limit != session.speed_limit_up
                else session.speed_limit_up,
                speed_limit_down_enabled=download_limit_enabled,
                speed_limit_up_enabled=upload_limit_enabled
            )
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 设置速度限制出错：{str(err)}")
            return False

    def recheck_torrents(self, ids):
        if not self.trc:
            return False
        ids = self.__parse_ids(ids)
        try:
            return self.trc.verify_torrent(ids=ids)
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 校验种子出错：{str(err)}")
            return False

    def get_client_speed(self):
        if not self.trc:
            return False
        try:
            session_stats = self.trc.session_stats(timeout=30)
            if session_stats:
                return {
                    "up_speed": session_stats.upload_speed,
                    "dl_speed": session_stats.download_speed
                }
            return False
        except Exception as err:
            log.error(f"【{self.client_name}】{self.name} 获取客户端速度出错：{str(err)}")
            return False
