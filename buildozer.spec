[app]
title = YTMP3
package.name = ytmp3
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,yt-dlp,ffmpeg-python
orientation = portrait
fullscreen = 0
android.arch = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
require_ios = false
allow_backup = false
android_api = 30
target.android.api = 30
ndk_dir = 
ndk_version = r25b

[buildozer:android]
android.api = 30
android.ndk = 25b
android.ndk_api = 30
android.use_gradle = true
android.archs = arm64-v8a,armeabi-v7a

[logcat]
logcat_filters = *:S Python:D