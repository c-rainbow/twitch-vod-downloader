import re
from typing import List, Tuple


# Get all possible video segment file names from the index.
# ex) '27.ts', '27-muted.ts', or '27-unmuted.ts' from '27'
def GetSegmentFilenames(segment_index: str) -> Tuple[str, str, str]:
  unmuted_filename = '%s-unmuted.ts' % segment_index
  original_filename = '%s.ts' % segment_index
  muted_filename = '%s-muted.ts' % segment_index
  return (unmuted_filename, original_filename, muted_filename)


# Get all video segment indexes from playlist content text.
# Video segment index is the beginning numeric part of the filename.
# ex) '27' from '27.ts', '27-muted.ts', or '27-unmuted.ts'
def GetSegmentIndexes(playlist_content: str) -> List[str]:
  lines = playlist_content.split('\n')
  filenames = [
    line.strip() for line in lines
    if line.strip() != '' and not line.startswith('#')
  ]
  
  segment_indexes: list[str] = []
  for filename in filenames:
    index = GetSegmentIndex(filename)
    segment_indexes.append(index)
  
  return segment_indexes


# Get URL of m3u8 HLS playlist file from the base address.
# It is simply 'index-dvr.m3u8'
def GetPlaylistUrl(base_url: str) -> str:
  if base_url.endswith('/'):
    return base_url + 'index-dvr.m3u8'
  else:
    return base_url + '/index-dvr.m3u8'


# Get video segment index from filename
# ex) '27' from '27.ts', '27-muted.ts', or '27-unmuted.ts'
def GetSegmentIndex(filename: str) -> str:
  match = re.match(r'\d+', filename)
  if match is None:
    raise ValueError('File %s does not start with a number' % filename)
  return match.group()