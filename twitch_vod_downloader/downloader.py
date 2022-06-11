import collections
import os
import time
from typing import Set, Tuple, Union

from twitch_vod_downloader import fetch
from twitch_vod_downloader import fileutil
from twitch_vod_downloader import stringutil
from twitch_vod_downloader import vod_info


VOD_URL = 'https://api.twitch.tv/v5/videos/{vod_id}'

SLEEP_DURATION_IN_SECONDS = 5.0


class VodDownloader:
    
  def __init__(self, vod_id: str, client_id: str=None, quality: str='chunked', output_path: str=None):
    self._vod_id = vod_id
    self._client_id = client_id
    self._quality = quality
    self._output_path = output_path

  def GetVodInfo(self) -> vod_info.VodInfo:
    url = VOD_URL.format(vod_id=self._vod_id)
    vod_json = fetch.FetchJson(url, headers=self._GetApiHeader())
    return vod_info.VodInfo(vod_json)
  
  def Download(self):
    vod_info = self.GetVodInfo()
    # Lazily set output path
    self._output_path = self._CreateOutputDirectory(vod_info)
    
    # Get base URLs and the content of the .m3u8 HLS playlist.
    base_urls = vod_info.GetBaseUrlsByResolution()
    base_url = base_urls.get(self._quality)
    playlist_url = stringutil.GetPlaylistUrl(base_url)
    playlist_content = fetch.FetchText(playlist_url)
    segment_indexes = stringutil.GetSegmentIndexes(playlist_content)
    
    # Keep track of which segments are downloaded.
    downloaded_indexes: Set[str] = set()
    failed_indexes: Set[str] = set()
    unfinished_indexes: collections.deque[str] = collections.deque(segment_indexes)
    
    while len(unfinished_indexes) or vod_info.IsStreamInProgress():
      if len(unfinished_indexes):
        segment_index = unfinished_indexes.popleft()
        
        # Skip if the segment is already downloaded
        if fileutil.SegmentExists(self._output_path, segment_index):
          downloaded_indexes.add(segment_index)
          continue
        
        downloaded_filename, content = self.TryDownloadingSegment(base_url, segment_index)
        if content is None:  # Download failed
          failed_indexes.add(segment_index)
        else:
          downloaded_indexes.add(segment_index)
          fileutil.WriteToBinaryFile(self.output_path, downloaded_filename, content)

      # Downloaded all segments in unfinished_indexes, but the stream is still in progress.
      # Check for new segments every N seconds
      elif vod_info.IsStreamInProgress():
        # Sleep for N seconds and get new VOD info and playlist content
        time.sleep(SLEEP_DURATION_IN_SECONDS)
        
        # Update VOD info to check if the stream is still in progress
        vod_info = self.GetVodInfo()
        
        # Refresh the playlist content, check if there are more indexes
        playlist_content = fetch.FetchText(playlist_url)
        segment_indexes = stringutil.GetSegmentIndexes(playlist_content)
        for segment_index in segment_indexes:
          if segment_index in downloaded_indexes:
            continue
          if segment_index in failed_indexes:
            continue
          unfinished_indexes.append(segment_index)      
  
  # Download the video file. Try to download unmuted version if it exists.
  # For example, there can be 1234.ts, 1234-muted.ts, and 1234-unmuted.ts.
  # We need to first try -unmuted.ts, then .ts, and then -muted.ts.
  def TryDownloadingSegment(self, base_url: str, segment_index: str) -> Union[Tuple[str, bytes], Tuple[None, None]]:
    unmuted_filename, original_filename, muted_filename = stringutil.GetSegmentFilenames(segment_index)
    
    # TODO: Try downloading 2-3 times?
    
    # First, try the unmuted filename
    _, content = fetch.FetchBinary(base_url, unmuted_filename)
    if content is not None:
      return (unmuted_filename, content)
    
    # Second, try the original filename
    _, content = fetch.FetchBinary(base_url, original_filename)
    if content is not None:
      return (original_filename, content)
      
    # Lastly, try the muted filename
    _, content = fetch.FetchBinary(base_url, muted_filename)
    if content is not None:
      return (muted_filename, content)

    # If the video could not be downloaded, return None
    return (None, None)
  
  # Create output directory for the downloaded VODs and other metadata
  def _CreateOutputDirectory(self, vod_info: vod_info.VodInfo) -> str:
    if self._output_path:
      os.makedirs(self._output_path, exist_ok=True)  
      return self._output_path
    else:
      username = vod_info.GetUsername()
      dir_path = './downloaded/{username}/{vod_id}/{quality}'.format(
          username=username, vod_id=self._vod_id, quality=self._quality)
      os.makedirs(dir_path, exist_ok=True)
      return dir_path
  
  def _GetApiHeader(self) -> dict[str, str]:
    return {
      'Client-ID': self._client_id,
      'Accept': 'application/vnd.twitchtv.v5+json',
      'Content-Type': 'application/json',
    }