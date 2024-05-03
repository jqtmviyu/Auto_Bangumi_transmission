import logging
import re
import time
from dataclasses import dataclass
from typing import List

from transmission_rpc import Client, TransmissionError
from transmission_rpc.error import (
    TransmissionAuthError,
    TransmissionConnectError,
)

# https://transmission-rpc.readthedocs.io/en/stable/

logger = logging.getLogger(__name__)


@dataclass
class CustomFile:
    name: str

    def __init__(self, file: dict):
        name = file.get("name")
        if name is not None:
            self.name = name
        else:
            self.name = ""


@dataclass
class CustomTorrent:
    id: int
    name: str
    hash: str
    status: str
    labels: List[str]
    save_path: str
    files: List[CustomFile]

    def __init__(self, fields: dict):
        # hashString => hash, downloadDir ==> save_path
        self.__dict__.update(
            {
                "id": fields.get("id"),
                "name": fields.get("name"),
                "hash": fields.get("hashString"),
                "status": fields.get("status"),
                "labels": fields.get("labels"),
                "save_path": fields.get("downloadDir"),
                "files": [CustomFile(file) for file in fields.get("files", [])],
            }
        )


class TrDownloader:
    def __init__(self, host: str, username: str, password: str, ssl: bool):
        host, port = self.parse_host(host)
        self._client = self.connect(host, port, username, password)
        self.host = host
        self.port = port
        self.username = username
        self.connect(host, port, username, password)
        logger.debug("[TR] Init")

    def parse_host(self, host_str: str):
        regex = re.compile(r"(?:(?:http|https):\/\/)?([\w\d\.-]+:[\d]+)")
        host_str = regex.search(host_str).group(1)  # type: ignore
        host, port = host_str.split(":")

        try:
            return host, int(port)
        except ValueError:
            logger.warning("[TR] Cannot parse port, use default port 9091")
            return host_str, 9091
        except Exception as e:
            logger.error(f"[TR] Unknown error: {e}, use default port 9091")
            return host_str, 9091

    def auth(self):
        try:
            self._client.get_session()
            logger.debug("[TR] Auth success")
            return True
        except TransmissionError:
            logger.debug("[TR] Auth failed")
            return False

    def connect(self, host: str, port: int, username: str, password: str, retry=3):
        times = 0
        while times < retry:
            try:
                return Client(
                    host=host, port=port, username=username, password=password
                )
            except TransmissionAuthError:
                logger.error(
                    f"[TR] Can't login Transmission Server {self.host} by {self.username}, retry in {5} seconds."
                )
                time.sleep(5)
                times += 1
            except TransmissionConnectError:
                logger.error("[TR] Cannot connect to TransmissionServer")
                logger.info("[TR] Please check the IP and port in settings")
                time.sleep(10)
                times += 1
            except Exception as e:
                logger.error(f"[TR] Unknown error: {e}")
                break
        raise Exception("[TR] Cannot connect to TransmissionServer")

    def add_torrent(self, torrent, download_dir: str, labels):
        logger.debug(f"[TR] Download dir: {download_dir}")
        if len(torrent) < 10:
            logger.debug(
                f"[TR] Add torrent error, torrent is too short: {len(torrent)}"
            )
            return
        try:
            resp = self._client.add_torrent(
                torrent=torrent, download_dir=download_dir, labels=labels, paused=False
            )
            logger.debug(f"[TR] Add torrent resp : {resp}")
        except TransmissionError:
            logger.debug(f"[TR] Add torrent error: {TransmissionError.message}")

    def add_torrents(self, torrent_urls, torrent_files, save_path, category):
        # print(f"[TR] torrent_urls ==>  {torrent_urls}")
        # print(f"[TR] torrent_files ==>  {torrent_files}")
        # 虽然写的是torrents但是传过来的可能是lsit,也可能是str|bytes
        if isinstance(torrent_urls, str):
            torrent_urls = [torrent_urls]
        if isinstance(torrent_files, bytes):
            torrent_files = [torrent_files]
        try:
            if torrent_urls:
                for torrent in torrent_urls:
                    self.add_torrent(torrent, save_path, labels=[category])
                    time.sleep(1)
            if torrent_files:
                for torrent in torrent_files:
                    self.add_torrent(torrent, save_path, labels=[category])
                    time.sleep(1)
            return True
        except TransmissionError:
            return False

    def __torrents_info(self):
        # ./.venv/lib/python3.12/site-packages/transmission_rpc/constants.py TORRENT_GET_ARGS
        arguments = [
            "id",
            "name",
            "hashString",
            "status",
            "labels",
            "downloadDir",
            "files",
        ]
        # 返回的是torrent列表,torrent对象里有个 fields 字典
        resp = self._client.get_torrents(arguments=arguments)
        # logger.debug(f"[TR] torrents resp: {[torrent.fields  for torrent in resp]}")
        return resp

    def torrents_info(self, status_filter, category, tag=None):
        torrents = self.__torrents_info()
        filtered_results = []
        for torrent in torrents:
            status = torrent.fields.get("status", 0)
            labels = torrent.fields.get("labels", [])
            if (
                status_filter is None
                or (status_filter == "completed" and (status >= 5 or status == 0))
                or (status_filter == "downloading" and status == 4)
                or (status_filter == "inactive" and status > 3)
            ) and (category is None or category in labels):
                filtered_results.append(CustomTorrent(torrent.fields))

        # NOTE: To compatible with qbittorrent api we use category as label
        """
        Filter torrents by status
        Docs: https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#33-torrent-accessor-torrent-get
        """
        # logger.debug(f"[TR] torrents info: {filtered_results}")
        return filtered_results

    # todo 单个种子里有多个文件的情况, 该怎么处理
    # todo 检查传的是单个hash 还是 hash 列表

    def __get_torrentIds_with_hashes(self, hashes):
        # tr-prc的大部分接口都是通过id/[id]来处理的
        torrents = self.__torrents_info()
        ids = []
        if isinstance(hashes, list):
            for torrent in torrents:
                if torrent.fields.get("hashString") in hashes:
                    ids.append(torrent.fields.get("id"))
        # 兼容下单个hash
        elif isinstance(hashes, str):
            for torrent in torrents:
                if torrent.fields.get("hashString") == hashes:
                    ids.append(torrent.fields.get("id"))
                    break
        return ids

    def __get_torrentInfo_with_hash(self, hash):
        torrents = self.__torrents_info()
        info = None
        for torrent in torrents:
            if torrent.fields.get("hashString") == hash:
                info = torrent.fields
                break
        return info

    def torrents_delete(self, hashes):
        logger.debug("TrDownloader.torrents_delete")
        ids = self.__get_torrentIds_with_hashes(hashes)
        if len(ids) != 0:
            self._client.remove_torrent(ids, delete_data=True)

    def torrents_rename_file(self, torrent_hash, old_path, new_path) -> bool:
        info = self.__get_torrentInfo_with_hash(torrent_hash)
        if info:
            try:
                # ! location是文件相对于下载目录的相对路径
                # ! name是文件的文件名, 不包含路径
                logger.debug(f"[TR] rename: {old_path} >> {new_path}")
                resp = self._client.rename_torrent_path(
                    info["id"], location=old_path, name=new_path
                )
                logger.debug(f"[TR] rename resp: {resp}")
                logger.debug(f"[TR] rename: {old_path} >> {new_path} Success")
                return True
            except TransmissionError:
                return False
        else:
            logger.debug(f"[TR] Error: cat't find torrent: {torrent_hash}")
            return False

    def move_torrent(self, hashes, new_location):
        ids = self.__get_torrentIds_with_hashes(hashes)
        self._client.move_torrent_data(ids, new_location)
        logger.debug(f"[TR] move torrent: {ids} to {new_location}")

    def set_category(self, _hash, category):
        ids = self.__get_torrentIds_with_hashes(_hash)
        try:
            if len(ids) != 0:
                self._client.change_torrent(ids, labels=[category])
                logger.debug(f"[TR] Set category [{category}] success")
        except TransmissionError:
            logger.warning(f"[TR] Category {category} add failed")

    def prefs_init(self, prefs):
        # todo 设置参数优化, 先暂时跳过
        pass

    def get_app_prefs(self):
        # todo 当设置里路径为空时, 获取tr下载地址, 保存到ab
        save_path = self._client.get_session().download_dir
        return {"save_path": save_path}

    def add_category(self, category):
        # tr不需要单独创建BangumiCollection分类
        pass

    def get_torrent_path(self, _hash):
        # 实际没有使用
        pass

    def rename_torrent_path(self, torrent_id):
        # 实际没有使用
        pass

    def logout(self):
        # 实际没有使用
        pass

    def check_host(self):
        # 实际没有使用
        pass

    def check_rss(self):
        pass

    def rss_add_feed(self, url, item_path):
        # 实际没有使用
        pass

    def rss_remove_item(self, item_path):
        # 实际没有使用
        pass

    def rss_get_feeds(self):
        # 实际没有使用
        pass

    def rss_set_rule(self, rule_name, rule_def):
        # 实际没有使用
        pass

    def get_download_rule(self):
        # 实际没有使用
        pass

    def check_connection(self):
        # 实际没有使用
        pass

    def remove_rule(self, rule_name):
        # 实际没有使用
        pass

    def add_tag(self, _hash):
        # 实际没有使用
        pass
