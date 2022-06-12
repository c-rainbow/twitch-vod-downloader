import argparse

from twitch_vod_downloader import downloader


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='What video do you want to download?')
  parser.add_argument(
      '-v', '--video', '--video-id', type=str, required=True,
      help='Video ID. For example, if the URL is https://twitch.tv/videos/123456789, then the video ID is 123456789')
  parser.add_argument('-c', '--client-id', type=str, required=True, help='Twitch API client ID')
  parser.add_argument(
      '-q', '--quality', type=str, default='chunked', help='Quality of the video to download, default to "chunked"')
  parser.add_argument(
      '-o', '--output-path', type=str, 
      help='Output path of the downloaded files. Default to ./downloaded/{username}/{video_id}/{quality}/')

  args = parser.parse_args()
  
  vod_downloader = downloader.VodDownloader(
      args.video, args.client_id, quality=args.quality, output_path=args.output_path)
  vod_downloader.Download()