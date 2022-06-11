from typing import Any


class VodInfo:
  
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
  def GetBaseUrlsByResolutions(self) -> dict[str, str]:
    animated_preview_url: str = self._vod_json['animated_preview_url']
    storyboard_index = animated_preview_url.find('/storyboards/')
    
    root_url: str = animated_preview_url[:storyboard_index]
    resolutions = self.GetResolutions()
    base_urls_by_resolution = {
      resolution: '%s/%s/' % (root_url, resolution) for resolution in resolutions
    }

    return base_urls_by_resolution

  # Base URL for a specific resolution
  def GetBaseUrlByResolution(self, resolution: str) -> str:
    base_urls_by_resolutions = self.GetBaseUrlsByResolutions()
    return base_urls_by_resolutions[resolution]
