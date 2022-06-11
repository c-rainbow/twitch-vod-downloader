import os
from typing import Tuple

from twitch_vod_downloader import stringutil


# Check if the segment is already downloaded
def SegmentExists(output_path: str, segment_index: str) -> bool:
  filenames = stringutil.GetSegmentFilenames(segment_index)
  
  for filename in filenames:
    file_path = os.path.join(output_path, filename)
    if os.path.exists(file_path):
      return True
    
  return False
  

def WriteToTextFile(output_path: str, filename: str, content: str):
  file_path = os.path.join(output_path, filename)
  with open(file_path, 'w') as f:
    f.write(content)


def WriteToBinaryFile(output_path: str, filename: str, content: bytes):
  file_path = os.path.join(output_path, filename)
  with open(file_path, 'wb') as f:
    f.write(content)