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


# Get VOD data
def GetVideoData(video_id: str) -> dict[str, Any]:
  video_url = VIDEO_URL.format(video_id=video_id)
  r = requests.get(video_url, headers=API_HEADERS)
  json_data = r.json()
  return json_data


# Get text content of the .m3u8 playlist
def GetPlaylistContent(url: str) -> str:
  r = requests.get(url)    
  return r.text


# Get video file HTTP status and content
def GetFileContent(base_url: str, filename: str) -> Tuple[int, Union[bytes, None]]:
  url = urljoin(base_url, filename)
  r = requests.get(url)
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.content)
  
  
# Get unmuted, original muted file names of a video segment
# For example, returns (1234-unmuted.ts, 1234.ts, 1234-muted.ts) from '1234-muted.ts'
def GetPossibleVideoFilenames(filename: str) -> Tuple[str, str, str]:
  match = re.match(r'\d+', filename)
  if match is None:
    raise ValueError('File %s does not start with a number' % filename)
  
  index = match.group()  # Returns the numeric part in the beginning
  return (
    '%s-unmuted.ts' % index, '%s.ts' % index, '%s-muted.ts' % index
  )
    

# Extract streamer's username from the VOD data JSON
def GetUsername(video_json: dict[str, Any]) -> str:
  username: str = video_json['channel']['name']
  return username


# List of available resolutions (ex: '160p30', '480p30', '720p60', 'chunked', etc)
def GetResolutions(video_json: dict[str, Any]) -> list[str]:
  resolution_dict: dict[str, str] = video_json['resolutions']
  return list(resolution_dict.keys()) + ['audio_only']


# If stream is in progress
def IsProcessing(video_json: dict[str, Any]) -> bool:
  template_preview_url = video_json['preview']['template']
  return '404_processing' in template_preview_url


# Base URLs by resolution.
# The .m3u8 playlist and .ts segment files exist under these paths
def GetBaseUrlsByResolution(video_json) -> dict[str, str]:
  animated_preview_url: str = video_json['animated_preview_url']
  storyboard_index = animated_preview_url.find('/storyboards/')
  
  base_url: str = animated_preview_url[:storyboard_index]
  resolutions = GetResolutions(video_json)
  base_urls_by_resolution = {
    resolution: '%s/%s/' % (base_url, resolution) for resolution in resolutions
  }

  return base_urls_by_resolution


# Playlist URLs for a base URL. Simply appends 'index-dvr.m3u8' at the end
def GetPlaylistUrl(base_url: str) -> str:
  return base_url + 'index-dvr.m3u8'


# Names of all .ts files in the playlist
def GetVideoFilenames(playlist_content: str) -> list[str]:
  lines = playlist_content.split('\n')
  filenames = [
    line.strip() for line in lines
    if line.strip() != '' and not line.startswith('#')
  ]
  return filenames


# Check if the segment is already downloaded, whether muted or not.
def IsDownloaded(dir_path: str, filename: str):
  unmuted_filename, original_filename, muted_filename = GetPossibleVideoFilenames(filename)
  
  for name in (unmuted_filename, original_filename, muted_filename):
    file_path = os.path.join(dir_path, name)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
      return True
  
  return False

# Download the video file. Try to download unmuted version if it exists.
# For example, there can be 1234.ts, 1234-muted.ts, and 1234-unmuted.ts.
# We need to first try -unmuted.ts, then .ts, and then -muted.ts.
def TryDownloadingSingleVideo(base_url: str, filename: str) -> Union[Tuple[str, bytes], Tuple[None, None]]:
  unmuted_filename, original_filename, muted_filename = GetPossibleVideoFilenames(filename)
  
  # TODO: Try downloading 2-3 times?
  
  # First, try the unmuted filename
  status_code, content = GetFileContent(base_url, unmuted_filename)
  if content is None:
      print('Downloading the unmuted video URL failed with', status_code, 'for', filename)
  else:
    return (unmuted_filename, content)
  
  # Second, try the original filename
  status_code, content = GetFileContent(base_url, original_filename)
  if content is None:
      print('Downloading the original video URL failed with', status_code, 'for', filename)
  else:
    return (original_filename, content)
    
  # Lastly, try the muted filename
  status_code, content = GetFileContent(base_url, muted_filename)
  if content is None:
      print('Downloading the muted video URL failed with', status_code, 'for', filename)
  else:
    return (muted_filename, content)

  # If the video could not be downloaded, return None
  return (None, None)


def PrepareForDownload() -> Tuple[str, str, list[str]]:
    # Video
    video_json = GetVideoData(VIDEO_ID)
    #print(json.dumps(video_json))
    
    username = GetUsername(video_json)
    print(username)
    
    resolutions = GetResolutions(video_json)
    print(resolutions)
    
    processing = IsProcessing(video_json)
    print(processing)
    
    base_urls_by_resolution = GetBaseUrlsByResolution(video_json)
    print(base_urls_by_resolution)

    base_url = base_urls_by_resolution[VIDEO_QUALITY]
    playlist_url = GetPlaylistUrl(base_url)    
    playlist_content = GetPlaylistContent(playlist_url)
    video_filenames = GetVideoFilenames(playlist_content)

    dir_path = './downloaded/{username}/{video_id}/{quality}'.format(
      username=username, video_id=VIDEO_ID, quality=VIDEO_QUALITY)
    os.makedirs(dir_path, exist_ok=True)

    # Write VOD info, for record
    info_file_path = os.path.join(dir_path, 'info.json')
    with open(info_file_path, 'w', encoding='utf8') as f:
      json.dump(video_json, f, indent=2, ensure_ascii=False)

    # Write playlist content, for record
    playlist_file_path = os.path.join(dir_path, 'playlist.m3u8')
    with open(playlist_file_path, 'w', encoding='utf8') as f:
      f.write(playlist_content)
      
    return (base_url, dir_path, video_filenames)

    
def DownloadVideos(base_url: str, dir_path: str, filenames: list[str]):  
  for filename in filenames:
    # Check if the video segment is already downloaded
    if IsDownloaded(dir_path, filename):
        print('File already exists:', filename)
        continue
    
    downloaded_filename, content = TryDownloadingSingleVideo(base_url, filename)
    if downloaded_filename is not None and content is not None:
      file_path = os.path.join(dir_path, downloaded_filename)
      with open(file_path, 'wb') as f:
        f.write(content)
        print('Downloaded video segment', downloaded_filename)
  

def CombineFiles(path):
  filelist = glob.glob(os.path.join(path, '*.ts'))
  print(filelist)
  
  if END_INDEX:
    filelist = filelist[START_INDEX:END_INDEX]

  with open(os.path.join(path, 'combined.ts'), 'wb') as combined_file:
    for filename in filelist:
      with open(filename, 'rb') as ts_f:
        ts_content = ts_f.read()
        combined_file.write(ts_content)


if __name__ == '__main__':
  base_url, dir_path, video_filenames = PrepareForDownload()
  #DownloadVideos(base_url, dir_path, video_filenames)
  print(dir_path)
  # CombineFiles(dir_path)