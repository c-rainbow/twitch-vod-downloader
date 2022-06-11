import collections
import os
import time
from typing import Optional, Set, Tuple

from twitch_vod_downloader import fetch
from twitch_vod_downloader import fileutil
from twitch_vod_downloader import stringutil
from twitch_vod_downloader import vod_info


VOD_URL = 'https://api.twitch.tv/v5/videos/{vod_id}'
DEFAULT_OUTPUT_PATH = './downloaded/{username}/{vod_id}/{quality}'


# Sleep for this duration before refreshing the playlist
# when all previous segments were downloaded and more segments were expected.
#
# NOTE: Although each segment is around 10 seconds long,
# the playlist file is often not updated for 30-60 seconds.
DEFAULT_SLEEP_DURATION_IN_SECONDS = 10.0


class VodDownloader:
    
  def __init__(self, vod_id: str, client_id: str, quality: str='chunked', output_path: Optional[str]=None,
               sleep_duration: float=DEFAULT_SLEEP_DURATION_IN_SECONDS):
    self._vod_id = vod_id
    self._client_id = client_id
    self._resolution = quality
    self._custom_output_path = output_path
    self._sleep_duration = sleep_duration

  def FetchVodInfo(self) -> vod_info.VodInfo:
    url = VOD_URL.format(vod_id=self._vod_id)
    status_code, vod_json = fetch.FetchJson(url, headers=self._GetApiHeader())
    if not vod_json:
      raise Exception('Fetching VOD info JSON failed with status %s' % status_code)

    return vod_info.VodInfo(vod_json)
  
  def Download(self):
    vod_info = self.FetchVodInfo()

    # Get the base URL for the desired VOD ID and resolution
    base_url = vod_info.GetBaseUrlByResolution(self._resolution)
    if not base_url:
      all_resolutions = ', '.join(vod_info.GetResolutions())
      raise Exception('Resolution "%s" is invalid. Valid ones are: %s' % (self._resolution, all_resolutions))

    # Create output path directory
    output_path = self._custom_output_path or self._GetDefaultOutputPath(vod_info)
    os.makedirs(output_path, exist_ok=True)
    
    # Get all segment indexes from the content of the .m3u8 HLS playlist
    playlist_url = stringutil.GetPlaylistUrl(base_url)
    segment_indexes = fetch.FetchSegmentIndexes(playlist_url)
    
    # Keep track of which segments are downloaded.
    downloaded_indexes: Set[str] = set()
    failed_indexes: Set[str] = set()  # TODO: Is there a need for two sets?
    unfinished_indexes = collections.deque(segment_indexes)
    
    # The loop should repeat until all segments are downloaded and the stream is over.
    while unfinished_indexes or vod_info.IsStreamInProgress():
      # Download unprocessed segments before checking for more
      if unfinished_indexes:
        segment_index = unfinished_indexes.popleft()
        
        # Skip if the segment is already downloaded
        existing_filename = fileutil.GetExistingSegment(output_path, segment_index)
        if existing_filename:
          downloaded_indexes.add(segment_index)
          print('Segment file', existing_filename, 'already exists. Skipping...')
          continue
        
        # Download the segment
        downloaded_filename, content = self.TryDownloadingSegment(base_url, segment_index)
        if content is None:  # Download failed
          failed_indexes.add(segment_index)
          print('Download failed for segment', segment_index)
        else:
          downloaded_indexes.add(segment_index)
          fileutil.WriteBinary(output_path, downloaded_filename, content)
          print('Download successful for segment', segment_index, 'to', downloaded_filename)

      # Downloaded all segments in unfinished_indexes, but the stream is still in progress.
      # Check for new segments every N seconds
      elif vod_info.IsStreamInProgress():
        print('Stream is in progress. Checking for more segments after', self._sleep_duration, 'seconds...')

        # Sleep for N seconds and get new VOD info and playlist content
        time.sleep(self._sleep_duration)
        
        # Update VOD info to check if the stream is still in progress
        vod_info = self.FetchVodInfo()
        
        # Refresh the playlist content, check if there are more indexes
        segment_indexes = fetch.FetchSegmentIndexes(playlist_url)
        print('Found total', len(segment_indexes), 'segment indexes in the playlist')

        # Add all new segment indexes to the queue
        for segment_index in segment_indexes:
          if segment_index in downloaded_indexes or segment_index in failed_indexes:
            continue
          unfinished_indexes.append(segment_index)
          print('Newly found segment', segment_index, 'is added to the queue') 
  
  # Download the video file. Try to download unmuted version if it exists.
  # For example, there can be 1234.ts, 1234-muted.ts, and 1234-unmuted.ts.
  # We need to first try -unmuted.ts, then .ts, and then -muted.ts.
  def TryDownloadingSegment(self, base_url: str, segment_index: str) -> Tuple[Optional[str], Optional[bytes]]:
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
  def _GetDefaultOutputPath(self, vod_info: vod_info.VodInfo) -> str:
    username = vod_info.GetUsername()
    output_path = DEFAULT_OUTPUT_PATH.format(
        username=username, vod_id=self._vod_id, quality=self._resolution)
    return output_path
  
  def _GetApiHeader(self) -> dict[str, str]:
    return {
      'Client-ID': self._client_id,
      'Accept': 'application/vnd.twitchtv.v5+json',
      'Content-Type': 'application/json',
    }