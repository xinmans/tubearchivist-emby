"""set metadata to episodes"""

from datetime import datetime

from src.connect import Jellyfin, TubeArchivist, clean_overview
from src.static_types import TAVideo

import os
import logging
from logging.handlers import RotatingFileHandler

logfile_name = '/app/logs/' + os.path.basename(__file__).split('.')[0] + '.log'
logging.basicConfig(
    handlers=[
        RotatingFileHandler(
            logfile_name,
            # Limit the size to 10000000Bytes ~ 10MB 
            maxBytes=10000000,
            backupCount=5
        )
    ],
    format='%(asctime)s %(levelname)-4s %(filename)s:%(funcName)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

class Episode:
    """interact with an single episode"""

    def __init__(self, youtube_id: str, jf_id: str):
        self.youtube_id: str = youtube_id
        self.jf_id: str = jf_id

    def get_ta_video(self) -> TAVideo:
        """get ta metadata"""
        ta_video: TAVideo = TubeArchivist().get_video(self.youtube_id)
        return ta_video

    def sync(self, ta_video: TAVideo) -> None:
        """sync episode metadata"""
        self.update_metadata(ta_video)
        self.update_artwork(ta_video)

    def update_metadata(self, ta_video: TAVideo) -> None:
        """update jellyfin metadata from item_id"""
        published: str = ta_video["published"]
        published_date: datetime = datetime.fromisoformat(published)
        logging.info(f"published_date: {published_date}")
        data: dict = {
            "Id": self.jf_id,
            "Name": ta_video.get("title"),
            "GenreItems": [],
            "Tags": [],
            "ProductionYear": published_date.year,
            "ProviderIds": {},
            "IndexNumber": published_date.year,
            "ParentIndexNumber": published_date.year,
            "PremiereDate": published_date.isoformat(),
            "Overview": self._get_desc(ta_video),
            "Studios": [{"Name": "YouTubeAchivist"}],
        }
        logging.info(f"data: {data}")
        path: str = f"Items/{self.jf_id}"
        res = Jellyfin().post(path, data)
        logging.info(f"res: {res}")

    def update_artwork(self, ta_video: TAVideo) -> None:
        """update episode artwork in jf"""
        thumb_path: str = ta_video["vid_thumb_url"]
        thumb_base64: bytes = TubeArchivist().get_thumb(thumb_path)
        path: str = f"Items/{self.jf_id}/Images/Primary"
        res = Jellyfin().post_img(path, thumb_base64)
        logging.info(f"res: {res}")

    def _get_desc(self, ta_video: TAVideo) -> str | bool:
        """get description"""
        raw_desc: str = ta_video["description"]
        if not raw_desc:
            return False

        desc_clean: str = clean_overview(raw_desc)
        return desc_clean
