import sys
sys.path.insert(0,".\Modules")

##api
from pytube import YouTube, Playlist
from ytmusicapi import YTMusic
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

##urrlib
import urllib.request
import urllib.parse

##system
import subprocess
import re, os, shutil
from threading import Thread
from subprocess import PIPE, Popen

##UI
from tkinter import filedialog

##helper
def read_file(file_path):
    f = open(file_path, "r")

    txt_lines = f.readlines()
    txt_lines_length = len(txt_lines)
    r = 0 
    while r < txt_lines_length:
        txt_lines[r]= txt_lines[r].replace('\n','')
        r+=1

    f.close()
    return txt_lines

def stamp_to_seconds(timestr):
    seconds= 0
    for part in timestr.split(':'):
        seconds= seconds*60 + int(part, 10)
    return seconds

##funcs
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

    def create_downloader_code(url_string_list):
        global playlist
        global destination
        global playlistsettings
        global audio_format
        global video_format
        global code_txt
        

        code_txt = ""
        sperator = ";"
        if isinstance(url_string_list, str):
            url_string_list = [url_string_list]

        if playlist == "--no-playlist":
            playlistsettings = ""

        print("set download code")

        def thread_code_writer(url_string):
            global playlist
            global destination
            global playlistsettings
            global audio_format
            global video_format
            global code_txt

            try:
                yt = YouTube(url_string)

                #artist = yt.metadata[0]['Artist']
                title = yt.metadata[0]['Song']

                filename = f"{title}.{audio_format}" #{artist}       
            except:
                filename = "%(title)s.%(ext)s"

            if audio_or_video == "a":
                #add thumbnail where possible
                if audio_format == "mp3" or audio_format == "m4a" or audio_format == "opus" or audio_format == "flac":
                    audio_format = audio_format + " --embed-thumbnail"
                
                #codepiece
                code_txt += f'yt-dlp -x {playlist} {playlistsettings} --audio-quality 192 --audio-format {audio_format} --add-metadata -o "{destination}{filename}" {url_string}{sperator}'
            elif audio_or_video == "v":
                #yt-dlp can't recognize webm as format it is just standard so needed to differ
                
                if video_format != "webm":
                    v_format = f"--format {video_format}"

                code_txt += f'yt-dlp -f bestvideo+bestaudio {playlist} {playlistsettings} {v_format} --add-metadata  -o "{destination}%(title)s.f%(format_id)s.%(ext)s" {url_string}{sperator}' 

        threads = []
       
        for url_string in url_string_list:
            t = Thread(daemon=True, target= thread_code_writer, args=(url_string,))
            threads.append(t)

        for x in threads:
            x.start()
        
        for x in threads:
            x.join()

        return code_txt[:-1]

    def check_spotify_in_yt_music(song_list):
        global missed_songs
        
        url_list = []
        missed_songs = []
        limit = 10

        def thread_yt__music_search(i):
            song_title = song_list[i][0]
            song_interpret = song_list[i][1]
            song_duration = int(song_list[i][2])/1000 #convert milliseconds into seconds

            ytmusic = YTMusic(requests_session=False)
            search_results = ytmusic.search(f"{song_title} - {song_interpret}")
            
            url_cache = []
            indicator_list = []
            

            for j in range(len(search_results)): #limit
                try:
                    indexed_result = search_results[j]

                    y_title = indexed_result["title"]
                    y_duration = stamp_to_seconds(str(indexed_result["duration"])) 
                    link = f"https://music.youtube.com/watch?v={indexed_result['videoId']}"

                    song_title_list =  re.sub("[!,*)@#%(&$_?.^]",'', song_title).split()
                    y_title_list =   re.sub("[!,*)@#%(&$_?.^]",'', y_title).split()

                    try:
                        title_equality =   len(set(song_title_list) & set(y_title_list)) / len(song_title_list) 
                    except:
                        title_equality = 0

                    if (abs(y_duration-song_duration)<= song_duration*0.2) and title_equality > 0.3:  
                        url_cache.append(link)
                        indicator_list.append(abs(y_duration-song_duration) + title_equality*15)
                except:
                    pass

            if len(url_cache) < 1:
                #####add to search in YT itself
                query_string = urllib.parse.urlencode({"search_query" : song_title + " - " + song_interpret})
                html_content = urllib.request.urlopen("http://www.youtube.com/results?" + query_string)
                html = html_content.read().decode()
                search_results = re.findall(r'"url":\"\/watch\?v=(.{11})', html)

                for j in range(limit): #len(search_results)):
                    link = "http://www.youtube.com/watch?v=" + search_results[j]

                    yt = YouTube(link)
                    video_length = yt.length
                    video_title = yt.title

                    song_title_list =  re.sub("[!,*)@#%(&$_?.^]",'', song_title).split()
                    v_title_list =   re.sub("[!,*)@#%(&$_?.^]",'', video_title).split()
                    

                    try:
                        title_equality =   len(set(song_title_list) & set(v_title_list)) / len(song_title_list) 
                    except:
                        title_equality = 0

                    if (abs(video_length-song_duration)<= song_duration*0.2) and title_equality > 0.3:
                        
                        url_cache.append(link)
                        indicator_list.append(abs(video_length-song_duration) + title_equality*15)
            
                if len(url_cache) < 1:
                    missed_songs.append(song_title)
            
            if len(url_cache) >= 1:
                final_url = url_cache[indicator_list.index(min(indicator_list))] 
                url_list.append(final_url)


        threads = []
        for i in range(len(song_list)):
            t = Thread(daemon=True, target= thread_yt__music_search, args=(i,))
            threads.append(t)

        for x in threads:
            x.start()
        
        for x in threads:
            x.join()
        
        print(url_list)
        return url_list

    def main():
        global url_string
        global playlist
        global destination
        global playlistsettings
        global audio_format
        global video_format
        global missed_songs

        wrong_input = "try again bad input"

        #get input
        url_string = str(input(" >> "))
        is_inputurl = re.match(regex, url_string) is not None

        #check as boolean if link is a spotify link
        regexp = re.compile(r'^(spotify:|https:\/\/[a-z]+\.spotify\.com\/)')
        is_spoitfy_url = bool(regexp.search(url_string))
      
        if is_inputurl and is_spoitfy_url:

            auth_manager = SpotifyClientCredentials(client_id=CID, client_secret=SECRET)
            sp = spotipy.Spotify(auth_manager=auth_manager)

            song_list = []

            # is it list-url or track-url
            regexpl = re.compile(r'^(spotify:|https:\/\/[a-z]+\.spotify\.com\/playlist)')
            regexalb = re.compile(r'^(spotify:|https:\/\/[a-z]+\.spotify\.com\/album)')
            regexart = re.compile(r'^(spotify:|https:\/\/[a-z]+\.spotify\.com\/artist)')
            regextr = re.compile(r'^(spotify:|https:\/\/[a-z]+\.spotify\.com\/track)')

            def spotipy_get_track_infos(results, key_change = None):
                if key_change == None:
                    key = 'items'
                elif key_change == "artist":
                    key = 'tracks'
                    

                for track in results[key]:
                    song = []

                    song.append(track['name'] )
                    song.append(track['artists'][0]['name'])
                    song.append(str(track['duration_ms']))
                    song_list.append(song)

            if bool(regexpl.search(url_string)):
                results = sp.playlist(url_string)

                for track in results['tracks']['items']:
                    song = []

                    song.append(track['track']['name'] )
                    song.append(track['track']['artists'][0]['name'])
                    song.append(str(track['track']['duration_ms']))
                    song_list.append(song)

            elif bool(regexalb.search(url_string)):
                results = sp.album_tracks(url_string)
                spotipy_get_track_infos(results)

            elif bool(regexart.search(url_string)):
                results = sp.artist_top_tracks(url_string)
                spotipy_get_track_infos(results, "artist")
                
            elif bool(regextr.search(url_string)):
                song = []
                track_info = sp.track(url_string)
                #print(track_info)

                song.append(track_info['name'])
                song.append(track_info['artists'][0]['name'])
                song.append(str(track_info['duration_ms']))
                song_list.append(song)   
                
            print(song_list)
            
            yt_urls = check_spotify_in_yt_music(song_list)
            code_list = create_downloader_code(yt_urls)

            
            if len(missed_songs)>0:
                print(f"\n------------------------ \nError with these songs:\n{missed_songs}\n------------------------\n")  
        elif is_inputurl:

            if playlist == "--no-playlist":
                playlistlength = 1 
            else:
                try:
                    video_links = Playlist(url_string).video_urls
                    playlistlength = len(video_links)
                except:
                    playlistlength = 1
            

            if playlistlength <= 1:
                code_list = create_downloader_code(url_string)
            else:
                if len(playlistsettings)!=0:
                    playlist_indexes = []
                    placeholder = playlistsettings.replace("playlist-items ", "").split(",")
                    for index in placeholder:
                        if len(index)>1:
                            from_to = index.split("-")

                            start_add = int(min(from_to))
                            end_add = int(max(from_to))

                            for j in range(start_add, end_add):
                                playlist_indexes.append(video_links[j])
                        else:
                            playlist_indexes.append(video_links[int(index)])
                    
                    video_links = playlist_indexes
                    playlistsettings = ""
                code_list = create_downloader_code(video_links)

        if is_inputurl:
            def d():
                subprocess.call(code_list, creationflags=subprocess.CREATE_NEW_CONSOLE)
        
            d = Thread(daemon=True, target=d)
            d.start()

        ##options
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
        elif(is_inputurl == False):
            print("This is not a valid Input")
            main()

        main()
        
    #declare
    playlist = "--no-playlist"
    playlistsettings = ""
    audio_format = "mp3"
    video_format = "mp4"
    spotifyapiinfo = read_file("Spotify_Application.info")
    CID =str(spotifyapiinfo[0])
    SECRET = str(spotifyapiinfo[1])     
    #declare END

    #declare User-preferences
    destination = ""
    while(destination == "" or destination == "/"):
        destination = input('Enter relative or a full path or hit enter to choose via explorer \n >> ') or filedialog.askdirectory(initialdir = f"{os.getcwd()}", 
                                                                                                                                    title = "Select folder",)+"/"
    
    if os.path.isabs(destination) == False:
        destination = "./Output/"+destination+"/"
    #declare User-preferences END

    print(f"Destination: {destination}")
    print("Enter: 'help' for all Functions.")

    #loop
    main()

def starter():
    audio_or_video = str(input("Enter: 'a' for audio or 'v' for video download \n >>"))
    if audio_or_video != 'a' and audio_or_video != 'v':
        print("bad input")
        starter()
    else:
        main_downloader(audio_or_video)   

##go
os.system('color 9')
starter()