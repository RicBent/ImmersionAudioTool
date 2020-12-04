# ImmersionAudioTool
Creates audio from media files for language immersion

## Warning: This tool is still in Beta! Don't use this unless you know what you are doing yet!

![](https://i.imgur.com/YES6QqX.png) ![](https://i.imgur.com/ehJOtsi.png)

## How to run
- Check if there is a release available for your operating system on the [releases page](https://github.com/RicBent/ImmersionAudioTool/releases/)
- If there is one, download it, extract it and run the executable
- If not, see "How to run from source"

## How to run from source:
- Install ffmpeg
- Install python3 and the following modules
    - PyQt5
    - eyed3
- run iat.py

## How to use:
- Select the input media file (video/audio)
    - You can place exactly one placeholder * for multi file selection
- Select subtitles (*.ass, *.srt)
    - You may leave the line empty if for each media file there is a subtitle file place next to it with the same name
- Select an output file
    - If you selected multiple input files you have to use exactly one placeholder * which will then be replaced with the placeholder part from the media files
- Join Maximum is the upper limit of time between two subtitles. If the intervall is smaller that part will be cut out
- Pre Padding is the amount of time that is added before each subtitle when cuts are made
- Post Padding is the amount of time that is added after each subtitle when cuts are made
- Album Name/Art setthose properties of the generated output files (optional, only works with mp3 currently)
- Hit convert and wait for it to finish

## Todo:
- Sanitize subs from any non spoken content
- Proper checks when ffmpeg errors out
- Clean up this readme when I'm not tired
