import subprocess, sys, re, os, threading, shutil
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

    def downloader():
        global url_string
        global playlist
        global destination
        global playlistsettings
        global audio_format
        global video_format

        print("start downloader")

        #get the name of the file to change location later
        def get_file_name():
            global filename 

            filename = str(subprocess.run("youtube-dl --no-playlist --get-title "+ url_string, capture_output=True).stdout)
            filename = str(filename).replace("b'", "").replace("\\n'", "")
        
        d = threading.Thread(name='daemon', target=get_file_name)
        d.daemon = True
        d.start()
        
        #start download sequence
        if audio_or_video == "a":
            #add thumbnail where possible
            if audio_format == "mp3" or audio_format == "m4a" or audio_format == "opus" or audio_format == "flac":
                audio_format = audio_format + " --embed-thumbnail"
            #download 
            subprocess.call(f"yt-dlp -x {playlist} {playlistsettings} --audio-quality 192 --audio-format {audio_format} --add-metadata --output ./Output/%(title)s.%(ext)s {url_string}", creationflags=subprocess.CREATE_NEW_CONSOLE)
            #reset audio_format for a later filemove check
            audio_format = audio_format.replace(" --embed-thumbnail", "")
        elif audio_or_video == "v":
            #yt-dlp can't recognize webm as format it is just standard so needed to differ
            if video_format == "webm":
                subprocess.call(f"yt-dlp -f bestvideo+bestaudio {playlist} {playlistsettings}  --add-metadata  -o ./Output/%(title)s.f%(format_id)s.%(ext)s {url_string}", creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.call(f"yt-dlp -f bestvideo+bestaudio {playlist} {playlistsettings}  --add-metadata  --format {video_format} -o ./Output/%(title)s.f%(format_id)s.%(ext)s {url_string}", creationflags=subprocess.CREATE_NEW_CONSOLE)

        #required because yt-dlp doesn't accept space key in destinationpath
        if audio_or_video == "a":
            filepath = f'./Output/{filename}.{audio_format}'
        elif audio_or_video == "v":
            filepath = f'./Output/{filename}.{video_format}'

        #check if destination already exists/create it and move file to destination
        if os.path.isdir(destination) == True:
            shutil.move(filepath, destination+str(filepath[9:]))
        else:
            os.mkdir(destination)
            shutil.move(filepath, destination+str(filepath[9:]))

    def main():
        global url_string
        global playlist
        global destination
        global playlistsettings
        global audio_format
        global video_formata

        wrong_input = "try again bad input"

        url_string = str(input(" >> "))
        is_inputurl = re.match(regex, url_string) is not None

        if is_inputurl == True:
            thread = Thread(target=downloader)
            thread.start()
            sleep(1)

        if url_string == "restart":
            starter()

        if url_string == "playlist":
            playlist = '--yes-playlist'
        elif url_string == "no-playlist":
            playlist = "--no-playlist"

        elif url_string == "playlist-spec":
            playlist_spec = str(input("Enter: 'list' --> download from to of Playlist \nEnter: 'spec' --> download specific videos\n >> "))
            if playlist_spec == "list":
                def special_match(strg, search=re.compile(r'[^0-9]').search):
                    return not bool(search(strg))
                def playlist_list():
                    global playlistsettings

                    start = str(input("  startvideo >> "))
                    end = str(input("  endvideo >> "))
                    if special_match(start) == False or special_match(end) == False:
                        print(wrong_input)
                        playlist_list()
                    else:
                        playlistsettings = f"--playlist-start {start}--playlist-end NUMBER {end}"
            elif playlist_spec == "spec":
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
    destination = "./"+str(input('Enter relative path or enter: "yes" to enter a full path \n >> ') or "Output")+"/"
    if destination == "./yes/":
        destination = str(input("Enter full path >>"))+"/"
    #Declare User-preferences END
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