from typing import Any, List, Optional, Tuple
from urllib.parse import urljoin
import requests

from twitch_vod_downloader import stringutil


# Get JSON content
def FetchJson(url: str, headers: dict[str, Any]) -> Tuple[int, Optional[dict[str, Any]]]:
  r = requests.get(url, headers=headers)    
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.json())


# Get text content
def FetchText(url: str) -> Tuple[int, Optional[str]]:
  r = requests.get(url)    
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.text)


# Get video file HTTP status and content
def FetchBinary(base_url: str, filename: str) -> Tuple[int, Optional[bytes]]:
  url = urljoin(base_url, filename)
  r = requests.get(url)
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.content)


# Get segment indexes from .m3u8 HLS playlist
def FetchSegmentIndexes(playlist_url: str) -> List[str]:
  status_code, playlist_content = FetchText(playlist_url)
  if not playlist_content:
    raise Exception('Getting the playlist content failed with status %d' % status_code)

  segment_indexes = stringutil.GetSegmentIndexes(playlist_content)
  return segment_indexes