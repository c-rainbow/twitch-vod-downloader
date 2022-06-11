import os

# Load Twitch client ID from .env file
from dotenv import load_dotenv
load_dotenv()

from twitch_vod_downloader import downloader


TWITCH_CLIENT_ID = os.environ['TWITCH_CLIENT_ID']
VIDEO_ID = os.environ['VIDEO_ID']  # ex: 123456789 in https://www.twitch.tv/videos/123456789
VIDEO_QUALITY = '360p30'  # os.environ['VIDEO_QUALITY']


  
if __name__ == '__main__':
  downloader = downloader.VodDownloader(VIDEO_ID, client_id=TWITCH_CLIENT_ID, quality=VIDEO_QUALITY)
  downloader.Download()