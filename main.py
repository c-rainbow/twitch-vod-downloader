import requests
import datetime
import sys
import json
import os
from os import path
import glob
from urllib.parse import urlparse

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
def GetVideoData(video_id: str) -> object:
  video_url = VIDEO_URL.format(video_id=video_id)
  r = requests.get(video_url, headers=API_HEADERS)
  json_data = r.json()
  return json_data


# If stream is in progress
def IsProcessing(video_json: object) -> bool:
  return False


def GetUsername(video_json: object) -> str:
  username = video_json['channel']['name']
  return username


def GetBaseUrlsByResolution(video_json):
  preview_url = video_json['animated_preview_url']
  print('preview_url:', preview_url)
  storyboard_index = preview_url.find('storyboards/')
  base_url = preview_url[:storyboard_index]
  resolutions = list(video_json['resolutions'].keys()) + ['audio_only']
  
  base_urls_by_resolution = {resolution: base_url + resolution + '/'  for resolution in resolutions}
  return base_urls_by_resolution

def GetPlaylistUrl(base_url):
  return base_url + 'index-dvr.m3u8'

def GetVideoFileUrls(base_url, playlist_content):
  lines = playlist_content.split('\n')
  lines = [base_url + line for line in lines if line != '' and not line.startswith('#')]
  return lines

def GetFilenameFromUrl(video_url):
  last_slash = video_url.rfind('/')
  filename = video_url[last_slash+1:]
  return filename

def TryDownloadingVideo(video_url):
  filename = GetFilenameFromUrl(video_url)

  if filename.endswith('-unmuted.ts'):
    # Try unmuted version first
    r = requests.get(video_url)
    if r.status_code >= 400:
      print('Downloading unmuted URL failed with', r.status_code, 'for', filename, '. Trying muted URL...')
      video_url = video_url.replace('-unmuted.ts', '-muted.ts')
    else:
      return r.content
  
  if filename.endswith('-muted.ts'):
    # Try muted URL
    r = requests.get(video_url)
    if r.status_code >= 400:
      print('Downloading unmuted URL failed with', r.status_code, 'for', filename)
      video_url = video_url.replace('-unmuted.ts', '.ts')
    else:
      return r.content
    
  # Lastly, try normal URL
  r = requests.get(video_url)
  if r.status_code >= 400:
    print('Downloading failed with', r.status_code, 'for', filename)
    return None
  return r.content


def main():
    # Video
    video_id = VIDEO_ID
    video_json = GetVideoData(video_id)
    print(json.dumps(video_json))
    username = GetUsername(video_json)
    print(username)
    
    
    
    
    return
    base_urls_by_resolution = GetBaseUrlsByResolution(video_json)
    print(base_urls_by_resolution)

    base_url = base_urls_by_resolution[VIDEO_QUALITY]
    playlist_url = GetPlaylistUrl(base_url)
    playlist_content = requests.get(playlist_url).text

    file_urls = GetVideoFileUrls(base_url, playlist_content)

    dir_path = './{username}/{video_id}/'.format(username=username, video_id=video_id)

    directory = os.makedirs('./{username}/{video_id}/'.format(username=username, video_id=video_id), exist_ok=True)

    info_file_path = os.path.join(dir_path, 'info.json')
    with open(info_file_path, 'w', encoding='utf8') as f:
      json.dump(video_json, f, indent=2, ensure_ascii=False)

    playlist_file_path = os.path.join(dir_path, 'playlist.m3u8')
    with open(playlist_file_path, 'w', encoding='utf8') as f:
      f.write(playlist_content)

    video_urls_path = os.path.join(dir_path, 'video_urls.txt')
    with open(video_urls_path, 'w', encoding='utf8') as f:
      f.write('\n'.join(file_urls))

    return username, video_id
    
def Download(username, video_id):
  dir_path = './{username}/{video_id}/'.format(username=username, video_id=video_id)
  video_urls_path = os.path.join(dir_path, 'video_urls.txt')
  with open(video_urls_path, 'r', encoding='utf8') as f:
    lines = f.read().split('\n')
    
  if START_INDEX:
    if END_INDEX is not None:
        lines = lines[START_INDEX:END_INDEX]
    else:
        lines = lines[START_INDEX:]
  
  for file_url in lines:
    filename = GetFilenameFromUrl(file_url)
    file_path = os.path.join(dir_path, filename)
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        print('Exists:', filename)
        continue
        
    content = TryDownloadingVideo(file_url)
    if content is not None:
      with open(file_path, 'wb') as f:
        f.write(content)
        print('Downloaded', filename)
  

def CombineFiles(path):
  #path = dir_path = './{username}/{video_id}/'.format(username=STREAMER_USERNAME, video_id=VIDEO_ID)

  filelist = glob.glob(path + '*.ts')
  print(filelist)
  
  if END_INDEX:
    filelist = filelist[START_INDEX:END_INDEX]

  with open(path + 'combined.ts', 'wb') as combined_file:
    for filename in filelist:
      with open(filename, 'rb') as ts_f:
        ts_content = ts_f.read()
        combined_file.write(ts_content)


if __name__ == '__main__':
  #username, video_id = main()
  main()
  #Download(username, video_id)
  
  # CombineFiles()