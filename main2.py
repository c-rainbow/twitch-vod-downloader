import os

from dotenv import load_dotenv

from twitch_vod_downloader import downloader

# Load Twitch client ID from .env file
load_dotenv()


CLIENT_ID = os.environ['CLIENT_ID']
VIDEO_ID = os.environ['VIDEO_ID']  # ex: 123456789 in https://www.twitch.tv/videos/123456789
VIDEO_QUALITY = os.environ['VIDEO_QUALITY']


if __name__ == '__main__':
  vod_downloader = downloader.VodDownloader(VIDEO_ID, CLIENT_ID, quality=VIDEO_QUALITY)
  vod_downloader.Download()