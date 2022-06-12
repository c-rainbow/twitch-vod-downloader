# twitch-vod-downloader
Download Twitch VOD from the beginning to the end, even if the stream is in progress


Copy .env.sample into .env, fill the environment variables, and run

```
python main.py [-h] -v VIDEO -c CLIENT_ID [-q QUALITY] [-o OUTPUT_PATH]

### Arguments

  -h, --help            show this help message and exit
  -v VIDEO, --video VIDEO, --video-id VIDEO
                        Video ID. For example, if the URL is https://twitch.tv/videos/123456789, then the video ID is 123456789
  -c CLIENT_ID, --client-id CLIENT_ID
                        Twitch API client ID
  -q QUALITY, --quality QUALITY
                        Quality of the video to download, default to "chunked"
  -o OUTPUT_PATH, --output-path OUTPUT_PATH
                        Output path of the downloaded files. Default to ./downloaded/{username}/{video_id}/{quality}/
-
```
