from typing import Any, Tuple, Union
from urllib.parse import urljoin
import requests


# Get JSON content
def FetchJson(url: str, headers: dict[str, Any]) -> Tuple[int, Union[str, None]]:
  r = requests.get(url, headers=headers)    
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.json())


# Get text content
def FetchText(url: str) -> Tuple[int, Union[str, None]]:
  r = requests.get(url)    
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.text)


# Get video file HTTP status and content
def FetchBinary(base_url: str, filename: str) -> Tuple[int, Union[bytes, None]]:
  url = urljoin(base_url, filename)
  r = requests.get(url)
  if r.status_code >= 400:
    return (r.status_code, None)
  return (r.status_code, r.content)