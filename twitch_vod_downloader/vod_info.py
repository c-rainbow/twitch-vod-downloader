from typing import Any, Tuple, Union
import requests
import json
import os
from os import path
import glob
from urllib.parse import urljoin
import re

# Load Twitch client ID from .env file
from dotenv import load_dotenv
load_dotenv()

TWITCH_CLIENT_ID = os.environ['TWITCH_CLIENT_ID']
VIDEO_ID = os.environ['VIDEO_ID']  # ex: 123456789 in https://www.twitch.tv/videos/123456789
VIDEO_QUALITY = os.environ['VIDEO_QUALITY']


VIDEO_URL = "https://api.twitch.tv/v5/videos/{video_id}"


START_INDEX = 0
END_INDEX = None # START_INDEX + 40

API_HEADERS = {
    'Client-ID': TWITCH_CLIENT_ID,
    'Accept': 'application/vnd.twitchtv.v5+json',
    'Content-Type': 'application/json',
}



class VodInfo:
  _vod_json: dict[str, Any] = None
  
  def __init__(self, vod_json: dict[str, Any]):
    self._vod_json = vod_json
    
  # Extract streamer's username from the VOD data JSON
  def GetUsername(self) -> str:
    username: str = self._vod_json['channel']['name']
    return username

  # List of available resolutions (ex: '160p30', '480p30', '720p60', 'chunked', 'audio_only', etc)
  def GetResolutions(self) -> list[str]:
    resolution_dict: dict[str, str] = self._vod_json['resolutions']
    return list(resolution_dict.keys()) + ['audio_only']

  # If stream is in progress
  def IsStreamInProgress(self) -> bool:
    template_preview_url = self._vod_json['preview']['template']
    return '404_processing' in template_preview_url

  # Base URLs by resolution.
  # The .m3u8 playlist and .ts segment files exist under these paths
  def GetBaseUrlsByResolution(self) -> dict[str, str]:
    animated_preview_url: str = self._vod_json['animated_preview_url']
    storyboard_index = animated_preview_url.find('/storyboards/')
    
    base_url: str = animated_preview_url[:storyboard_index]
    resolutions = self.GetResolutions()
    base_urls_by_resolution = {
      resolution: '%s/%s/' % (base_url, resolution) for resolution in resolutions
    }

    return base_urls_by_resolution
