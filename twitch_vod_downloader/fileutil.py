import os
from typing import Optional, Tuple

from twitch_vod_downloader import stringutil


# Get the downloaded filename of the segment
def GetExistingSegment(output_path: str, segment_index: str) -> Optional[str]:
  filenames = stringutil.GetSegmentFilenames(segment_index)
  
  for filename in filenames:
    file_path = os.path.join(output_path, filename)
    if os.path.exists(file_path) and os.path.getsize(file_path):
      return filename
    
  return None
  

# Write to a text file
def WriteText(output_path: str, filename: str, content: str):
  file_path = os.path.join(output_path, filename)
  with open(file_path, 'w') as f:
    f.write(content)


# Write to a binary file
def WriteBinary(output_path: str, filename: str, content: bytes):
  file_path = os.path.join(output_path, filename)
  with open(file_path, 'wb') as f:
    f.write(content)
