[app]
title = YTMP3
package.name = ytmp3
package.domain = com.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,yt-dlp
orientation = portrait
fullscreen = 0
android.arch = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
require_ios = false
allow_backup = false
android_api = 31
target.android.api = 31
ndk_dir = 
ndk_version = r25b

[buildozer:android]
android.api = 31
android.ndk = 25b
android.ndk_api = 31
android.use_gradle = true
android.archs = arm64-v8a,armeabi-v7a

[logcat]
logcat_filters = *:S Python:D