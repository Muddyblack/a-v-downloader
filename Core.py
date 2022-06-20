import sys
sys.path.insert(0,".\Modules")

from pytube import YouTube, Playlist

import subprocess, threading
import re, os, shutil
from threading import Thread
from subprocess import PIPE, Popen
from time import sleep



def main_downloader(audio_or_video):
    global url_string
    global playlist
    global destination
    global playlistsettings
    global audio_format
    global video_format

    # regex needed to watch if input is a weblink
    regex = re.compile(
            r'^(?:http|ftp)s?://' # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
            r'localhost|' #localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?' # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    def create_downloader_code(url_string, is_it_mixer = False):
        global playlist
        global destination
        global playlistsettings
        global audio_format
        global video_format

        if is_it_mixer == False:
            playlist == "--no-playlist"
            playlistsettings = ""

        print("set download code")

        
        filename = "%(title)s.%(ext)s"
    
        try:
            yt = YouTube(url_string)

            #artist = yt.metadata[0]['Artist']
            title = yt.metadata[0]['Song']

            filename = f"{title}.{audio_format}" #{artist} •
            
        except:
            pass

        if audio_or_video == "a":
            #add thumbnail where possible
            if audio_format == "mp3" or audio_format == "m4a" or audio_format == "opus" or audio_format == "flac":
                audio_format = audio_format + " --embed-thumbnail"
            #codepiece
            return f'yt-dlp -x {playlist} {playlistsettings} --audio-quality 192 --audio-format {audio_format} --add-metadata -o "{destination}{filename}" {url_string}'
        elif audio_or_video == "v":
            #yt-dlp can't recognize webm as format it is just standard so needed to differ
            
            if video_format != "webm":
                v_format = f"--format {video_format}"
            return f'yt-dlp -f bestvideo+bestaudio {playlist} {playlistsettings} {v_format} --add-metadata  -o "{destination}%(title)s.f%(format_id)s.%(ext)s" {url_string}' 
                                                #{playlist} {playlistsettings}

    def main():
        global url_string
        global playlist
        global destination
        global playlistsettings
        global audio_format
        global video_format

        wrong_input = "try again bad input"

        url_string = str(input(" >> "))
        is_inputurl = re.match(regex, url_string) is not None

        if is_inputurl == True:
            if playlist == "--yes-playlist":
                code_list = ""
                video_links = Playlist(url_string).video_urls
                playlistlength = len(video_links)
                if playlistlength < 1:
                    code_list = create_downloader_code(url_string, True)
                else:
                    if len(playlistsettings)!=0:
                        playlist_indexes = []
                        placeholder = playlistsettings.replace("playlist-items ", "").split(",")
                        for index in placeholder:
                            if len(index)>1:
                                from_to = index.split("-")

                                start_add = int(min(from_to))
                                end_add = int(max(from_to))
                                j = start_add
                                while j <= end_add:
                                    playlist_indexes.append(video_links[j])
                                    j += 1
                            else:
                                playlist_indexes.append(video_links[int(index)])
                        
                        video_links = playlist_indexes
                        playlistsettings = ""

                    playlistlength = len(video_links)
                    print(playlistlength)
                    seperator = "; "
                    i = 0
                    while i < playlistlength:
                        if i == playlistlength - 1:
                            seperator = ""
                        
                        code_list += create_downloader_code(video_links[i]) + seperator
                        i += 1
                        
                    
                print(code_list)
                subprocess.call(code_list, creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.call(create_downloader_code(url_string), creationflags=subprocess.CREATE_NEW_CONSOLE)

        if url_string == "restart":
            starter()

        if url_string == "playlist":
            playlist = '--yes-playlist'
        elif url_string == "no-playlist":
            playlist = "--no-playlist"

        elif url_string == "playlist-spec":
            def special_match(strg, search=re.compile(r'[^0-9,-]').search):
                return not bool(search(strg))
            def playlist_spec():
                global playlistsettings

                print("Enter specific videos like: 1,2,7,10-13")
                playlistsettingsinput = str(input("  >>"))
                if special_match(playlistsettingsinput) == False or playlistsettingsinput[-1] in (",","-") or playlistsettingsinput[0] in (",","-"):
                    print(wrong_input)
                    playlist_spec()
                else:
                    playlistsettings = "playlist-items " + playlistsettingsinput

            playlist_spec()

        elif url_string == "set-Aformat":
            def set_audio_format():
                global audio_format

                audio_format = input(" Use: mp3, wav, m4a, opus, aac, flac \n  >>")

                chars_to_check = ["mp3", "wav", "m4a", "opus", "aac", "flac"]
                
                for char in chars_to_check:
                    if char == audio_format:
                        print("Audioformat is now: " + char)
                        clean_input = True
                        break
                    else:
                        clean_input = False
                

                if clean_input == False:
                    print(" bad format")
                    set_audio_format()
            set_audio_format()

        elif url_string == "set-Vformat":
            global video_format

            def set_video_format():
                video_format = input(" Use: mp4, webm, 3gp \n  >>")

                chars_to_check = ["mp4", "webm", "3gp"]
                
                for char in chars_to_check:
                    if char == video_format:
                        print("Videoformat is now: " + char)
                        clean_input = True
                        break
                    else:
                        clean_input = False

                if clean_input == False:
                    print(" bad format")
                    set_video_format()
            set_video_format()

        elif url_string == "stop":
            exit()
        elif url_string == "help":
            print("Enter: 'stop' --> exit function.\n"+
            "Enter a YT-URL --> download YT-Video \n"+
            "Enter: 'playlist' if the link is a Playlist and 'no-playlist' to switch back\n"+
            "Enter: 'playlist-spec' --> settings to download specific videos of Playlist\n"+
            "Enter: 'restart' --> restarts script from complete beginning")
            if audio_or_video == "a":
                print("Enter: 'set-Aformat' --> you can use: mp3, wav, m4a, opus, aac, flac")
            elif audio_or_video == "v":
                print("Enter: 'set-Vformat' --> you can use: mp4, webm, 3gp")
        else:
            print("This is not a valid Input")
            main()
        main()
        
    #declare
    playlist = "--no-playlist"
    playlistsettings = ""
    audio_format = "mp3"
    video_format = "mp4"
    #declare END
    #Declare User-preferences
    destination = str(input('Enter relative path or enter: "yes" to enter a full path \n >> ') or "Output")+"/"
    if os.path.isabs(destination) == False:
        destination = "./"+destination
    #Declare User-preferences END
    print(destination)
    print("Enter: 'help' for all Functions.")
    main()

def starter():
    audio_or_video = str(input("Enter: 'a' for audio or 'v' for video download \n >>"))
    if audio_or_video != 'a' and audio_or_video != 'v':
        print("bad input")
        starter()
    else:
        main_downloader(audio_or_video)   

os.system('color 9')
starter()