import logging
import time
import re

import pdb


from transmission_rpc import Client, TransmissionError
from transmission_rpc.error import (
    TransmissionConnectError,
    TransmissionAuthError,
)

# https://transmission-rpc.readthedocs.io/en/stable/

logger = logging.getLogger(__name__)

class CustomFile:
    def __init__(self, file):
      self.name = file['name']
    def __str__(self):
        return f"CustomFile(name='{self.name}')"

class CustomTorrent:
    def __init__(self, fields):
        self._fields = fields
        self.id = fields['id']
        self.name = fields['name']
        self.hash = fields['hashString']
        self.status = fields['status']
        self.labels = fields['labels']
        self.save_path = fields['downloadDir']
        self.files = [ CustomFile(file) for file in fields['files'] ]
    def files_str(self):
        return str([f"CustomFile(name='{file["name"]}')" for file in self._fields['files']])
    def __str__(self):
        return f"CustomTorrent(id={self.id}, name='{self.name}', hash='{self.hash}', status={self.status}, labels={self.labels}, save_path='{self.save_path}', files={self.files_str()})"

class TrDownloader:
    def __init__(self, host: str, username: str, password: str, ssl: bool):
        host, port = self.parse_host(host)
        self._client = self.connect(host, port, username, password)
        self.host = host
        self.port = port
        self.username = username
        self.connect(host, port, username, password)

    def parse_host(self, host_str: str):
        regex = re.compile(r'(?:(?:http|https):\/\/)?([\w\d\.-]+:[\d]+)')
        host_str = regex.search(host_str).group(1)
        host, port = host_str.split(":")

        try:
            return host, int(port)
        except ValueError:
            logger.warning("Cannot parse port, use default port 9091")
            return host_str, 9091
        except Exception as e:
            logger.error(f"Unknown error: {e}, use default port 9091")
            return host_str, 9091

    def auth(self):
        try:
            self._client.get_session()
            return True
        except TransmissionError:
            return False

    def logout(self):
        pass

    def connect(self, host: str, port: int, username: str, password: str, retry=3):
        times = 0
        while times < retry:
            try:
                return Client(host=host, port=port, username=username, password=password)
            except TransmissionAuthError:
                logger.error(
                    f"Can't login Transmission Server {self.host} by {self.username}, retry in {5} seconds."
                )
                time.sleep(5)
                times += 1
            except TransmissionConnectError:
                logger.error("Cannot connect to TransmissionServer")
                logger.info("Please check the IP and port in settings")
                time.sleep(10)
                times += 1
            except Exception as e:
                logger.error(f"Unknown error: {e}")
                break
        raise Exception("Cannot connect to TransmissionServer")

    def add_torrent(self, torrent: str, download_dir: str, labels):
        try:
            self._client.add_torrent(torrent=torrent, download_dir=download_dir, labels=labels, paused=False)
            return True
        except TransmissionError:
            return False

    def add_torrents(self, torrent_urls, torrent_files, save_path, category):
        try:
            if torrent_urls:
                for torrent in torrent_urls:
                    self.add_torrent(torrent, save_path, labels=[category])
            if torrent_files:
                for torrent in torrent_files:
                    self.add_torrent(torrent, save_path, labels=[category])
            return True
        except TransmissionError:
            return False

    def torrents_delete(self, ids):
        return self._client.remove_torrent(ids, delete_data=True)

    def torrents_rename_file(self, torrent_id, old_path, new_path) -> bool:
        # old path just use to be compatible with download_client.py
        torrent = self._client.get_torrent(torrent_id)
        try:
            # location是相对于这个种子的, 例如一个种子里有很多文件
            self._client.rename_torrent_path(torrent_id, location=torrent.name, name=new_path)
            return True
        except TransmissionError:
            logger.debug(f"Error: {torrent.name} >> {new_path}")
            return False

    def move_torrent(self, ids, location):
        self._client.move_torrent_data(ids, location)

    def torrents_info(self, status_filter, category, tag=None):
        # ./.venv/lib/python3.12/site-packages/transmission_rpc/constants.py TORRENT_GET_ARGS
        # KEY_MAP = {"hashString": "hash", "downloadDir": "save_path"}
        arguments = [
            "id",
            "name",
            "hashString",
            "status",
            "labels",
            "downloadDir",
            "files"
        ]
        # 返回的是torrent列表,torrent对象里有个files属性,是个字典
        torrents = self._client.get_torrents(arguments=arguments)
        # for torrent in torrents:
        #     print('0 ==> ', torrent.fields)
        custom_torrents = [CustomTorrent(torrent.fields) for torrent in torrents]
        torrents_info = self._filter_status(custom_torrents, status_filter)
        if category:
            torrents_info = [
                torrent for torrent in torrents_info if category in torrent.labels
            ]
        # NOTE: To compatible with qbittorrent api we use category as label
        return torrents_info

    def _filter_status(self, torrents_info, status_filter: str):
        """
        Filter torrents by status
        Docs: https://github.com/transmission/transmission/blob/main/docs/rpc-spec.md#33-torrent-accessor-torrent-get
        """
        if status_filter == "completed":
            # We regard torrents queue to seed as completed
            return [torrent for torrent in torrents_info if torrent.status >= 5]
        elif status_filter == "downloading":
            return [torrent for torrent in torrents_info if torrent.status == 4]
        elif status_filter == "inactive":
            return [torrent for torrent in torrents_info if torrent.status <= 3]

        return torrents_info

    def set_category(self, ids, category):
        try:
            self._client.change_torrent(ids, labels=[category])
        except TransmissionError:
            logger.warning(f"[Downloader] Category {category} add failed")

    def get_torrent_path(self, torrent_id):
        pass

    def add_tag(self, torrent_id):
        pass

    def rename_torrent_path(self, torrent_id):
        pass