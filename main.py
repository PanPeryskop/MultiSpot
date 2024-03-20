import customtkinter as ctk
import webbrowser
from AnimatedGif import *
from customtkinter import CTkImage
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from PIL import Image
from io import BytesIO
import time
import configparser
import random
import threading
import os
import re
import ctypes

redirect_uri, client_id, client_secret = None, None, None
scope = None
auth_manager = None
sp = None


def end_all():
    app.quit()
    quit()


def my_profile():
    webbrowser.open('https://github.com/PanPeryskop')
    pass


def how_to_use():
    webbrowser.open('https://github.com/PanPeryskop/MultiSpot/wiki/How-to-Use')
    pass


def change_config(frame):
    destroy_frame(frame)
    if os.path.exists("config.sg"):
        os.remove("config.sg")
    get_config(False)
    setup_multispot()
    pass


def destroy_frame(frame):
    frame.destroy()
    pass


def save_config(client_id, client_secret, redirect_uri, config_frame, start):
    config['Spotify'] = {'client_id': client_id, 'client_secret': client_secret, 'redirect_uri': redirect_uri}
    with open(config_file, 'w') as configfile:
        config.write(configfile)

    destroy_frame(config_frame)

    load_config(start)

    app.quit()

    if not start:
        setup_multispot()
    pass


def restart(frame):
    destroy_frame(frame)
    setup_multispot()
    pass


def load_config(start):
    global client_id, client_secret, redirect_uri
    config.read(config_file)
    client_id = config.get('Spotify', 'client_id')
    client_secret = config.get('Spotify', 'client_secret')
    redirect_uri = config.get('Spotify', 'redirect_uri')
    if not start:
        global scope, auth_manager, sp
        scope = 'playlist-read-private user-modify-playback-state playlist-modify-public playlist-modify-private user-top-read'
        auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri,
                                    scope=scope)
        sp = spotipy.Spotify(auth_manager=auth_manager)


def do_random_activity(arg):

    playlist_id = '4MnsAykYyLNT98OylEr02Y'
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    track = random.choice(tracks)
    track_uri = track['track']['uri']
    sp.start_playback(uris=[track_uri])


def random_activity(frame):
    destroy_frame(frame)
    processing_frame(do_random_activity, None)
    finished_frame()
    to_destroy = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    restart(to_destroy)
    pass


def clear_playlist(playlist_id):
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    track_ids = [track['track']['id'] for track in tracks]
    sp.playlist_remove_all_occurrences_of_items(playlist_id, track_ids)


def process_url_to_shuffle(args):
    playlist_url, frame = args
    if playlist_url.startswith('https://open.spotify.com/playlist/'):
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
        playlist = sp.playlist(playlist_id)
        playlist_name = playlist['name']
        tracks_data = []
        results = sp.playlist_items(playlist_id)
        tracks_data.extend(results['items'])
        while results['next']:
            results = sp.next(results)
            tracks_data.extend(results['items'])

        tracks = list(set([track['track']['id'] for track in tracks_data if re.match('^[a-zA-Z0-9]*$', track['track']['id'])]))
        if playlist['owner']['id'] == sp.me()['id']:
            new_playlist = sp.user_playlist_create(user=sp.me()['id'], name=playlist_name)
            new_playlist_id = new_playlist['id']
            for i in range(len(tracks)):
                sp.playlist_add_items(playlist_id=new_playlist_id, items=['spotify:track:' + tracks[i]])
            sp.current_user_unfollow_playlist(playlist_id)
        else:
            new_playlist = sp.user_playlist_create(user=sp.me()['id'], name=playlist_name+' (Shuffled)')
            new_playlist_id = new_playlist['id']
            for i in range(len(tracks)):
                sp.playlist_add_items(playlist_id=new_playlist_id, items=['spotify:track:' + tracks[i]])


def go_to_playlist_shuffler(playlist_url, frame):
    destroy_frame(frame)
    processing_frame(process_url_to_shuffle, [playlist_url, frame])
    to_destroy = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    finished_frame()
    restart(to_destroy)
    pass


def playlist_shuffler(frame):
    destroy_frame(frame)
    queue_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000', fg_color='#000000', bg_color='#000000')
    queue_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(queue_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)
    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)
    buttons_text = ["My Profile", "How to Use", "Change Config", "Return"]
    buttons_x = [355, 509, 677, 844]
    buttons_command = [my_profile, how_to_use, lambda: change_config, lambda: restart(queue_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0,
                               text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    track_to_playlist_label = ctk.CTkLabel(queue_frame, text="Enter url to playlist", font=("Roboto", 44, "bold"),
                                           text_color="#FFFFFF", width=700, height=157)
    track_to_playlist_label.place(x=150, y=209)

    user_input = ctk.CTkEntry(queue_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20), width=400, height=50)
    user_input.place(x=300, y=400)
    submit_button = ctk.CTkButton(queue_frame, text="Submit", command=lambda: go_to_playlist_shuffler(user_input.get(), queue_frame), width=227, height=64, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20, "bold"))
    submit_button.place(x=386, y=750)
    pass


def update_page(page):
    pass


def prev_page():
    pass


def next_page():
    pass


def prepare_display():
    pass


def select_source(frame):
    pass


def process_input_queue_setter(u_input, frame):
    if u_input.isdigit():
        num = int(u_input)
        if 0 < num < 11:
            # destroy_frame(frame)
            # processing_frame(magic_playlist, int(input))
            # to_destroy = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
            # finished_frame()
            restart(frame)
        else:
            error_label = ctk.CTkLabel(frame, text="Please enter a number between 1 and 10.", text_color="red", font=("Roboto", 40, "bold"))
            error_label.pack()
            app.after(2500, error_label.destroy)
            return
    else:
        return


def queue_setter(frame):
    destroy_frame(frame)
    queue_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000', fg_color='#000000', bg_color='#000000')
    queue_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(queue_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)
    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)
    buttons_text = ["My Profile", "How to Use", "Change Config", "Return"]
    buttons_x = [355, 509, 677, 844]
    buttons_command = [my_profile, how_to_use, lambda: change_config, lambda: restart(queue_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0,
                               text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    track_to_playlist_label = ctk.CTkLabel(queue_frame, text="How many playlists do you want to\nadd to queue?", font=("Roboto", 44, "bold"),
                                           text_color="#FFFFFF", width=700, height=157)
    track_to_playlist_label.place(x=150, y=209)

    user_input = ctk.CTkEntry(queue_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20), width=400, height=50)
    user_input.place(x=300, y=400)
    user_input.bind('<KeyRelease>', lambda event: update_slider(event, slider))
    user_input.insert(0, 5)
    slider = ctk.CTkSlider(queue_frame, from_=1, to=10, number_of_steps=9, command=lambda value: slider_activity(value, queue_frame, user_input), width=400, height=40, fg_color='#2e2e2e', bg_color='#000000', button_hover_color='#FFFFFF', button_color='#FFFFFF', progress_color='light grey')
    slider.place(relx=0.5, rely=0.6, anchor='center')
    submit_button = ctk.CTkButton(queue_frame, text="Submit", command=lambda: process_input_queue_setter(user_input.get(), queue_frame), width=227, height=64, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20, "bold"))
    submit_button.place(x=386, y=750)
    pass


def get_top_tracks(count):
    top_tracks = sp.current_user_top_tracks(limit=count, time_range='medium_term')
    top_tracks_ids = []
    for track in top_tracks['items']:
        top_tracks_ids.append(track['id'])
    random.shuffle(top_tracks_ids)
    return top_tracks_ids


def get_recommended(playlist_count):
    top_tracks = get_top_tracks(20)
    top_tracks = random.sample(top_tracks, 5)
    recommended_tracks = sp.recommendations(seed_tracks=top_tracks, limit=playlist_count)
    return recommended_tracks


def magic_playlist(args):
    name, playlist_count = args
    playlist = sp.user_playlist_create(sp.me()['id'], name)
    playlist_id = playlist['id']
    tracks = get_recommended(playlist_count)
    track_ids = []
    for track in tracks['tracks']:
        track_ids.append(track['id'])
    sp.playlist_add_items(playlist_id, track_ids)
    pass


def magic_playlist_creator(name, playlist_count, frame):
    destroy_frame(frame)
    processing_frame(magic_playlist, [name, playlist_count])
    to_destroy = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    finished_frame()
    restart(to_destroy)
    pass


def get_name(playlist_count):
    get_name_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000', fg_color='#000000', bg_color='#000000')
    get_name_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(get_name_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)
    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)
    buttons_text = ["My Profile", "How to Use", "Change Config", "Return"]
    buttons_x = [355, 509, 677, 844]
    buttons_command = [my_profile, how_to_use, lambda: change_config, lambda: restart(get_name_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0,
                               text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    track_to_playlist_label = ctk.CTkLabel(get_name_frame, text="Enter playlist name", font=("Roboto", 44, "bold"),
                                           text_color="#FFFFFF", width=700, height=157)
    track_to_playlist_label.place(x=150, y=209)

    user_input = ctk.CTkEntry(get_name_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20), width=400, height=50)
    user_input.place(x=300, y=400)
    user_input.insert(0, "Playlist name")

    submit_button = ctk.CTkButton(get_name_frame, text="Submit", command=lambda: magic_playlist_creator(user_input.get(), playlist_count, get_name_frame), width=227, height=64, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20, "bold"))
    submit_button.place(x=386, y=750)


def process_input_magic(input, frame):
    playlist_count = 0
    if input.isdigit() and int(input) > 0:
        playlist_count = int(input)
        destroy_frame(frame)
        get_name(playlist_count)
    elif input > 50:
        error_label = ctk.CTkLabel(app, text="Please enter a number between 1 and 50.")
        error_label.pack()
        app.after(5000, error_label.destroy)
    else:
        error_label = ctk.CTkLabel(app, text="Please enter a number.")
        error_label.pack()
        app.after(5000, error_label.destroy)


def magic_recommender(frame):
    destroy_frame(frame)
    magic_recommender_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000', fg_color='#000000', bg_color='#000000')
    magic_recommender_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(magic_recommender_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)
    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)
    buttons_text = ["My Profile", "How to Use", "Change Config", "Return"]
    buttons_x = [355, 509, 677, 844]
    buttons_command = [my_profile, how_to_use, lambda: change_config, lambda: restart(magic_recommender_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0,
                               text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    track_to_playlist_label = ctk.CTkLabel(magic_recommender_frame, text="How long do you want the playlist\nto be?", font=("Roboto", 44, "bold"),
                                           text_color="#FFFFFF", width=700, height=157)
    track_to_playlist_label.place(x=150, y=209)

    user_input = ctk.CTkEntry(magic_recommender_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20), width=400, height=50)
    user_input.place(x=300, y=400)
    user_input.bind('<KeyRelease>', lambda event: update_slider(event, slider))
    user_input.insert(0, 25)
    slider = ctk.CTkSlider(magic_recommender_frame, from_=1, to=50, number_of_steps=49, command=lambda value: slider_activity(value, magic_recommender_frame, user_input), width=400, height=40, fg_color='#2e2e2e', bg_color='#000000', button_hover_color='#FFFFFF', button_color='#FFFFFF', progress_color='light grey')
    slider.place(relx=0.5, rely=0.6, anchor='center')
    submit_button = ctk.CTkButton(magic_recommender_frame, text="Submit", command=lambda: process_input_magic(user_input.get(), magic_recommender_frame), width=227, height=64, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20, "bold"))
    submit_button.place(x=386, y=750)
    pass


def get_recommendations(track_id):
    results = sp.recommendations(seed_tracks=[track_id])
    tracks = []
    for track in results['tracks']:
        tracks.append(track['uri'])
    return tracks


def generate_playlist(track_id, times=5):
    all_tracks = []
    for i in range(times):
        recommendations = get_recommendations(track_id)
        for track in recommendations:
            if track not in all_tracks:
                all_tracks.append(track)
    return all_tracks


def create_playlist(args):
    track_url, playlist_name = args
    if track_url.startswith('https://open.spotify.com/track/'):
        number_of_characters = len(track_url)
        if number_of_characters == 73:
            track_id = track_url.split('/')[-1].split('?')[0]
        else:
            track_id = track_url.split('/')[-1]
        playlist = generate_playlist(track_id)
        playlist_spot = sp.user_playlist_create(sp.me()['id'], playlist_name, public=True)
        playlist_id = playlist_spot['id']
        track_ids = [track for track in playlist]
        sp.playlist_add_items(playlist_id, track_ids)


def add_track_to_playlist(track_url, playlist_name, frame):
    args = [track_url, playlist_name]
    destroy_frame(frame)
    processing_frame(create_playlist, args)
    to_destroy = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    finished_frame()
    restart(to_destroy)


def track_to_playlist(frame):
    destroy_frame(frame)
    track_to_playlist_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    track_to_playlist_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(track_to_playlist_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)
    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)
    buttons_text = ["My Profile", "How to Use", "Change Config", "Return"]
    buttons_x = [355, 509, 677, 844]
    buttons_command = [my_profile, how_to_use, lambda: change_config, lambda: restart(track_to_playlist_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0, text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    middle_frame = ctk.CTkFrame(track_to_playlist_frame, fg_color='#000000', bg_color='#000000', border_width=0, border_color='#000000', width=1000, height=888)
    middle_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    track_to_playlist_label = ctk.CTkLabel(middle_frame, text="Track to Playlist", font=("Roboto", 36, "bold"), text_color="#FFFFFF")
    track_to_playlist_label.place(x=350, y=50)

    track_url_label = ctk.CTkLabel(middle_frame, text="Enter the track url", font=("Roboto", 40), text_color="#FFFFFF")
    track_url_label.place(x=43, y=200)

    track_url_entry = ctk.CTkEntry(middle_frame, font=("Roboto", 24), width=417, height=75, border_width=0, border_color="#000000", fg_color="#FFFFFF", text_color="#000000")
    track_url_entry.place(x=520, y=190)
    track_url_entry.insert(0, "Track URL")

    playlist_name_label = ctk.CTkLabel(middle_frame, text="Enter the playlist name", font=("Roboto", 40), text_color="#FFFFFF")
    playlist_name_label.place(x=43, y=400)

    playlist_entry = ctk.CTkEntry(middle_frame, font=("Roboto", 24), width=417, height=75, border_width=0, border_color="#000000", fg_color="#FFFFFF", text_color="#000000")
    playlist_entry.place(x=520, y=390)
    playlist_entry.insert(0, "Playlist name")

    submit_button = ctk.CTkButton(middle_frame, text="Submit", font=("Roboto", 24), fg_color="#FFFFFF", bg_color="#000000", border_width=0, text_color="#000000", command=lambda: add_track_to_playlist(track_url_entry.get(), playlist_entry.get(), track_to_playlist_frame), width=227, height=64)
    submit_button.place(rely=0.8, relx=0.5, anchor=ctk.CENTER)
    pass


def add_random_track_to_queue():
    genres = ['pop', 'rap', 'rock', 'urbano latino', 'hip hop', 'trap latino', 'reggaeton', 'dance pop', 'pop rap',
              'modern rock', 'pov: indie', 'musica mexicana', 'latin pop', 'classic rock', 'filmi', 'permanent wave',
              'trap', 'alternative metal', 'k-pop', 'r&b', 'corrido', 'canadian pop', 'norteno', 'sierreno',
              'album rock', 'soft rock', 'pop dance', 'sad sierreno', 'edm', 'hard rock', 'contemporary country',
              'mellow gold', 'uk pop', 'melodic rap', 'modern bollywood', 'alternative rock', 'banda', 'post-grunge',
              'corridos tumbados', 'sertanejo universitario', 'nu metal', 'country', 'art pop', 'atl hip hop',
              'urban contemporary', 'sertanejo', 'southern hip hop', 'singer-songwriter', 'reggaeton colombiano',
              'arrocha', 'french hip hop', 'colombian pop', 'alt z', 'country road', 'mexican pop', 'canadian hip hop',
              'j-pop', 'indonesian pop', 'singer-songwriter pop', 'ranchera', 'new wave pop', 'indietronica',
              'german hip hop', 'pop urbaine', 'rock en espanol', 'latin alternative', 'gangster rap', 'soul',
              'k-pop boy group', 'latin arena pop', 'chicago rap', 'italian pop', 'heartland rock', 'k-pop girl group',
              'agronejo', 'modern country pop', 'electro house', 'latin hip hop', 'canadian contemporary r&b',
              'pop punk', 'neo mellow', 'pop rock', 'latin rock', 'punjabi pop', 'rap metal', 'trap argentino',
              'new romantic', 'new wave', 'uk dance', 'slap house', 'modern alternative rock', 'indie pop',
              'indie rock', 'house', 'conscious hip hop', 'modern country rock', 'east coast hip hop', 'folk rock',
              'metal', 'turkish pop', 'bedroom pop', 'desi pop', 'italian hip hop', 'hoerspiel', 'afrobeats',
              'adult standards', 'post-teen pop', 'neo soul', 'sped up', 'cloud rap', 'viral pop', 'talent show',
              'spanish pop', 'punk', 'alternative r&b', 'grupera', 'west coast rap', 'opm', 'boy band',
              'psychedelic rock', 'glam metal', 'stomp and holler', 'desi hip hop', 'ccm', 'rage rap', 'hip pop',
              'puerto rican pop', 'german pop', 'miami hip hop', 'argentine rock', 'sertanejo pop', 'tropical',
              'glam rock', 'funk carioca', 'nigerian pop', 'argentine hip hop', 'dark trap', 'latin viral pop',
              'piano rock', 'detroit hip hop', 'italian adult pop', 'country rock', 'underground hip hop',
              'mexican hip hop', 'progressive electro house', 'synthpop', 'metropopolis', 'garage rock', 'indie folk',
              'vocal jazz', 'classical', 'europop', 'progressive house', 'art rock', 'yacht rock', 'mpb', 'pagode',
              'tropical house', 'urbano espanol', 'chamber pop', 'rap francais', 'dance rock', 'j-rock',
              'polish hip hop', 'sleep', 'folk', 'anime', 'trap brasileiro', 'disco', 'pluggnb', 'british soul',
              'metalcore', 'australian pop', 'uk hip hop', 'christian music', 'gen z singer-songwriter', 'electropop',
              'big room', 'forro', 'swedish pop', 'classic oklahoma country', 'reggaeton flow', 'pop nacional',
              'british invasion', 'mexican rock', 'indie soul', 'contemporary r&b', 'folk-pop', 'white noise',
              'pagode novo', 'soundtrack', 'funk metal', 'grunge', 'french pop', 'emo rap', 'salsa', 'rain',
              'r&b francais', 'lgbtq+ hip hop', 'turkish rock', 'memphis hip hop', 'mariachi', 'brostep',
              'classic soul', 'funk mtg', 'trap triste', 'dirty south rap', 'melodic metalcore', 'blues rock',
              'alternative hip hop', 'melancholia', 'pop soul', 'brazilian gospel', 'outlaw country',
              'orchestral soundtrack', 'dutch house', 'turkish hip hop', 'queens hip hop', 'christian alternative rock',
              'mandopop', 'lounge', 'worship', 'dfw rap', 'electronica', 'pixel', 'trap italiana', 'pop reggaeton',
              'new orleans rap', 'otacore', 'rock-and-roll', 'funk', 'quiet storm', 'motown', 'japanese teen pop',
              'brazilian hip hop', 'gruperas inmortales', 'kleine hoerspiel', 'indie poptimism', 'dream pop',
              'rap conscient', 'neo-synthpop', 'funk rock', 'easy listening', 'bolero', 'g funk', 'barbadian pop',
              'progressive rock', 'eurodance', 'hardcore hip hop', 'bachata', 'australian dance', 'neon pop punk',
              'emo', 'trap boricua', 'brazilian rock', 'funk paulista', 'pop venezolano', 'cantautor', 'chanson',
              'drift phonk', 'florida rap', 'bedroom r&b', 'latin christian', 'movie tunes', 'indonesian pop rock',
              'russian hip hop', 'spanish hip hop', 'cali rap', 'dancehall', 'brooklyn drill', 'trap queen',
              'urbano chileno', 'color noise', 'children\'s music', 'world worship', 'urbano mexicano',
              'sheffield indie', 'classic texas country', 'escape room', 'modern indie pop', 'funk rj', 'plugg',
              'anime rock', 'merseybeat', 'reggae fusion', 'shoegaze', 'tamil hip hop', 'britpop', 'australian rock',
              'industrial metal', 'baroque pop', 'brooklyn indie', 'pop argentino', 'r&b en espanol', 'trance',
              'turkish trap', 'thai pop', 'lilith', 'indian instrumental', 'downtempo', 'southern rock', 'sophisti-pop',
              'punjabi hip hop', 'polish trap', 'socal pop punk', 'candy pop', 'tamil pop', 'rockabilly', 'girl group',
              'uk contemporary r&b', 'atl trap', 'old school thrash', 'classic bollywood', 'compositional ambient',
              'gym phonk', 'north carolina hip hop', 'dark r&b', 'country dawn', 'symphonic rock', 'tennessee hip hop',
              'instrumental lullaby', 'pittsburgh rap', 'thrash metal', 'afropop', 'screamo', 'canadian rock',
              'kindermusik', 'melodic drill', 'nyc rap', 'modern blues rock', 'rock nacional brasileiro', 'philly rap',
              'afrofuturism', 'healing hz', 'cumbia pop', 'rap latina', 'reggae', 'madchester', 'spanish pop rock',
              'k-rap', 'dutch hip hop', 'trip hop', 'la indie', 'alternative dance', 'v-pop', 'rap rock',
              'funk consciente', 'indie anthem-folk', 'musica chihuahuense', 'chill house', 'australian hip hop',
              'azontobeats', 'new americana', 'tejano', 'korean ost', 'nova mpb', 'dutch edm', 'j-division',
              'sertanejo tradicional', 'acoustic pop', 'aesthetic rap', 'pop flamenco', 'cancion melodica', 'sigilkore',
              'rap conciencia', 'neo-psychedelic', 'dutch pop', 'adoracao', 'ska argentino', 'irish rock',
              'classic italian pop', 'indie pop rap', 'pop r&b', 'groove metal', 'power metal', 'lo-fi study',
              'classic country pop', 'danish pop', 'jazz', 'industrial rock', 'hyperpop', 'axe', 'phonk brasileiro',
              'pixie', 'bossa nova', 'uk post-punk', 'lo-fi indie', 'cumbia sonidera', 'southern soul', 'roots reggae',
              'sad rap', 'german techno', 'lo-fi beats', 'sad lo-fi', 'pop emo', 'binaural', 'german metal',
              'cumbia villera', 'latin worship', 'german dance', 'drill', 'pop edm', 'arab pop', 'brazilian reggae',
              'broadway', 'roots rock', 'samba', 'tech house', 'filter house', 'video game music', 'neo-classical',
              'jazz pop', 'show tunes', 'rap canario', 'mollywood', 'sufi', 'swedish hip hop', 'turkish alt pop',
              'hollywood', 'spanish rock', 'nursery', 'irish singer-songwriter', 'electro latino', 'shimmer pop',
              'lullaby', 'korean r&b', 'baton rouge rap', 'skate punk', 'grime', 'country pop', 'german rock',
              'nigerian hip hop', 'russian pop', 'noise pop', 'speed metal', 'canadian trap', 'indonesian indie',
              'rap marseille', 'vallenato', 'kentucky hip hop', 'ohio hip hop', 'la pop', 'swedish trap pop',
              'salsa puertorriquena', 'environmental', 'musica para ninos', 'french indie pop', 'hindi hip hop',
              'tollywood', 'ambient pop', 'stutter house', 'cloud rap francais', 'jazz blues', 'background piano',
              'lagu jawa', 'florida drill', 'cuarteto', 'dreamo', 'turbo folk', 'pinoy hip hop', 'czsk hip hop',
              'rap napoletano', 'chicago drill', 'japanese singer-songwriter', 'oxford indie', 'new rave',
              'french rock', 'swedish electropop', 'classic j-pop', 'polish pop', 'drill francais', 'new jack swing',
              'canadian singer-songwriter', 'drill espanol', 'gym hardstyle', 'indonesian singer-songwriter', 'dangdut',
              'swing', 'deep house', 'new french touch', 'industrial', 'uk alternative pop', 'coverchill',
              'hare krishna', 'complextro', 'kollywood', 'uk metalcore', 'baroque', 'el paso indie', 'flamenco urbano',
              'modern indie folk', 'country rap', 'early music', 'glitchcore', 'cantopop', 'bachata dominicana',
              'modern folk rock', 'egyptian pop', 'mexican indie', 'bubblegrunge', 'beatlesque', 'norwegian pop',
              'meditation', 'symphonic metal', 'arabesk', 'german drill', 'deep underground hip hop', 'electronic trap',
              'classic pakistani pop', 'electric blues', 'weirdcore', 'late romantic era', 'chill r&b', 'meme rap',
              'viral rap', 'japanese vgm', 'funk ostentacao', 'trap funk', 'arrochadeira', 'indie r&b',
              'pop rock brasileiro', 'previa', 'blues', 'covertronica', 'pagode baiano', 'indie rock italiano',
              'bhojpuri pop', 'neue deutsche harte', 'scandipop', 'classic canadian rock', 'meme', 'belgian edm',
              'indonesian jazz', 'contemporary vocal jazz', 'nu-cumbia', 'rap dominicano', 'anime score',
              'classic swedish pop', 'ambient lo-fi', 'swamp rock', 'vocaloid', 'classical era', 'pakistani hip hop',
              'australian psych', 'australian indie', 'instrumental hip hop', 'c-pop', 'old school atlanta hip hop',
              'indonesian rock', 'punk blues', 'taiwan pop', 'power pop', 'schlager', 'chillhop', 'russian trap',
              'nz pop', 'gujarati pop', 'memphis soul', 'musica popular colombiana', 'mambo chileno', 'christian rock',
              'classic indonesian rock', 'early romantic era', 'edmonton indie', 'sacramento indie', 'jam band',
              'drum and bass', 'melbourne bounce international', 'dutch rap pop', 'dangdut koplo', 'turkish folk',
              'golden age hip hop', 'javanese dangdut', 'post-punk argentina', 'alternative emo', 'greek trap',
              'post-punk', 'hamburg hip hop', 'soul blues', 'pop rap brasileiro', 'venezuelan hip hop', 'j-pixie',
              'cantautora mexicana', 'deep euro house', 'pop lgbtq+ brasileira', 'bass house',
              'nouvelle chanson francaise', 'crunk', 'electro', 'operatic pop', 'spanish indie pop', 'celtic rock',
              'vietnamese hip hop', 'p-pop', 'indie hip hop', 'stoner rock', 'pop house', 'bubblegum pop',
              'argentine indie', 'modern bhajan', 'new york drill', 'red dirt', 'irish pop', 'danish hip hop',
              'progressive metal', 'canadian metal', 'malaysian pop', 'countrygaze', 'indie garage rock', 'etherpop',
              'ska', 'bebop', 'funk pop', 'chilean rock', 'chinese viral pop', 'turkce drill', 'australian electropop',
              'musica de fondo', 'philly indie', 'hip house', 'post-romantic era', 'swedish gangsta rap',
              'dancefloor dnb', 'comic', 'scenecore', 'piano cover', 'rumba', 'electra', 'korean pop', 'reggae rock',
              'dance-punk', 'chill pop', 'german alternative rap', 'canadian indie', 'preschool children\'s music',
              'moombahton', 'tagalog rap', 'background music', 'funk bh', 'torch song', 'indie surf',
              'italian underground hip hop', 'pop romantico', 'dutch rock', 'rome indie', 'uk drill', 'protopunk',
              'shush', 'smooth jazz', 'j-poprock', 'old school hip hop', 'ectofolk', 'small room',
              'turkish singer-songwriter', 'indonesian r&b', 'kentucky roots', 'turkish alternative rock',
              'bedroom soul', 'cartoon', 'modern salsa', 'writing', 'background jazz', 'lo-fi jazzhop',
              'musica infantil', 'romanian pop', 'gauze pop', 'chillwave', 'deep ccm', 'norteno-sax',
              'alternative pop rock', 'finnish pop', 'trova', 'desi trap', 'dembow', 'cumbia', 'speedrun', 'world',
              'norwegian indie', 'perreo', 'reggaeton chileno', 'aussietronica', 'classic schlager', 'melbourne bounce',
              'rock cristiano', 'finnish hip hop', 'french indietronica', 'experimental pop', 'belgian hip hop',
              'classic opm', 'jazz funk', 'tecnobanda', 'japanese soundtrack', 'modern dream pop', 'pinoy r&b',
              'czech hip hop', 'indie triste', 'south carolina hip hop', 'trap mexicano', 'albanian hip hop',
              'boom bap espanol', 'chutney', 'laiko', 'sunshine pop', 'birmingham metal', 'german soundtrack',
              'disco house', 'fvnky rimex', 'acid rock', 'instrumental worship', 'japanese alternative rock',
              'scottish rock', 'corridos alternativos', 'nashville sound', 'modern alternative pop', 'rap df',
              'velha guarda', 'rap politico', 'post-hardcore', 'cumbia 420', 'british singer-songwriter',
              'bossa nova cover', 'social media pop', 'brazilian edm', 'scorecore', 'redneck', 'german baroque',
              'detroit trap', 'texas country', 'greek pop', 'british soundtrack', 'swedish metal', 'israeli pop',
              'slowcore', 'gaming edm', 'houston rap', 'german romanticism', 'nu jazz', 'panamanian pop',
              'new jersey rap', 'epicore', 'r&b brasileiro', 'slowed and reverb', 'czech pop', 'death metal',
              'arkansas country', 'chicano rap', 'high vibe', 'swedish trap', 'political hip hop', 'j-rap', 'uk funky',
              'albanian pop', 'mexican rock-and-roll', 'black americana', 'ghazal', 'modern southern rock',
              'indian singer-songwriter', 'japanese emo', 'indian indie', 'indonesian folk', 'deboxe',
              'french synthpop', 'russian dance', 'gothic metal', 'lo-fi cover', 'post-disco', 'greek hip hop',
              'rap genovese', 'trap chileno', 'reggaeton mexicano', 'cumbia chilena', 'italian indie pop',
              'kentucky indie', 'nyc pop', 'uk alternative hip hop', 'bronx drill', 'italo dance', 'salsa colombiana',
              'euphoric hardstyle', 'christian indie', 'canadian punk', 'polish viral pop', 'musica sonorense',
              'brill building pop', 'modern blues', 'rawstyle', 'afroswing', 'oakland hip hop', 'hard rock brasileiro',
              'grupero romantico', 'phonk', 'modern power pop', 'rap calme', 'rock urbano mexicano', 'british blues',
              'hardcore punk', 'anime lo-fi', 'hungarian pop', 'russian alt pop', 'rap belge', 'chicago indie',
              'lo-fi sleep', 'german cloud rap', 'cumbia peruana', 'indie game soundtrack', 'spanish new wave',
              'stomp and flutter', 'bossbeat', 'minimal techno', 'alternative country', 'gothic symphonic metal',
              'banda jalisciense', 'minnesota hip hop', 'latin talent show', 'frauenrap', 'early modern classical',
              'asmr', 'acoustic cover', 'afrofuturismo brasileiro', 'zolo', 'nu disco', 'indonesian pop punk',
              'afro r&b', 'hi-nrg', 'lo-fi chill', 'anadolu rock', 'duranguense', 'dubstep', 'trancecore',
              'dutch trance', 'christian hip hop', 'jazz rap', 'persian pop', 'rock gospel brasileiro',
              'pop electronico', 'finnish dance pop', 'supergroup', 'deep groove house', 'classic hardstyle',
              'modern hard rock', 'ocean', 'haryanvi pop', 'belgian pop', 'contemporary post-bop',
              'vietnamese melodic rap', 'hip hop tuga', 'gospel', 'shiver pop', 'jazz trumpet', 'american metalcore',
              'canadian electronic', 'water', 'barnmusik', 'northern soul', 'argentine telepop', 'deathcore',
              'pakistani pop', 'visual kei', 'stoner metal', 'ukrainian pop', 'doo-wop', 'colombian hip hop', 'traprun',
              'melodic dubstep', 'seattle hip hop', 'detroit rock', 'hindi indie', 'ambient worship', 'piseiro',
              'ska mexicano', 'big beat', 'canadian country', 'pinoy trap', 'vapor soul', 'haryanvi hip hop',
              'taiwan singer-songwriter', 'hardwave', 'australian indie folk', 'folklore argentino', 'partyschlager',
              'rock alternativo brasileiro', 'diva house', 'london rap', 'argentine reggae', 'future garage',
              'milan indie', 'intelligent dance music', 'drumless hip hop', 'nwobhm', 'charva', 'cool jazz',
              'canadian pop punk', 'indonesian alternative rock', 'indonesian folk pop', 'melodic death metal',
              'j-pop boy group', 'japanese electropop', 'australian surf rock', 'j-acoustic', 'progressive bluegrass',
              'corridos clasicos', 'rif', 'turkce slow sarkilar', 'canadian contemporary country', 'chicago bop',
              'middle earth', 'swedish synthpop', 'hawaiian hip hop', 'neoperreo', 'boston rock', 'classic mandopop',
              'soul jazz', 'rave funk', 'seattle indie', 'vocal house', 'russelater', 'cubaton', 'vapor twitch',
              'mainland chinese pop', 'trap soul', 'electronica argentina', 'tropicalia', 'manguebeat', 'rock uruguayo',
              'rap espanol', 'korean city pop', 'jazz saxophone', 'moroccan pop', 'impressionism', 'nu gaze',
              'chill drill', 'urdu hip hop', 'traditional blues', 'dinner jazz', 'funk 150 bpm', 'jamaican dancehall',
              'brighton indie', 'spacegrunge', 'musica bajacaliforniana', 'suomi rock', 'comic metal',
              'swedish idol pop', 'alte', 'japanese r&b', 'swedish alternative rock', 'psychedelic hip hop',
              'japanese chillhop', 'roots worship', 'experimental r&b', 'uplifting trance', 'new age', 'p funk',
              'scam rap', 'vallenato moderno', 'german indie', 'new age piano', 'float house', 'sky room',
              'swedish indie pop', 'rock drums', 'sound', 'levenslied', 'nueva cancion', 'russian rock', 'bhajan',
              'experimental hip hop', 'bolero mexicano', 'vancouver indie', 'arabic hip hop', 'new jersey indie',
              'nashville hip hop', 'ska punk', 'rap cristiano', 'english indie rock', 'naija worship', 'uk americana',
              'neo-singer-songwriter', 'modern j-rock', 'south african pop', 'lo-fi product', 'rap maroc',
              'ambient folk', 'bass trap', 'classic kollywood', 'jazz piano', 'rebel blues', 'toronto indie',
              'progressive trance', 'tierra caliente', 'muziek voor kinderen', 'dark pop', 'odia pop',
              'trap colombiano', 'indie quebecois', 'ambient', 'funk viral', 'medieval rock', 'teen pop',
              'folk brasileiro', 'lo-fi', 'manele', 'instrumental rock', 'trap baiano', 'british folk', 'rap baiano',
              'amapiano', 'funk mandelao', 'celtic', 'tekk', 'turkish alternative', 'german hard rock',
              'canadian latin', 'bases de freestyle', 'minneapolis sound', 'bubblegum dance', 'funk das antigas',
              'jazz cover', 'british indie rock', 'alabama rap', 'baltimore indie', 'women\'s music',
              'old school rap francais', 'antiviral pop', 'shamanic', 'basshall', 'czech rock', 'a cappella',
              'deep tropical house', 'nasheed', 'japanese soul', 'german trap', 'rkt', 'brazilian ccm', 'zhongguo feng',
              'crank wave', 'st louis rap', 'canzone d\'autore', 'trap catala', 'athens indie', 'australian house',
              'australian reggae fusion', 'philly soul', 'classic girl group', 'boom bap', 'r&b argentino', 'bow pop',
              'texas latin rap', 'synthwave', 'chill phonk', 'rap catala', 'pinoy rock', 'thai indie pop', 'austropop',
              'azonto', 'karadeniz turkuleri', 'russian drain', 'indie viet', 'nu-metalcore',
              'swedish singer-songwriter', 'hopebeat', 'gymcore', 'focus', 'wonky', 'swedish eurodance',
              'russian gangster rap', 'taiwan indie', 'synth funk', 'rap mineiro', 'rap algerien', 'ye ye',
              'singaporean pop', 'pinoy reggae', 'art punk', 'batidao romantico', 'indiecoustica', 'hypnagogic pop',
              'djent', 'variete francaise', 'classify', 'indonesian worship', 'greek drill', 'g-house',
              'turkish trap pop', 'lebanese pop', 'tamaulipas rap', 'polish alternative', 'swedish drill',
              'harlem renaissance', 'uk doom metal', 'hard bop', 'jazztronica', 'portuguese pop', 'classic soundtrack',
              'italian baroque', 'westcoast flow', 'rap chileno', 'rap geek', 'russian romanticism', 'j-pop girl group',
              'new school turkce rap', 'sleaze rock', 'brazilian jazz', 'electronic rock', 'chill abstract hip hop',
              'jazz guitar', 'rhythm game', 'proto-metal', 'prog metal', 'bassline', 'retro soul', 'jazz fusion',
              'latin afrobeat', 'classic colombian pop', 'iskelma', 'proto-hyperpop', 'japanese classical',
              'electro swing', 'rock nacional', 'rap cearense', 'rock gaucho', 'pop folk', 'spanish punk',
              'australian children\'s music', 'rock kapak', 'cyberpunk', 'eau claire indie',
              'scottish singer-songwriter', 'lo-fi vgm', 'chicha', 'french soundtrack', 'deep german hip hop',
              'classic city pop', 'salsa venezolana', 'hardcore techno', 'classic russian pop', 'ottawa rap',
              'turkish deep house', 'stomp pop', 'nintendocore', 'boom bap brasileiro', 'italo disco', 'ghanaian pop',
              'rap sardegna', 'lata', 'latin jazz', 'swedish power metal', 'anime rap', 'hk-pop', 'classic arab pop',
              'rap underground espanol', 'italian alternative', 'glitch hop', 'forro de favela', 'black metal',
              'filthstep', 'spanish metal', 'boston hip hop', 'romanian trap', 'cumbia santafesina', 'german r&b',
              'thai rock', 'anthem emo', 'merengue', 'rock brasiliense', 'banda sinaloense', 'french reggae',
              'trap carioca', 'hands up', 'german underground rap', 'atlanta indie', 'bitpop', 'newcastle nsw indie',
              'christian pop', 'bandung indie', 'chill breakcore', 'classic uk pop', 'flamenco', 'musica tlaxcalteca',
              'indie electropop', 'deep disco house', 'livetronica', 'chicago punk', 'aussie drill', 'mahraganat',
              'pet calming', 'classic russian rock', 'pop violin', 'nederpop', 'indie punk', 'reggaeton cristiano',
              'breakbeat', 'lo-fi rap', 'palm desert scene', 'german punk', 'afghan pop', 'folk punk',
              'argentine alternative rock', 'finnish metal', 'boston folk', 'nordic soundtrack', 'cumbia del sureste',
              'australian alternative rock', 'desi emo rap', 'violao', 'grave wave', 'abstract hip hop',
              'israeli mediterranean', 'german pop rock', 'lovers rock', 'barnsagor', 'fantasy metal', 'melodic thrash',
              'mississippi hip hop', 'german singer-songwriter', 'lo-fi emo', 'cumbia ranchera', 'future house',
              'anthem worship', 'australian metalcore', 'thai indie rock', 'dembow dominicano', 'icelandic indie',
              'dark synthpop', 'upstate ny rap', 'acoustic opm', 'australian country', 'venezuelan rock', 'scream rap',
              'morelos indie', 'bboy', 'noise rock', 'narco rap', 'sholawat', 'manchester hip hop', 'future bass',
              'organic electronic', 'pop nacional antigas', 'instrumental funk', 'k-indie', 'cumbia sonorense',
              'carnaval', 'digital hardcore', 'dutch indie', 'garage rock revival', 'indie liguria',
              'christmas instrumental', 'ghanaian hip hop', 'trap venezolano', 'traphall', 'belgian dance',
              'swedish melodeath', 'kirtan', 'qawwali', 'cancion infantil latinoamericana', 'polish classical',
              'reggae en espanol', 'detroit trap brasileiro', 'psychedelic soul', 'kizomba', 'nerdcore brasileiro',
              'canzone napoletana', 'neue neue deutsche welle', 'chinese r&b', 'thai hip hop', 'uptempo hardcore',
              'indian folk', 'modern reggae', 'happy hardcore', 'musica tradicional cubana', 'solo wave',
              'canadian soundtrack', 'classic sierreno', 'egyptian trap', 'classic praise', 'asian american hip hop',
              'swedish pop rap', 'turkish psych', 'veracruz indie', 'icelandic rock', 'finnish power metal',
              'indonesian reggae', 'bubble trance', 'acoustic guitar cover', 'pop virale italiano', 'rai',
              'danish rock', 'liquid funk', 'turkish jazz', 'tontipop', 'dansband', 'pianissimo', 'kayokyoku',
              'singaporean mandopop', 'bronx hip hop', 'jazz trio', 'japanese punk rock', 'dark clubbing',
              'electro-pop francais', 'egyptian hip hop', 'french shoegaze', 'drill italiana', 'aggressive phonk',
              'uk dnb', 'progressive metalcore', 'french romanticism', 'neo r&b', 'german house', 'electropowerpop',
              'japanese alternative pop', 'vegas indie', 'austindie', 'uk reggae', 'healing',
              'musica triste brasileira', 'samba-enredo', 'afro soul', 'jovem guarda', 'gujarati garba', 'nightcore',
              'saskatchewan indie', 'swedish death metal', 'hamburg electronic', 'canadian americana', 'umbanda',
              'souldies', 'anti-folk', 'riot grrrl', 'monterrey indie', 'mexican classic rock', 'new orleans jazz',
              'organic house', 'dixieland', 'cosmic american', 'rap feminino nacional', 'british alternative rock',
              'indonesian idol pop', 'jawaiian', 'mariachi cristiano', 'classic cantopop', 'romantico',
              'german power metal', 'classic disco polo', 'musique pour enfants', 'swedish tropical house', 'discofox',
              'chilena', 'j-metal', 'welsh rock', 'bulgarian pop', 'virginia hip hop', 'brega paraense', 'thai trap',
              'grungegaze', 'chicago hardcore', 'sludge metal', 'pacific islands pop', 'south african rock',
              'swedish indie rock', 'russian post-punk', 'smooth saxophone', 'ukrainian rock', 'chicago soul',
              'samba moderno', 'freestyle', 'american shoegaze', 'latin metal', 'german reggae', 'danish metal',
              'rock mineiro', 'sound team', 'canadian electropop', 'drone', 'regional mexicano femenil', 'indian edm',
              'j-idol', 'okinawan pop', 'sandalwood', 'scottish new wave', 'indie jazz', 'afrikaans', 'nz reggae',
              'israeli rock', 'oklahoma country', 'viking metal', 'christian trap', 'brega', 'buffalo hip hop',
              'kazakh pop', 'chill lounge', 'belly dance', 'minimal tech house', 'icelandic pop', 'classic indo pop',
              'oakland indie', 'surf punk', 'australian trap', 'brutal death metal', 'christian metal',
              'japanese vtuber', 'south african hip hop', 'rhode island rap', 'austrian pop', 'shaabi', 'celtic metal',
              'salsa peruana', 'tecnobrega', 'indian lo-fi', 'transpop', 'chillstep', 'japanese trap',
              'egyptian alternative', 'jersey club', 'experimental', 'channel pop', 'czech drill', 'texas metal',
              'polish rock', 'norwegian pop rap', 'indonesian lo-fi pop', 'samba de roda', 'sda a cappella',
              'harlem hip hop', 'danish pop rock', 'canadian ccm', 'russian emo rap', 'pinoy city pop', 'slayer',
              'memphis phonk', 'danspunk', 'polish alternative rap', 'uk pop punk', 'indie rock mexicano', 'bhangra',
              'russian punk', 'chill dream pop', 'quran', 'classic turkish pop', 'dark techno', 'gothenburg indie',
              'musica gaucha tradicionalista', 'boston indie', 'quebec indie', 'uk house', 'psychedelic trance',
              'neoclassical darkwave', 'oc rap', 'rave', 'vapor pop', 'cdo indie', 'classic venezuelan pop',
              'kazakh hip hop', 'guadalajara indie', 'german alternative rock', 'karadeniz pop', 'post-rock',
              'children\'s folk', 'polish drill', 'vaporwave', 'hungarian hip hop', 'alternative americana', 'hyphy',
              'easycore', 'new beat', 'indonesian hip hop', 'instrumental grime', 'punk urbano', 'reggae uruguayo',
              'khaliji', 'opera metal', 'scottish indie', 'ann arbor indie', 'study beats',
              'vintage italian soundtrack', 'folk rock italiano', 'mexican pop punk', 'midwest emo', 'cumbia paraguaya',
              'italian romanticism', 'russian drill', 'swedish hard rock', 'romanian house', 'viral trap',
              'liverpool indie', 'pinoy drill', 'bandinhas', 'experimental rock', 'northern irish indie', 'bluegrass',
              'jazz boom bap', 'early us punk', 'dub', 'spectra', 'nashville singer-songwriter', 'drill chileno',
              'classic danish pop', 'ambient guitar', 'piano blues', 'indian classical', 'horror punk',
              'pinoy alternative rap', 'yugoslav rock', 'turkish instrumental', 'folk metal', 'melodic metal',
              'classic french pop', 'russian electronic', 'new jersey hardcore', 'rune folk', 'french techno',
              'technical death metal', 'magyar trap', 'indonesian viral pop', 'rap underground argentino',
              'norwegian hip hop', 'dancehall queen', 'gospel r&b', 'polish viral rap', 'south african house',
              'icelandic classical', 'viral afropop', 'wave', 'german metalcore', 'pop minang',
              'progressive groove metal', 'deep turkish pop', 'pink noise', 'contemporary jazz', 'classic house',
              'rhythm and blues', 'classic israeli pop', 'glee club', 'american folk revival', 'kosovan pop',
              'rva drill', 'atmosphere', 'peruvian rock', 'zhenskiy rep', 'bc underground hip hop', 'pinoy indie',
              'uk dancehall', 'kurdish pop', 'gaming dubstep', 'danish electronic', 'spanish folk metal',
              'pinoy singer-songwriter', 'deep latin christian', 'north carolina roots', 'chill guitar', 'folktronica',
              'croatian pop', 'swedish soul', 'bergamo indie', 'lo-fi house', 'puerto rican rock', 'idol rock', 'idol',
              'kolsche karneval', 'rocksteady', 'acoustic blues', 'latinx alternative', 'frenchcore',
              'washington indie', 'soca', 'auckland indie', 'oyun havasi', 'central asian hip hop', 'antideutsche',
              'christian metalcore', 'chiptune', 'spanish modern rock', 'post-minimalism', 'rap uliczny',
              'nederlandse hardstyle', 'gothenburg metal', 'icelandic experimental', 'kabarett', 'latin classical',
              'ghanaian alternative', 'deep pop edm', 'jangle pop', 'calming instrumental', 'ethereal wave',
              'emo rap italiano', 'polish underground rap', 'musica aragonesa', 'turkish edm', 'balkan trap',
              'gothic rock', 'classic peruvian pop', 'italian opera', 'gospel antigas', 'celtic punk', 'irish folk',
              'dream plugg', 'classical drill', 'rock andaluz', 'focus beats', 'j-indie', 'rap boricua',
              'indonesian city pop', 'afrobeat', 'rap uruguayo', 'pop teen brasileiro', 'dark plugg', 'idol kayo',
              'kiwi rock', 'maga rap', 'pop chileno', 'chinese indie', 'brain waves', 'argentine heavy metal',
              'chinese singer-songwriter', 'arab electronic', 'chihuahua indie', 'progressive post-hardcore',
              'microhouse', 'portland indie', 'comedy rap', 'samba-jazz', 'classic garage rock', 'game mood',
              'portland hip hop', 'ukrainian viral pop', 'belgian rock', 'russian grime', 'chilean indie',
              'french opera', 'anime phonk', 'glitchbreak', 'west bengali pop', 'rock catala', 'neue deutsche welle',
              'fourth world', 'native american traditional', 'music box', 'bgm', 'samba paulista', 'viking folk',
              'neomelodici', 'comedy', 'chicago house', 'tropical alternativo', 'vietnamese trap', 'musica angolana',
              'samba-rock', 'brega romantico', 'korean instrumental', 'halloween', 'trap pesado', 'theme',
              'persian hip hop', 'rap underground mexicano', 'narodna muzika', 'swedish indie folk', 'trap dominicano',
              'contemporary classical', 'southern americana', 'fotbollslatar', 'texas blues', 'huzunlu sarkilar',
              'malayalam pop', 'electrofox', 'partido alto', 'rap nacional antigo', 'italian pop rock', 'murcia indie',
              'german trance', 'reggae tuga', 'concepcion indie', 'canadian folk', 'pop quebecois', 'uk melodic rap',
              'piano worship', 'new jersey punk', 'instrumental post-rock', 'nordic house',
              'australian alternative pop', 'dutch metal', 'volkspop', 'kavkaz', 'polish indie', 'no beat',
              'japanese new wave', 'cologne indie', 'new jersey underground rap', 'reggae do maranhao',
              'french tech house', 'minimal melodic techno', 'japanese pop punk', 'lagu timur', 'slc indie', 'mizrahi',
              'musica costena', 'entehno', 'lustrum', 'balkan hip hop', 'hip hop quebecois', 'cowboy western',
              'uk experimental electronic', 'malaysian mandopop', 'welsh metal', 'reggae cristao', 'indonesian emo',
              'metallic hardcore', 'belgian indie', 'rochester mn indie', 'liedermacher', 'victoria bc indie',
              'japanese viral pop', 'bay area indie', 'trap peruano', 'ska chileno', 'marathi pop', 'trap antillais',
              'laboratorio', 'chillsynth', 'minimalism', 'chalga', 'dutch cabaret', 'brega funk', 'chicago blues',
              'hungarian rock', 'trap tuga', 'barnemusikk', 'birmingham grime', 'parody', 'nuevo folklore mexicano',
              'rap tunisien', 'future rock', 'jamaican hip hop', 'mantra', 'classic iskelma', 'new weird america',
              'colombian rock', 'brazilian punk', 'big band', 'japanese old school hip hop', 'kermis', 'dong-yo',
              'diy emo', 'plug brasileiro', 'uk garage', 'italian soundtrack', 'australian indigenous music',
              'deathgrind', 'neo classical metal', 'taiwan hip hop', 'neoclassicism', 'ambeat', 'peruvian hip hop',
              'south african gospel', 'swedish country', 'symphonic deathcore', 'lagu melayu', 'thai folk rock',
              'shanty', 'scandinavian r&b', 'kwaito', 'australian indie rock', 'east coast reggae', 'emoplugg',
              'finnish trap', 'indonesian punk', 'rock baiano', 'brisbane indie', 'greek underground rap',
              'musica tamaulipeca', 'british children\'s music', 'progressive deathcore', 'arab alternative',
              'melodic techno', 'pinoy pop punk', 'swancore', 'gregorian dance', 'assamese pop', 'future funk',
              'electro jazz', 'grime brasileiro', 'guaracha', 'romanian rap', 'czsk emo rap', 'wrestling',
              'deep comedy', 'uk contemporary jazz', 'latin viral rap', 'strut', 'bergen indie', 'tagalog worship',
              'country gospel', 'dark cabaret', 'folclore salteno', 'progressive psytrance', 'dark wave', 'ska revival',
              'corridos belicos', 'new comedy', 'russian edm', 'ecuadorian pop', 'roda de samba', 'fado',
              'post-screamo', 'vintage french electronic', 'carnaval cadiz', 'pastoral', 'acoustic rock',
              'rock independant francais', 'texas pop punk', 'alternative roots rock', 'japanese post-hardcore',
              'nova musica pernambucana', 'slovak hip hop', 'musica sinaloense', 'comedy rock', 'colombian indie',
              'volksmusik', 'belo horizonte indie', 'ostrock', 'israeli hip hop', 'vbs', 'xtra raw',
              'musica per bambini', 'louvor', 'french jazz', 'hard bass', 'world devotional', 'industrial hip hop',
              'russian hyperpop', 'japanese metalcore', 'german oi', 'nepali pop', 'sinhala pop', 'darksynth',
              'korean indie rock', 'gregorian chant', 'mambo', 'deep talent show', 'miami bass',
              'vietnamese singer-songwriter', 'classic thai pop', 'argentine punk', 'samba reggae',
              'turkish soundtrack', 'musica andina', 'chinese idol pop', 'kansas city hip hop', 'steampunk',
              'experimental ambient', 'deathgrass', 'drain', 'russian viral rap', 'j-ambient', 'banjo',
              'cancion infantil mexicana', 'solfeggio product', 'slamming deathcore', 'classic polish pop',
              'turkce kadin rap', 'norwegian rock', 'jungle', 'ecm-style jazz', 'abstract beats', 'cello',
              'ukrainian phonk', 'saxophone house', 'south african trap', 'nottingham hip hop', 'reggae cover',
              'old school bassline', 'polish alternative rock', 'rock quebecois', 'indonesian ska', 'australian r&b',
              'emo mexicano', 'islamic recitation', 'english baroque', 'uk tech house', 'australian post-hardcore',
              'synthesizer', 'deep new americana', 'russian underground rap', 'dark rock', 'dark post-punk',
              'old school dancehall', 'doom metal', 'musica poblana', 'italian tenor', 'canadian classical',
              'classical tenor', 'swedish americana', 'swedish melodic rock', 'dangdut remix', 'crossover thrash',
              'russian rave', 'musica potosina', 'sacramento hip hop', 'german indie folk', 'north east england indie',
              'punk rock mexicano', 'psicodelia brasileira', 'josei rap', 'japanese instrumental', 'bakersfield sound',
              'korean old school hip hop', 'korean talent show', 'chinese hip hop', 'tex-mex', 'anime cv', 'city pop',
              'deutschrock', 'drill brasileiro', 'kawaii metal', 'canadian metalcore', 'groove gospel', 'jewish pop',
              'orgcore', 'classic belgian pop', 'brazilian metal', 'ballet class', 'musica catalana', 'kindie rock',
              'musica neoleonesa', 'indian fusion', 'carnatic', 'popwave', 'nottingham indie', 'psychedelic pop',
              'battle rap', 'classic j-rock', 'indonesian post-hardcore', 'nightrun', 'albuquerque indie',
              'irish country', 'portuguese rock', 'roots americana', 'brazilian indie', 'glam punk', 'brazilian emo',
              'brit funk', 'alabama indie', 'western swing', 'cumbia lagunera', 'malaysian indie', 'post-metal',
              'french metal', 'classic norwegian pop', 'australian singer-songwriter', '8d', 'blackened deathcore',
              'tololoche', 'classic persian pop', 'flamenco fusion', 'double drumming', 'brazilian soul',
              'west coast reggae', 'k-pop ballad', 'manila sound', 'canadian children\'s music', 'jazz quartet',
              'afro house', 'singaporean singer-songwriter', 'sertanejo gospel', 'traditional country', 'dabke',
              'lithuanian pop', 'christian uplift', 'trop rock', 'flint hip hop', 'trot', 'rock alternativo espanol',
              'virginia metal', 'lds youth', 'chinese bgm', 'german viral rap', 'early avant garde', 'swedish jazz',
              'cumbia andina mexicana', 'super eurobeat', 'novelty', 'russian metal', 'witch house', 'acoustic chill',
              'african rock', 'tribal house', 'space age pop', 'uzbek pop', 'finnish heavy metal', 'popping', 'glitch',
              'zouk', 'kawaii future bass', 'musica alagoana', 'louisiana blues', 'rap cristao', 'hip-hop experimental',
              'norwegian metal', 'klubowe', 'progressive jazz fusion', '5th wave emo', 'dansktop', 'swiss pop',
              'himachali pop', 'bongo flava', 'deep chill', 'musica coahuilense', 'eurobeat', 'braindance',
              'melodic hardcore', 'latin funk', 'modern jazz piano', 'asbury park indie', 'speed up brasileiro',
              'rap anime', 'czech folk', 'trance brasileiro', 'pub rock', 'czech pop rock',
              'australian underground hip hop', 'slovak pop', 'lds', 'modern melodic hardcore', 'salsa choke',
              'relaxative', 'south african pop dance', 'birmingham hip hop', 'ukrainian indie', 'australian americana',
              'emo trap en espanol', 'shabad', 'organic ambient', 'thai folk pop', 'gabber', 'bruneian pop',
              'acoustic punk', 'hardcore', 'j-reggae', 'flute rock', 'dreampunk', 'magyar alternative',
              'norwegian country', 'maskandi', 'banda carnavalera', 'afro drill', 'mathcore', 'zouk riddim',
              'groove room', 'israeli singer-songwriter', 'nu gabber', 'australian garage punk', 'latin soundtrack',
              'cologne hip hop', 'cante flamenco', 'bouncy house', 'brazilian bass', 'san marcos tx indie',
              'dominican pop', 'deconstructed club', 'japanese shoegaze', 'azeri rap', 'tolkien metal', 'shred',
              'icelandic singer-songwriter', 'talentschau', 'rap lyonnais', 'classic czech pop', 'psychobilly',
              'indian rock', 'country blues', 'tango', 'hurdy-gurdy', 'tone', 'deep rai', 'math rock', 'viet chill rap',
              'yodeling', 'malang indie', 'reggae gaucho', 'chilean hardcore', 'swedish garage rock',
              'hyperpop francais', 'ukg revival', 'symphonic black metal', 'classic greek pop', 'finnish melodeath',
              'techno kayo', 'rap baixada fluminense', 'shonen', 'electroclash', 'karneval', 'nashville indie', 'zxc',
              'mande pop', 'finnish alternative rock', 'ukrainian hip hop', 'latintronica', 'german hyperpop',
              'r&b italiano', 'italian techno', 'bosnian pop', 'lithuanian edm', 'belarusian indie', 'lambadao',
              'praise', 'papuri', 'ebm', 'brazilian boogie', 'dutch tech house', 'circuit', 'punjabi lo-fi',
              'christian lo-fi', 'ukrainian classical', 'chamber psych', 'vocal harmony group', 'pakistani indie',
              'experimental classical', 'cumbia colombiana regia', 'polish reggae', 'german worship', 'puirt-a-beul',
              'fantasy', 'reading indie', 'russian indie', 'electro bailando', 'disco polo', 'seiyu',
              'messianic praise', 'batak', 'indie catala', 'dutch r&b', 'turk sanat muzigi', 'perth indie',
              'chinese melodic rap', 'oktoberfest', 'belarusian hip hop', 'fogo pentecostal', 'ethnotronica',
              'polish punk', 'microtonal', 'cumbia ecuatoriana', 'anime piano', 'russian modern classical',
              'japanese piano', 'swedish dancehall', 'swedish reggae', 'austin americana', 'indie rockism',
              'euskal rock', 'rap antillais', 'italian reggae', 'high-tech minimal', 'ambient house', 'world fusion',
              'deep tech house', 'rap siciliano', 'pop worship', 'moldovan pop', 'new italo disco', 'chill beats',
              'west end', 'melodic deathcore', 'south african alternative', 'syrian pop', 'turkish modern jazz',
              'uk post-punk revival', 'instrumental soul', 'classic finnish pop', 'furry', 'shatta', 'musica gaucha',
              'christian afrobeat', 'workout product', 'indie extremena', 'slovak rock', 'british jazz',
              'russian punk rock', 'ragga jungle', 'oldschool deutschrap', 'no wave', 'orchestra',
              'california hardcore', 'concurso de talentos argentino', 'swiss indie', 'british power metal',
              'tanzanian pop', 'christelijk', 'surf music', 'lithuanian electronic', 'honky tonk', 'jump up',
              'rap romantico', 'funktronica', 'thai indie', 'san diego rap', 'j-punk', 'smutny rap', 'atlanta metal',
              'mundart', 'metal cover', 'finnish death metal', 'leicester indie', 'apostolic worship', 'montreal indie',
              'chanson paillarde', 'sevdah', 'gypsy jazz', 'hardvapour', 'boston metal', 'brega saudade', 'timba',
              'delta blues', 'speed up turkce', 'pinoy idol pop', 'musica cristiana guatemalteca', 'pirate',
              'funky house', 'scottish indie rock', 'techno', 'southern gospel', 'dariacore', 'russian witch house',
              'baglama', 'classic bhangra', 'britpop revival', 'pinoy indie rock', 'khaleeji iraqi', 'hawaiian',
              'czech classical', 'free jazz', 'acid house', 'neo-traditional bluegrass', 'trap beats', 'huayno',
              'shibuya-kei', 'denpa-kei', 'atlanta bass', 'french death metal', 'norwegian black metal',
              'comedie musicale', 'deathstep', 'nz hip hop', 'adventista', 'japanese drill', 'finnish edm', 'barcadi',
              'cocuk sarkilari', 'underground power pop', 'indonesian indie rock', 'funk melody', 'deep minimal techno',
              'atmospheric black metal', 'musica llanera', 'nasyid', 'polish old school hip hop', 'southern metal',
              'lesen', 'classic punjabi pop', 'jacksonville indie', 'japanese pop rap', 'cantautora argentina',
              'garhwali pop', 'carnatic vocal', 'norwegian singer-songwriter', 'nederreggae',
              'rap francais nouvelle vague', 'venezuelan indie', 'german ska', 'canadian old school hip hop',
              'nueva ola chilena', 'k-rock', 'punk \'n\' roll', 'minneapolis indie', 'handpan', 'canadian celtic',
              'yogyakarta indie', 'hyperpop en espanol', 'pakistani folk', 'irish hip hop', 'japanese indie pop',
              'chaotic hardcore', 'classic malaysian pop', 'harmonica blues', 'jamgrass', 'us power metal',
              'bangla pop', 'trap cristao', 'vintage jazz', 'malayalam hip hop', 'poezja spiewana', 'rap montrealais',
              'boston punk', 'jazz house', 'fingerstyle', 'baltimore hip hop', 'drone metal', 'musica nayarita',
              'indonesian edm', 'german ccm', 'folklore ecuatoriano', 'riddim', 'japanese screamo', 'indiana hip hop',
              'nepali indie', 'fluxwork', 'indonesian blues', 'futurepop', 'estonian hip hop', 'neurofunk',
              'vlaamse kinderliedje', 'michigan indie', 'classic dubstep', 'french psychedelic', 'psychill',
              'czech punk', 'russian viral pop', 'american contemporary classical', 'burmese pop', 'russian folk rock',
              'twee pop', 'rai algerien', 'chinderlieder', 'vietnamese idol pop', 'pittsburgh indie', 'sovietwave',
              'symphonic power metal', 'bristol indie', 'australian talent show', 'speed plug brasileiro',
              'new orleans blues', 'futuristic swag', 'manchester indie', 'mexican edm', 'geek folk', 'skansk musik',
              'scottish electronic', 'kompa', 'malian blues', 'substep', 'rumba congolaise', 'classic bangla pop',
              'british modern classical', 'classical performance', 'kundalini', 'norwegian classical',
              'kurdish hip hop', 'gaita zuliana', 'african gospel', 'balkan beats', 'cumbia amazonica', 'wyoming roots',
              'latin house', 'japanese dance pop', 'grand rapids indie', 'semarang indie', 'san diego indie', 'touhou',
              'ndombolo', 'hinos ccb', 'electric bass', 'epa dunk', 'cumbia salvadorena', 'dutch drill', 'dmv rap',
              'abstract', 'russian chanson', 'swedish progressive metal', 'rap regio', 'serbian hip hop',
              'medieval folk', 'cumbia uruguaya', 'enka', 'swiss rock', 'chill out', 'hong kong indie', 'bozlak',
              'japanese chill rap', 'russian dance pop', 'leipzig electronic', 'horrorcore', 'galante era',
              'croatian rock', 'nova musica carioca', 'psychedelic folk', '21st century classical',
              'brazilian classical', 'tempe indie', 'vintage tollywood', 'folclor colombiano',
              'neo-traditional country', 'nantes indie', 'rock piauiense', 'norske viser', 'experimental vocal',
              'south carolina indie', 'deathrash', 'alternative pop', 'american modern classical', 'african reggae',
              'pagan black metal', 'palestinian hip hop', 'kleinkunst', 'sung poetry', 'virgin islands reggae',
              'paisley underground', 'viet lo-fi', 'trova mexicana', 'springfield mo indie', 'russian reggae',
              'grindcore', 'alaska indie', 'finnish drill', 'christian punk', 'italian metal', 'folclore santiagueno',
              'flamenco guitar', 'kompa gouyad', 'jamtronica', 'ontario indie', 'japanese indie rock',
              'canadian post-hardcore', 'techengue', 'tape club', 'anime latino', 'huapango', 'chinese electropop',
              'japanese folk', 'kenyan pop', 'memphis blues', 'german punk rock', 'modern jazz trio', 'dark disco',
              'oc indie', 'folklore surero', 'jazz rock', 'kingston on indie', 'thai viral pop', 'malay rap',
              'bubblegum bass', 'dutch americana', 'modern hardcore', 'rap maromba', 'brazilian house', 'pop peruano',
              'musica campechana', 'musica popular paraense', 'vintage schlager', 'melodic groove metal', 'azeri pop',
              'aggrotech', 'vgm remix', 'musica oaxaquena', 'middle east hip hop', 'kannada hip hop',
              'french movie tunes', 'italian tech house', 'dream trance', 'boogaloo', 'mod revival', 'raw techno',
              'gaian doom', 'nu age', 'salsa international', 'swedish metalcore', 'collage pop', 'arab trap',
              'thai folk', 'horror synth', 'champeta', 'tallava', 'cuban alternative', 'american post-rock',
              'alberta country', 'classical piano', 'zespol dzieciecy', 'copla', 'kodomo no ongaku',
              'musica popular mineira', 'musica maranhense', 'drift', 'swiss hip hop', 'hokkaido indie',
              'fremantle indie', 'bogor indie', 'early music ensemble', 'kurdish folk', 'uk post-hardcore',
              'chinese minyao', 'singing bowl', 'danish alternative rock', 'kenyan r&b', 'alternative ccm',
              'folklore boliviano', 'soukous', 'huayno peruano', 'blackgaze', 'military rap', 'cumbia surena',
              'psychedelic doom', 'south african jazz', 'musica juiz-forana', 'instrumental bluegrass',
              'neue volksmusik', 'chopped and screwed', 'norwegian trap', 'israeli folk', 'instrumental math rock',
              'fidget house', 'funky tech house', 'beach house', 'malaysian hip hop', 'german jazz rap',
              'taiwan idol pop', 'uk desi rap', 'oriental metal', 'rajasthani pop', 'ukrainian electronic',
              'electro dub', 'japanese ska', 'irish metal', 'jirai kei', 'new tribe', 'lo-fi brasileiro', 'turntablism',
              'new england emo', 'latincore', 'jumpstyle', 'hauntology', 'zouglou', 'igbo pop', 'french indie folk',
              'dreamgaze', 'arkansas hip hop', 'children\'s choir', 'riddim dubstep', 'olympia wa indie',
              'korean singer-songwriter', 'orthodox chant', 'new delhi indie', 'hong kong rock', 'dc hardcore',
              'elektropunk', 'melbourne indie', 'rock viet', 'viet remix', 'chanson virale', 'north carolina indie',
              'luk thung', 'corridos cristianos', 'garage pop', 'scottish metal', 'hard motivation', 'norwegian jazz',
              'bluegrass gospel', 'motivation', 'electro trash', 'musica canaria', 'russian ska', 'chanson quebecois',
              'instrumental acoustic guitar', 'progressive trance house', 'trinibad', 'piratenmuziek', 'speed garage',
              'swedish heavy metal', 'clean comedy', 'japanese jazz', 'bolobedu house', 'greek indie', 'nyhc',
              'spanish synthpop', 'balearic', 'reunion pop', 'doujin', 'hindustani classical', 'downtempo bass',
              'latin ska', 'early synthpop', 'azeri traditional', 'western americana', 'hard industrial techno',
              'bounce', 'hip hop timur', 'classic portuguese pop', 'peruvian indie',
              'auteur-compositeur-interprete quebecois', 'shojo', 'oceania soundtrack', 'minimal wave',
              'belgian techno', 'cuban rumba', 'cumbia editada', 'indie platense', 'classic nz pop',
              'adoracion pentecostal', 'deep smooth jazz', 'korean dream pop', 'brass band', 'polish metal', 'hel',
              'florida death metal', 'talentkonkurranse', 'ambient idm', 'italian lounge', 'techno rave',
              'future bounce', 'acid techno', 'ballroom', 'hong kong hip hop', 'queercore', 'musica criolla',
              'bornesange', 'classic k-pop', 'musica instrumental cristiana', 'euskal musica', 'musical advocacy',
              'straight edge', 'opera', 'thai teen pop', 'cdmx indie', 'scottish folk', 'freak folk',
              'progressive uplifting trance', 'kawaii edm', 'guitarra mexicana', 'canto popular uruguayo',
              'french baroque', 'cha-cha-cha', 'utopian virtual', 'dakke dak', 'danseband',
              'rap underground colombiano', 'channel islands indie', 'orebro indie', 'experimental bass',
              'french folk pop', 'chinese drama ost', 'salsa cubana', 'acid jazz', 'sudanese pop',
              'southern soul blues', 'power-pop punk', 'cape town indie', 'brutal deathcore', 'progressive sludge',
              'nuevo folklore argentino', 'philly drill', 'classic progressive house', 'comptine',
              'african-american classical', 'native american contemporary', 'doomgaze', 'black thrash',
              'folklore peruano', 'dutch singer-songwriter', 'chinese manyao', 'louisville indie', 'nerdcore',
              'london indie', 'orlando indie', 'zikir', 'brazilian thrash metal', 'brazilian punk rock', 'stride',
              'contemporary gospel', 'tech trance', 'harpsichord', 'trap metal italiana', 'reggae catala',
              'classic japanese jazz', 'turkce remix', 'synth punk', 'musica andina chilena', 'telugu folk',
              'neo-progressive', 'canzone genovese', 'tin pan alley', 'japanese math rock', 'italian power metal',
              'jump blues', 'west coast trap', 'calypso', 'ethiopian pop', 'new england americana', 'renaissance',
              'morna', 'rabindra sangeet', 'avant-garde metal', 'sgija', 'gbvfi', 'desert blues',
              'musique urbaine kinshasa', 'german post-hardcore', 'argentine ambient', 'mashup', 'afrobeat brasileiro',
              'space ambient', 'classic nepali pop', 'swiss metal', 'rap motywacja', 'modern ska punk', 'arabic jazz',
              'french worship', 'welsh indie', 'anarcho-punk', 'antilliaanse rap', 'rebetiko', 'spacewave',
              'japanese rockabilly', 'glasgow indie', 'jazz trombone', 'dark hardcore', 'canadian indie folk',
              'sevillanas', 'hard alternative', 'toronto rap', 'japanese jazz fusion', 'kasi rap',
              'russian alternative rock', 'asheville indie', 'forro tradicional', '528hz', 'kabyle',
              'german show tunes', 'musik anak-anak', 'cowpunk', 'kannada pop', 'nu skool breaks', 'necrotrap',
              'chanson humoristique', 'plugg francais', 'classical guitar', 'german jazz', 'cedm', 'porro',
              'plena uruguaya', 'trap maroc', 'lo-fi latino', 'rap angolano', 'musica nicaraguense', 'carimbo',
              'melanesian pop', 'taiwan punk', 'balochi pop', 'egg punk', 'estonian pop', 'rogaland musikk', 'popgaze',
              'italian folk metal', 'danish modern jazz', 'russian metalcore', 'ecuadorian indie', 'irish indie rock',
              'rap criolo', 'american post-punk', 'indie cordoba', 'nordic folk', 'socal indie', 'metal mineiro',
              'fussball', 'anime drill', 'japanese jazztronica', 'nordic folk metal', 'brazilian progressive metal',
              'vancouver punk', 'oi', 'children\'s story', 'arab folk', 'streektaal', 'bulgarian trap',
              'belgian singer-songwriter', 'queer country', 'indie curitibano', 'chinese indie rock', 'kyrgyz hip hop',
              'italian progressive rock', 'cuatro venezolano', 'vgm instrumental', 'seemannslieder', 'suomirap',
              'k-pop reality show', 'rap italiano old school', 'finnish classical', 'underground rap',
              'hyperpop brasileiro', 'mexican metal', 'musica sarda', 'men chika', 'manso indie', 'russian indie rock',
              'danish indie pop', 'kundiman', 'dungeon synth', 'sinhala indie', 'frankfurt electronic',
              'nashville americana', 'malaysian tamil pop', 'balkan brass', 'metal guitar', 'polish post-punk',
              'hip hop cubano', 'mbalax', 'boy pop', 'tekno', 'vintage dutch pop', 'goregrind', 'czsk viral pop',
              'brazilian groove metal', 'gainesville indie', 'bolero cubano', 'classic greek rock', 'latvian pop',
              'ritmo kombina', 'nz electronic', 'persian electronic', 'spanish classical', 'dayton indie',
              'electro-industrial', 'irish indie', 'japanese power metal', 'bayerischer rap', 'argentine indie rock',
              'soulful house', 'turkce trap metal', 'keroncong', 'progressive death metal', 'mallsoft', 'elephant 6',
              'israeli trap', 'bulgarian hip hop', 'man\'s orchestra', 'ulkucu sarkilar', 'marathi traditional',
              'avant-garde jazz', 'folklore paraguayo', 'world chill', 'indie shoegaze', 'spanish invasion',
              'south african deep house', 'cambridgeshire indie', 'merengue tipico', 'bali indie', 'country quebecois',
              'tropical tecladista', 'chicago pop punk', 'ska jazz', 'gothabilly', 'japanese celtic',
              'cristiana para ninos', 'nova canco', 'north carolina emo', 'german boom bap', 'post-post-hardcore',
              't-pop girl group', 'drill and bass', 'avant-garde', 'canadian house', 'jamaican ska', 'huayno popular',
              'accordion', 'louvores pentecostais', 'swedish electronic', 'mega funk', 'belgian dnb', 'french dub',
              'funky breaks', 'vietnamese bolero', 'slovak trap', 'vaqueiro', 'rosary', 'cueca chilena',
              'new orleans funk', 'new wave of thrash metal', 'latin tech house', 'classic anime', 'cambodian pop',
              'christchurch indie', 'czech singer-songwriter', 'electronic djent', 'british orchestra',
              'japanese post-rock', 'danish indie', 'industrial pop', 'rap inde', 'space rock', 'sudanese hip hop',
              'fallen angel', 'early reggae', 'folclor afrocolombiano', 'family gospel', 'deep dnb', 'ethio-jazz',
              'belarusian pop', 'proto-techno', 'congolese gospel', 'gengetone', 'italian jazz', 'hokkien pop',
              'pop cristiano', 'progressive power metal', 'dutch dnb', 'tipico', 'medieval', 'voidgaze',
              'kizomba antigas', 'experimental folk', 'full on', 'thai ost', 'icelandic folk', 'swedish doom metal',
              'greek metal', 'folklore nuevo argentino', 'tamborazo', 'cincinnati rap', 'mappila paattu', 'hard techno',
              'classic finnish rock', 'folclore tucumano', 'lds instrumental', 'bajki', 'romanian rock',
              'post-doom metal', 'cumbia boliviana', 'son cubano', 'c86', 'modern funk', 'irish electronic',
              'indie dream pop', 'tamil worship', 'neru', 'persian rock', 'danish electropop', 'depressive black metal',
              'norwegian folk rock', 'old-time', 'irish pub song', 'autonomous black metal', 'football', 'j-core',
              'dublin indie', 'korean electropop', 'nz singer-songwriter', 'rap liegeois', 'instrumental djent',
              'zamba', 'danish jazz', 'choral', 'pop ambient', 'downtempo deathcore', 'turkish punk',
              'puerto rican folk', 'coupe-decale', 'traditional soul', 'australian metal', 'german heavy metal',
              'old west', 'ilahiler', 'crust punk', 'operetta', 'musica santomense', 'classic sinhala pop',
              'black punk', 'sydney indie', 'phleng phuea chiwit', 'adoracion', 'irish post-punk', 'slovak punk',
              'semba', 'commons', 'okc indie', 'zen', 'musica ayacuchana', 'finnish punk', 'kc indie', 'ska espanol',
              'yaoi', 'hard trance', 'melodic hard rock', 'coral gospel', 'nz indie', 'rap kreyol', 'garage house',
              'gqom', 'jazz mexicano', 'uk dub', 'turin indie', 'psychokore', 'indonesian indie pop', 'svensk progg',
              'thai pop rap', 'forro gospel', 'munich indie', 'ugandan pop', 'kizomba cabo-verdiana',
              'sichuanese hip hop', 'modern old-time', 'canadian modern jazz', 'musique guadeloupe',
              'swedish black metal', 'cypriot pop', 'vancouver metal', 'jazz clarinet', 'finnish hard rock',
              'musica tabasquena', 'audiophile vocal', 'modular synth', 'arunachal indie', 'slow game', 'polish blues',
              'krautrock', 'nwocr', 'nagpuri pop', 'japanese underground rap', 'omaha indie', 'tunisian pop',
              'vintage tango', 'folkmusik', 'palestinian pop', 'viola caipira', 'dutch indie rock',
              'korean underground rap', 'outsider', 'modern jungle', 'musica para criancas', 'israeli indie',
              'musica capixaba', 'symphonic death metal', 'connecticut hardcore', 'canadian garage rock', 'lagu sunda',
              'musica jalisciense', 'kyushu indie', 'ukrainian folk rock', 'rumeli turkuleri', 'library music',
              'modern uplift', 'midwest americana', 'german country', 'musica sudcaliforniana', 'tulsa indie',
              'gypsy punk', 'vietnamese pop', 'rock alternatif francais', 'dalarna indie',
              'british contemporary classical', 'miami indie', 'outsider house', 'draga', 'buffalo ny metal',
              'victorian britain', 'ukrainian post-punk', 'oshare kei', 'swedish synth', 'french punk', 'nephop',
              'heavy alternative', 'deep german indie', 'thai bl ost', 'symfonicky orchestr', 'rap capixaba',
              'neue deutsche todeskunst', 'rock chapin', 'brazilian hardcore', 'reggae peruano', 'modern goth',
              'native american flute', 'aussie emo', 'okinawan folk', 'greek house', 'dutch trap', 'cover acustico',
              'classic icelandic pop', 'blaskapelle', 'hiplife', 'funana', 'atlanta punk', 'uk worship', 'blasmusik',
              'granada indie', 'mandolin', 'zimdancehall', 'hardtekk', 'swedish punk', 'mestissatge', 'funk evangelico',
              'salsa urbana', 'musica madeirense', 'musica crista reformada', 'finnish indie', 'british country',
              'tibetan pop', 'bleep techno', 'trondersk musikk', 'atmospheric dnb', 'nordic post-rock',
              'dusseldorf electronic', 'musiikkia lapsille', 'corrosion', 'baiao', 'hungarian folk',
              'chinese traditional', 'beat italiano', 'chamame', 'traditional folk', 'persian melodic rap',
              'canterbury scene', 'pop costarricense', 'croatian hip hop', 'musica tropical guatemalteca', 'glitch pop',
              'persian alternative', 'rap paranaense', 'duluth indie', 'russian synthpop', 'samurai trap',
              'japanese vocal jazz', 'grimewave', 'russian trance', 'trival', 'slovenian pop', 'coco',
              'technical groove metal', 'austrian hip hop', 'swing italiano', 'dark progressive house', 'scouse rap',
              'vaportrap', 'hammond organ', 'maimouna', 'japanese contemporary classical', 'dissonant death metal',
              'shimmer psych', 'gothic americana', 'experimental house', 'deep adult standards', 'japanese guitar',
              'andean flute', 'marathi devotional', 'trio huasteco', 'austin hip hop', 'mecha',
              'instrumental stoner rock', 'pinoy alternative rock', 'instrumental surf', 'ghanaian gospel', 'swamp pop',
              'brass band pop', 'haitian gospel', 'deep latin alternative', 'munich electronic', '432hz',
              'kentucky punk', 'naat', 'musica istmena', 'german indie pop', 'telugu indie', 'russian plugg',
              'neapolitan funk', 'austrian indie', 'deep techno', 'bath indie', 'icelandic electronic', 'modern cello',
              'eugene indie', 'plunderphonics', 'musica andina colombiana', 'spanish reggae', 'dark jazz',
              'mongolian alternative', 'rennes indie', 'long island punk', 'christian hardcore', 'kora', 'jazz metal',
              'canadian hardcore', 'spanish folk rock', 'manitoba indie', 'balkan drill', 'freeform hardcore',
              'technical thrash', '48g', 'bass music', 'denton tx indie', 'nz children\'s music', 'drone folk',
              'german thrash metal', 'zillertal', 'latvian hip hop', 'greek downtempo', 'eventyr', 'emo punk',
              'russian folk', 'retro metal', 'post-black metal', 'japanese blues', 'piedmont blues',
              'vintage hollywood', 'ambient psychill', 'kentucky metal', 'singeli', 'choro', 'swiss house',
              'nordnorsk musikk', 'nova musica paulista', 'string duo', 'indian underground rap', 'nuevo flamenco',
              'armenian pop', 'indy indie', 'brazilian power metal', 'musica indigena latinoamericana', 'breakcore',
              'new orleans soul', 'korean indie folk', 'deathrock', 'lagu bali', 'classic dutch pop',
              'jazz double bass', 'modern enka', 'amharic pop', 'south african choral', 'indie emo',
              'russian trap metal', 'gothic black metal', 'emo trap italiana', 'musica baiana', 'turkish metal',
              'swing revival', 'deep christian rock', 'indonesian psychedelia', 'swedish house', 'rumba catalana',
              'jazz drums', 'pittsburgh rock', 'musica eletronica gospel', 'phoenix indie', 'spanish post-punk',
              'charlotte nc indie', 'darkstep', 'multidisciplinary', 'ambient post-rock', 'kaneka', 'connecticut indie',
              'arab groove', 'charanga', 'kolkata indie', 'cantautor catala', 'tampa indie', 'dutch prog', 'geek rock',
              'seinen', 'rhode island indie', 'denver indie', 'spanish noise pop', 'german indie rock', 'virginia punk',
              'italian trance', 'rap ivoire', 'vocal trance', 'jackin\' house', 'speed house', 'indie valenciana',
              'warm drone', 'villancicos', 'sepedi pop', 'reggae maghreb', 'igbo rap', 'deep funk ostentacao', 'bard',
              'swamp blues', 'vermont indie', 'musica feirense', 'new mexico music', 'zilizopendwa',
              'indie rock peruano', 'folklore chileno', 'deep soft rock', 'tamil devotional', 'korean trap',
              'japanese garage rock', 'belarusian electronic', 'musica quintanarroense', 'british dance band',
              'jesus movement', 'deep norteno', 'alabama metal', 'galician rock', 'deep soundtrack',
              'classic luk thung', 'indie siciliano', 'tatar pop', 'neo-pagan', 'leeds indie', 'cincinnati indie',
              'oud', 'christian a cappella', 'twoubadou', 'deep happy hardcore', 'british black metal',
              'japanese dream pop', 'sambalpuri pop', 'lapland metal', 'hungarian edm', 'musica afroperuana',
              'nueva trova chilena', 'brisbane hip hop', 'hexd', 'ambient techno', 'funk capixaba', 'ai', 'vincy soca',
              'paraguayan rock', 'punk chileno', 'kurdish remix', 'slovenian electronic', 'kent indie',
              'canadian indigenous music', 'persian underground hip hop', 'korean worship', 'jazz cubano',
              'musica popular uruguaya', 'chant religieux', 'bristol electronic', 'classic hungarian pop',
              'straight-ahead jazz', 'polish indie rock', 'british death metal', 'telugu devotional', 'neo metal',
              'underground amapiano', 'marimba orquesta', 'cyber metal', 'deep uplifting trance', 'dub techno',
              'neurostep', 'pinoy praise', 'portland punk', 'new orleans indie', 'rare groove', 'acidcore',
              'brazilian percussion', 'wu fam', 'gyerekdalok', 'hardstyle', 'ghettotech', 'classic azeri pop',
              'spiritual hip hop', 'skramz', 'jazz worship', 'lagu bugis', 'polish black metal', 'melodipop',
              'nice indie', 'vienna indie', 'louvor icm', 'malayalam indie', 'sinhala rap', 'rap femenino mexicano',
              'dub reggae', 'fort worth indie', 'hamburg indie', 'indie cristao', 'waiata maori',
              'classic romanian pop', 'ohio indie', 'australian ska', 'vintage swedish pop', 'harp', 'portuguese indie',
              'hindustani vocal', 'griot', 'slack-key guitar', 'minimal dub', 'musica mixteca', 'gospel drill',
              'raboday', 'neotango', 'taiwan campus folk', 'spanish folk', 'german literature', 'danish post-punk',
              'german opera', 'koligeet', 'alberta hip hop', 'nz folk', 'campursari', 'welsh hip hop', 'pakistani rock',
              'stockholm indie', 'powerviolence', 'dark folk', 'belarusian rock', 'chasidic pop',
              'viral pop brasileiro', 'funk mexicano', 'pennsylvania hardcore', 'jordanian pop', 'gothenburg hip hop',
              'chinese classical piano', 'orquesta tipica', 'uyghur pop', 'taiwanese indie', 'sound art',
              'progressive doom', 'lithuanian hip hop', 'tinku', 'texas hardcore', 'bangladeshi rock',
              'charlottesville indie', 'musiqi-ye zanan', 'kazakh indie', 'schranz', 'punk euskera', 'utah indie',
              'spa', 'beatboxing', 'soviet synthpop', 'bay area hip hop', 'western mass indie', 'swedish stoner rock',
              'dunedin indie', 'nl folk', 'melodic power metal', 'beatdown', 'miami metal', 'novo rock gaucho',
              'japanese heavy metal', 'classic hungarian rock', 'norwegian alternative rock', 'guinean pop',
              'pakistani electronic', 'guided meditation', 'birmingham indie', 'czech metal', 'cape verdean folk',
              'jazz organ', 'cinematic post-rock', 'world meditation', 'christian hard rock', 'lexington ky indie',
              'chinese talent show', 'vocaloid metal', 'montenegrin pop', 'beats', 'detroit house', 'windsor on indie',
              'german tech house', 'histoire pour enfants', 'black \'n\' roll', 'taiwan rock', 'rock keyboard',
              'pop paraguayo', 'czech country', 'footwork', 'smooth soul', 'west australian hip hop',
              'chinese classical performance', 'experimental jazz', 'louisiana metal', 'bouyon',
              'new orleans americana', 'ukrainian edm', 'bisaya rap', 'dubsteppe', 'tunantada', 'telugu worship',
              'guatemalan pop', 'hamilton on indie', 'norsk lovsang', 'hyperpop italiano', 'maine indie',
              'thai post-rock', 'uk bass', 'musica paraibana', 'progressive alternative', 'musique militaire',
              'tennessee metal', 'venda pop', 'indie napoletano', 'college a cappella', 'melodic black metal',
              'american grindcore', 'polish jazz', 'bhojpuri folk', 'exotica', 'nz christian', 'scottish techno',
              'truck-driving country', 'synth prog', 'musica guerrerense', 'bardcore', 'comedia', 'experimental indie',
              'epunk', 'gospel rap', 'neo-rockabilly', 'dancehall colombiano', 'kenyan hip hop', 'japanese indie folk',
              'neofolk', 'folclore jujeno', 'icelandic hip hop', 'hungarian metal', 'ghent indie', 'oulu metal',
              'dallas indie', 'bouzouki', 'jazzy dnb', 'chinese audiophile', 'power blues-rock', 'polish electronica',
              'canadian blues', 'british comedy', 'afro house angolano', 'musica cabo-verdiana', 'alt-idol',
              'schweizer rap', 'technical deathcore', 'musica infantil catala', 'anglican liturgy', 'lampung indie',
              'afghan rap', 'polish death metal', 'sound effects', 'piano mpb', 'scottish hush', 'black comedy',
              'trance mexicano', 'polca paraguaya', 'greek swing', 'japanese beats', 'tamaulipas indie',
              'cornetas y tambores', 'north moroccan rap', 'voetbal', 'indonesian hardcore', 'brisbane punk',
              'background jazz product', 'malawian pop', 'dub brasileiro', 'irish neo-traditional', 'italian gothic',
              'italian gothic metal', 'musica catarinense', 'muzica etno', 'spytrack', 'zcc', 'punk cover',
              'chinese worship', 'png pop', 'spanish indie folk', 'syrian hip hop', 'guitarra andina', 'lagu aceh',
              'zambian hip hop', 'gospel reggae', 'lebanese indie', 'tamil indie', 'ukulele', 'dutch moombahton',
              'psychedelic folk rock', 'musica yucateca', 'polynesian hip hop', 'cartoni animati', 'thall', 'chakra',
              'charango', 'christian power metal', 'british choir', 'brazilian ska', 'raggatek', 'folklore venezolano',
              'jain bhajan', 'slavic folk metal', 'psychedelic punk', 'ok indie', 'fan chant', 'detroit techno',
              'austin metal', 'austrian dnb', 'grebo', 'bandoneon', 'austrian metal', 'candomble', 'c-pop girl group',
              'broken transmission', 'sunnlensk tonlist', 'ramonescore', 'instrumental progressive metal',
              'musica bautista', 'sorani pop', 'north carolina metal', 'action rock', 'sci-fi metal', 'mashcore',
              'italo house', 'belgian indie rock', 'alpine yodeling', 'turkish electronic', 'indie folk argentino',
              'deep acoustic pop', 'trinidadian reggae', 'lithuanian trap', 'deep idm', 'cameroonian pop', 'er ge',
              'varmland rock', 'chinese folk', 'afro-cuban percussion', 'slam poetry', 'samoan pop',
              'musica evangelica instrumental', 'bush ballad', 'atmospheric post-metal', 'newfoundland indie',
              'halftime dnb', 'romanian electronic', 'marimba de guatemala', 'maithili', 'chamber folk',
              'one-person band', 'slam death metal', 'nwothm', 'punk melodico chileno', 'kurdish rock',
              'rochester ny indie', 'czech folk rock', 'hard house', 'tanzanian hip hop', 'xitsonga pop', 'zambian pop',
              'armenian hip hop', 'spiritual jazz', 'austin rock', 'york indie', 'idaho indie', 'gambian hip hop',
              'deep ragga', 'muzica crestina', 'musica duranguense', 'caucasian classical', 'carnaval limburg', 'visor',
              'italian library music', 'quebec punk', 'trap angolano', 'post-disco soul', 'oaxaca indie',
              'boston hardcore', 'danish techno', 'greek fem rap', 'vogue', 'rock en asturiano', 'bomba y plena',
              'melbourne punk', 'nuevo tango', 'german prog', 'psych gaze', 'corridos adictivos', 'tamazight',
              'modern progressive rock', 'british grindcore', 'nordic contemporary classical', 'vintage chanson',
              'dc indie', 'polish prog', 'berlin school', 'uk82', 'zim urban groove', 'moog', 'marathi remix',
              'experimental electronic', 'polish synthpop', 'sinaloa indie', 'death \'n\' roll', 'persian traditional',
              'hungarian underground rap', 'ska catala', 'blues latinoamericano', 'makossa', 'afro-funk',
              'dansei seiyu', 'southampton indie', 'rockabilly en espanol', 'rock of gibraltar',
              'technical melodic death metal', 'sami', 'cleveland metal', 'deep contemporary country',
              'british post-rock', 'jazz vibraphone', 'baltic classical', 'korean drill', 'nz dnb', 'scottish hip hop',
              'canadian underground hip hop', 'muzika l\'yeladim', 'italian electronica', 'israelite hip hop',
              'christmas product', 'rosario indie', 'mewati pop', 'israeli jazz', 'norwegian house',
              'gothic alternative', 'tuareg guitar', 'asakaa', 'musica popular amazonense', 'afrikaans hip hop',
              'appalachian folk', 'hardgroove', 'scratch', 'korean electronic', 'flick hop', 'slovenian indie',
              'devon indie', 'israeli techno', 'accordeon', 'malaysian punk', 'cosmic post-rock', 'jazz catala',
              'australian ambient', 'belgian metal', 'music hall', 'cruise', 'american primitive', 'norrlandsk hip hop',
              'swahili gospel', 'korean superband', 'usbm', 'marwadi pop', 'malayalam madh', 'khayal',
              'waiata mo tamariki', 'russian ccm', '2-step', 'indian electronic', 'uk christian rap',
              'italian renaissance', 'rap tico', 'classic korean pop', 'fijian pop', 'martial industrial',
              'new york death metal', 'dancehall chileno', 'detskie pesni', 'chamber orchestra', 'subliminal product',
              'musica portuguesa contemporanea', 'tearout', 'emotional black metal', 'psicodelia chilena',
              'cosmic death metal', 'fictitious orchestra', 'st louis drill', 'musique comorienne', 'hungarian punk',
              'chinese indie pop', 'vinahouse', 'classical cello', 'street punk espanol', 'swiss trap', 'bemani',
              'rap metal espanol', 'orchestral performance', 'brazilian modern jazz', 'paidika tragoudia', 'latmiya',
              'batida', 'puerto rican indie', 'sambass', 'hungarian classical performance', 'folklore uruguayo',
              'hindustani instrumental', 'cook islands pop', 'psalmen', 'fake', 'sitar', 'greek contemporary classical',
              'karaoke', 'ecuadorian alternative rock', 'palestinian alternative', 'israeli classical piano',
              'dominican indie', 'italian punk', 'deep gothic post-punk', 'math pop', 'peruvian punk',
              'musica michoacana', 'neo kyma', 'rap feminino chileno', 'polyphony', 'mumbai indie',
              'classic italian folk pop', 'viking black metal', 'wassoulou', 'south african underground rap',
              'ryukyu ongaku', 'rap chretien', 'yugoslav new wave', 'jig and reel', 'chaabi marocain', 'breton folk',
              'quebec death metal', 'punk catala', 'modern psychedelic folk', 'chinese soundtrack', 'zim hip hop',
              'tuna', 'musica nublensina', 'south asian metal', 'ukrainian classical piano', 'mongolian hip hop',
              'crack rock steady', 'danzon', 'kumaoni pop', 'malayalam cover', 'bomba', 'violao classico',
              'bangladeshi indie', 'newcastle indie', 'violin', 'tassie indie', 'bagpipe', 'graz indie', 'mpb gospel',
              'australian indigenous hip hop', 'sega mauricien', 'cumbia cristiana', 'rock curitibano', 'deep dubstep',
              'garage punk', 'spanish techno', 'balkan punk', 'ambient synth', 'french garage rock', 'warrington indie',
              'khortha pop', 'portland metal', 'gospel singers', 'rva indie', 'uwielbienie', 'goralski', 'eritrean pop',
              'slavic metal', 'taiwan instrumental', 'garage punk blues', 'vegan straight edge', 'mandible',
              'clap and tap', 'buffalo ny indie', 'remix product', 'japanese boom bap', 'christian dance',
              'kids hip hop', 'salsa cristiana', 'deep disco', 'swedish hardcore', 'bahai',
              'musique pour enfant quebecois', 'ukrainian folk pop', 'macedonian pop', 'lafayette indie', 'igbo trap',
              'chhattisgarhi pop', 'gulf hip hop', 'memphis americana', 'bahamian pop', 'shoegaze brasileiro',
              'cavernous death metal', 'new wave of glam metal', 'finnish new wave', 'lldm', 'slushwave',
              'modern swing', 'serbian electronic', 'sanfona', 'naija old school', 'american 21st century classical',
              'west african jazz', 'urban kiz', 'japanese melodic punk', 'punk rock italiano', 'british industrial',
              'deep progressive rock', 'british experimental', 'military band', 'wrock', 'japanese hyperpop',
              'rogaland indie', 'northeast indian indie', 'magyar retro dance', 'sheilat', 'detroit trap en espanol',
              'dennery segment', 'swedish rockabilly', 'rap portuense', 'kuduro', 'detske pisnicky', 'deep big room',
              'japanese psychedelic', 'didgeridoo', 'irish rebel song', 'ambient trance', 'uppsala indie',
              'mississippi indie', 'pop catracho', 'faroese pop', 'rwandan pop', 'french black metal',
              'indonesian underground hip hop', 'japanese electronic', 'uk beatdown', 'ukulele cover', 'pornogrind',
              'new isolationism', 'norwegian americana', 'musica hondurena', 'trio batak', 'jazz harp', 'panpipe',
              'cancoes infantis', 'swiss folk', 'indonesian metal', 'jazz brass', 'louange', 'hmong pop', 'comedienne',
              'manipuri pop', 'sonora indie', 'german black metal', 'argentine metal',
              'south african soulful deep house', 'czsk reggae', 'polish folk metal', 'solomon islands pop',
              'concert band', 'drill beats', 'kansai indie', 'san antonio rap', 'svensk lovsang', 'hamburger schule',
              'modern darkwave', 'brazilian post-hardcore', 'musica jibara', 'guyanese pop', 'derby indie',
              'norwegian punk rock', 'spanish electronic', 'danish singer-songwriter', 'spanish prog',
              'traditional british folk', 'italian new wave', 'hindi worship', 'american melodeath', 'persian drill',
              'deep progressive trance', 'worcester ma indie', 'telugu remix', 'chain punk', 'musica lombarda',
              'jewish hip hop', 'cypriot hip hop', 'bulgarian rock', 'swiss techno', 'ambient country',
              'swedish folk pop', 'greek guitar', 'psybass', 'vintage broadway', 'portuguese folk', 'flemish folk',
              'swedish prog', 'musicas espiritas', 'jalsat', 'garage psych', 'gospel italiano', 'throat singing',
              'rap pernambucano', 'japanese worship', 'lancaster pa indie', 'chinese jazz', 'memphis indie',
              'neo-kraut', 'musica aguascalentense', 'rusyn folk', 'persian sad rap', 'punta', 'sungura',
              'stateside dnb', 'tucson indie', 'slovenian rock', 'punta rock', 'stomp and whittle', 'deep deep house',
              'dronescape', 'glitch beats', 'plugg en espanol', 'euskal indie', 'muzica copii', 'ambient black metal',
              'makina', 'musica pitiusa', 'dub punk', 'leipzig indie', 'drill dominicano', 'indian percussion',
              'festigal', 'polish contemporary classical', 'german pagan metal', 'pittsburgh metal', 'contrabass',
              'norwegian space disco', 'ukrainian contemporary classical', 'kelowna bc indie', 'folk black metal',
              'bass trip', 'hungarian techno', 'moderne ludovky', 'mongolian pop', 'indie electronica',
              'malayalam worship', 'lagu sasak', 'banda guanajuatense', 'english renaissance', 'light music',
              'deep progressive house', 'chicano punk', 'guitarra clasica', 'halifax indie', 'dancehall guyanaise',
              'lancashire indie', 'columbus ohio indie', 'oth indie', 'cuento infantile', 'kenyan drill',
              'baptist gospel', 'czech indie', 'jazz puertorriqueno', 'singaporean electronic', 'armenian folk',
              'pashto pop', 'canadian psychedelic rock', 'detske pesnicky', 'german dnb', 'northern irish punk',
              'trad quebecois', 'future ambient', 'spanish rockabilly', 'aarhus indie', 'italian folk', 'rap galego',
              'swiss alternative rock', 'solipsynthm', 'brazilian techno', 'fast melodic punk', 'libyan pop',
              'american romanticism', 'northeast indian hip hop', 'erotica', 'atmospheric sludge',
              'arabic instrumental', 'swiss indie folk', 'brazilian dnb', 'acid trance', 'rap metalcore',
              'bossa nova jazz', 'highlife', 'deep liquid', 'psydub', 'broken beat', 'old school hard trance',
              'power thrash', 'corsican folk', 'deep soul house', 'musikkorps', 'romanian folk', 'psalms',
              'austin singer-songwriter', 'sega', 'magyar mulatos', 'limerick indie', 'xhosa', 'russian techno',
              'zurich indie', 'minimal dnb', 'hungarian indie', 'indie psych-pop', 'greek rock', 'industrial techno',
              'mexican traditional', 'vintage italian pop', 'experimental synth', 'swiss singer-songwriter', 'rasiya',
              'nitzhonot', 'gambian pop', 'canadian experimental', 'swiss reggae', 'deep brazilian pop', 'capoeira',
              'metal gotico', 'finnish pop punk', 'deep liquid bass', 'kenyan alternative', 'freakbeat', 'spirituals',
              'drone ambient', 'orquestas de galicia', 'irish punk', 'mezmur', 'punk tuga', 'french post-punk',
              'experimental guitar', 'boogie-woogie', 'musica costarricense', 'german dark minimal techno',
              'singaporean hip hop', 'texas punk', 'forest psy', 'serialism', 'reiki', 'gamecore', 'erotik',
              'swedish techno', 'dirty texas rap', 'australian blues', 'blackened screamo', 'vintage cantonese pop',
              'french dnb', 'indie singer-songwriter', 'cosmic black metal', 'nordic ambient', 'musica potiguar',
              'russian dnb', 'popullore jugu', 'technical black metal', 'bansuri', 'soul flow',
              'greek psychedelic rock', 'klapa', 'electronica chilena', 'birdsong', 'reggae mexicano', 'puglia indie',
              'deep new wave', 'somali pop', 'brazilian tech house', 'australian experimental', 'ukhc', '8-bit',
              'pop boliviano', 'indorock', 'uk stoner rock', 'south african country', 'canadian indigenous hip hop',
              'indie folk italiano', 'bible', 'berlin minimal techno', 'minimal dubstep', 'austro-german modernism',
              'deep metalcore', 'japanese experimental', 'nz gangsta rap', 'persian trap', 'irish classical',
              'italian ska', 'mbira', 'japanese girl punk', 'shamisen', 'focus trance', 'indie veneto',
              'south african r&b', 'musica nortena chilena', 'gypsy fusion', 'kansas indie', 'russian pop punk',
              'purple sound', 'dunedin sound', 'japanese edm', 'technical brutal death metal', 'outer hip hop',
              'rap moldovenesc', 'japanese traditional', 'pinoy metal', 'punjabi folk', 'edinburgh indie',
              'classic moroccan pop', 'laulaja-lauluntekija', 'uruguayan indie', 'kids dance party', 'erotic product',
              'surinamese pop', 'post-punk mexicano', 'drill tuga', 'belgian new wave', 'classic bulgarian pop',
              'joropo', 'arkansas indie', 'italian contemporary jazz', 'west virginia indie', 'jazz venezolano',
              'mizo pop', 'southern china indie', 'language', 'destroy techno', 'lezginka', 'oberkrainer',
              'dancehall mauricien', 'stl indie', 'dutch blues', 'lund indie', 'pacific islands gospel', 'lagu sabahan',
              'indie pop rock', 'musica occitana', 'vlaamse rap', 'turkish reggae', 'contemporary folk', 'spacesynth',
              'string folk', 'powwow', 'german melodeath', 'minneapolis punk', 'wyoming indie', 'deep neofolk',
              'detroit indie', 'country boogie', 'east anglia indie', 'belgian jazz', 'milwaukee hip hop',
              'romanian indie', 'canadian post-punk', 'yoruba worship', 'khmer hip hop', 'dutch jazz',
              'finnish progressive metal', 'malagasy pop', 'korean soundtrack', 'afro psych', 'vispop', 'madrigal',
              'chill baile', 'drumfunk', 'spanish indie rock', 'experimental club', 'thrash core',
              'hardcore punk espanol', 'indie rock colombiano', 'norrbotten indie', 'zydeco', 'sierra leonean pop',
              'christlicher rap', 'southeast asian post-rock', 'bisrock', 'german street punk', 'kyrgyz pop',
              'russian shoegaze', 'cantaditas', 'japanese idm', 'brazilian experimental', 'little rock indie',
              'traditional scottish folk', 'salay', 'malawian hip hop', 'belgian electronic', 'cologne electronic',
              'american choir', 'venda rap', 'gamelan', 'swedish psychedelic rock', 'tango cancion',
              'british math rock', 'musica mocambicana', 'purulia pop', 'progressive breaks', 'argentine hardcore',
              'guitarra argentina', 'irish dance', 'punk colombiano', 'new wave of osdm', 'african electronic',
              'north dakota indie', 'minneapolis metal', 'danish black metal', 'dark psytrance', 'baltic post-punk',
              'panamanian rock', 'deep ambient', 'denver metal', 'hengelliset laulut', 'trallpunk', 'early music choir',
              'samba gospel', 'brazilian indie rock', 'dutch black metal', 'chattanooga indie', 'navajo', 'santali pop',
              'musique tahitienne', 'german blues', 'mexican son', 'nordic shoegaze', 'afrobeat fusion',
              'indonesian trap', 'yoga', 'uk noise rock', 'barbershop', 'finnish black metal', 'rap guarulhense',
              'tunisian alternative', 'psychedelic jazz fusion', 'sefardi', 'irish drill', 'italian mandolin',
              'classical harp', 'galego', 'pei indie', 'myanmar indie', 'canadian psychedelic', 'australian techno',
              'traditional rockabilly', 'german electronica', 'ney', 'house argentino', 'lithuanian indie',
              'deep southern trap', 'vlaamse cabaret', 'ottawa indie', 'russian nu metal', 'khandeshi pop',
              'musique acadienne', 'ragtime', 'cabaret', 'vintage chinese pop', 'nohay', 'rock tico', 'banda peruana',
              'marimba mexicana', 'american orchestra', 'abstract idm', 'brazilian blues', 'russian pixel', 'ny roots',
              'sasscore', 'voidgrind', 'assyrian pop', 'malaysian tamil rap', 'jazz violin', 'estonian rock',
              'greenlandic pop', 'japanese psychedelic rock', 'erhu', 'celtic harp', 'ruta destroy', 'taiwan post-rock',
              'belgian modern jazz', 'montana indie', 'euroska', 'neo-psicodelia brasileira', 'western saharan folk',
              'pahadi pop', 'musica calabrese', 'deep melodic hard rock', 'luxembourgian indie',
              'south african electronic', 'finnish jazz', 'synthwave brasileiro', 'turkish post-punk', 'vaudeville',
              'portuguese metal', 'boogie', 'trap cristiano', 'guidance', 'barnalog', 'australian comedy',
              'slovak folk', 'dutch musical', 'piano house', 'deep german punk', 'psychedelic blues-rock',
              'gospel amapiano', 'new wave of speed metal', 'deep east coast hip hop', 'manitoba country',
              'hip hop reunionnais', 'friese muziek', 'caracas indie', 'essex indie', 'tzadik', 'galician folk',
              'klezmer', 'musica mapuche', 'jazz guitar trio', 'german death metal', 'traditional reggae',
              'string band', 'ambient dub techno', 'wisconsin indie', 'swedish post-hardcore', 'thai instrumental',
              'adelaide indie', 'new weird finland', 'son cubano clasico', 'georgian hip hop', 'dark electro',
              'musica goiana', 'humppa', 'calgary indie', 'albany ny indie', 'uilleann pipes',
              'post-punk latinoamericano', 'technical grindcore', 'musica indigena mexicana', 'polish hardcore',
              'fo jing', 'musica mallorquina', 'lo star', 'judaica', 'chinese instrumental', 'nz metal',
              'chicago mexican', 'euskal reggae', 'deep funk house', 'indonesian death metal', 'circus',
              'austrian black metal', 'speedcore', 'portuguese techno', 'joseon pop', 'georgian alternative',
              'indonesian emo rap', 'finnish progressive rock', 'cleveland indie', 'deep flow', 'talentos brasileiros',
              'cybergrind', 'grunge pop', 'norwegian contemporary jazz', 'psybreaks', 'african percussion',
              'folklore veracruzano', 'gothic post-punk', 'szanty', 'polish folk', 'sinogaze',
              'ukrainian alternative rock', 'forro manauara', 'blues-rock guitar', 'byzantine', 'metal colombiano',
              'rap tuga underground', 'finnish reggae', 'underground boom bap', 'tijuana indie', 'macedonian hip hop',
              'old school highlife', 'atmospheric doom', 'georgian pop', 'taiwan electronic', 'classic danish rock',
              'rap congolais', 'hip hop galsen', 'epic doom', 'french folk', 'experimental techno', 'talentkonkurrence',
              'mexican tech house', 'folklore cuyano', 'russian heavy metal', 'palestinian traditional',
              'isle of wight indie', 'latvian indie', 'lagu karo', 'electronicore', 'washboard', 'australian classical',
              'crossover prog', 'ukrainian folk', 'therapy', 'finnish soul', 'atlantic canada hip hop', 'neo-crust',
              'cork indie', 'marching band', 'experimental indie rock', 'canadian post-rock', 'blackened crust',
              'street band', 'electronica venezuela', 'darbuka', 'italian post-punk', 'kashmiri pop', 'rap ecuatoriano',
              'norwegian death metal', 'noise punk', 'cameroonian hip hop', 'barockinterpreten', 'bmore',
              'west-vlaamse hip hop', 'euskal metal', 'tanzlmusi', 'mallet', 'maluku pop', 'neo-trad metal',
              'bolivian rock', 'junior songfestival', 'progressive thrash', 'bisaya indie', 'pasodobles',
              'hard minimal techno', 'gnawa', 'jazz orchestra', 'umea hardcore', 'finlandssvenska musik', 'emocore',
              'ilocano pop', 'belarusian punk', 'norwegian gospel', 'lagu tarling', 'korean shoegaze',
              'rock progressif francais', 'bisaya worship', 'rap catarinense', 'electronica peruana',
              'ukrainian experimental', 'nordic classical piano', 'florida hardcore', 'traditional ska', 'thai metal',
              'franco-flemish school', 'dutch experimental electronic', 'finnish doom metal',
              'traditional english folk', 'canadian death metal', 'musica pernambucana', 'kalmar indie',
              'norwegian prog', 'ukrainian metal', 'zim gospel', 'narodnozabavna', 'croatian indie', 'bachchon ke geet',
              'russian classical piano', 'new england metal', 'komedi', 'czsk hyperpop', 'rock gotico',
              'deep folk metal', 'canberra indie', 'blues mexicano', 'hip hop boliviano', 'balfolk', 'jewish a capella',
              'japanese house', 'sesotho pop', 'musica mexiquense', 'musica valenciana', 'modern jangle pop',
              'dark ambient', 'faroese indie', 'greek black metal', 'deep freestyle', 'noisecore', 'american oi',
              'balkan post-punk', 'grenada soca', 'dainuojamoji poezija', 'military cadence', 'bodo pop',
              'musique touareg', 'myanmar hip hop', 'emoviolence', 'azeri alternative', 'indie tico',
              'musique mariage algerien', 'lithuanian rock', 'indie campechano', 'albanian rock', 'punk galego',
              'massage', 'italian metalcore', 'virginia indie', 'french hardcore', 'maine hip hop', 'taraneem',
              'tibetan mantra', 'bangladeshi hip hop', 'estonian electronic', 'pune indie', 'italian post-hardcore',
              'iowa hip hop', 'musica antigua', 'swiss worship', 'lagu manado', 'tijuana electronic', 'xinyao',
              'japanese classical piano', 'swedish experimental', 'russian emo', 'swiss black metal',
              'russian post-rock', 'swedish underground rap', 'winnipeg hip hop', 'avant-garde black metal',
              'classic tollywood', 'knoxville indie', 'mincecore', 'musica sammarinese', 'australian hardcore',
              'forro instrumental', 'bajan soca', 'bosnian indie', 'louisville underground', 'czech alternative rap',
              'korean bl ost', 'bangalore indie', 'chimurenga', 'trash rock', 'togolese pop', 'uk diy punk',
              'cornwall indie', 'montana roots', 'brasilia indie', 'canadian comedy', 'electronica cristiana',
              'deep dance pop', 'yemeni pop', 'modern big band', 'bagpipe marching band', 'gospel soul',
              'muzica usoara', 'brazilian death metal', 'krajiska muzika', 'spanish experimental', 'tribute',
              'german classical piano', 'musica paranaense', 'london on indie', 'japanese bedroom pop',
              'kannada bhava geethe', 'german hardcore', 'dresden indie', 'hi-tech', 'psychedelic space rock',
              'australian jazz', 'pre-war blues', 'polka nortena', 'slovak electronic', 'hausa pop',
              'indonesian hyperpop', 'oslo indie', 'college marching band', 'black death', 'cascadian black metal',
              'latino comedy', 'classical trumpet', 'raspe', 'beach music', 'italian death metal', 'polyphonies corses',
              'dikir barat', 'icelandic post-punk', 'second line', 'finnish metalcore', 'stuttgart indie',
              'cascadia psych', 'texas death metal', 'deep melodic death metal', 'bornehistorier', 'hjemmesnekk',
              'canadian black metal', 'polish thrash metal', 'seattle metal', 'muzica moldoveneasca', 'd-beat',
              'nyc metal', 'finnish electro', 'acousmatic', 'backing track', 'mindfulness', 'traditional funk',
              'michigan folk', 'breaks', 'dessin anime', 'irish banjo', 'ukrainian black metal', 'igbo traditional',
              'malmo indie', 'latvian rock', 'finnish worship', 'german stoner rock', 'deep funk',
              'musica de intervencao', 'rap gaucho', 'danish death metal', 'mexican death metal', 'dub metal',
              'milwaukee indie', 'cantonese worship', 'lasten satuja', 'musique nigerienne', 'indonesian deathcore',
              'kabyle moderne', 'russian old school hip hop', 'street punk', 'algerian folk', 'underground grunge',
              'japanese classical performance', 'classical soprano', 'ua trap', 'sevilla indie', 'reggae tico',
              'zenonesque', 'old school nederhop', 'pinoy edm', 'cymraeg', 'slovak indie', 'afrikaans gqom',
              'noel quebecois', 'odia bhajan', 'turkish classical performance', 'rwandan gospel', 'kuduro antigo',
              'swedish blues', 'turkish classical', 'rap abc paulista', 'polish techno', 'rock campineiro',
              'italian jazz fusion', 'neo grime', 'algorave', 'canadian rockabilly', 'cardiff indie', 'zambian gospel',
              'cornish folk', 'japanese post-punk', 'hard rock mexicano', 'kansas hip hop', 'spanish jazz',
              'south dakota indie', 'adivasi pop', 'kokborok pop', 'fuji', 'historic piano performance',
              'melbourne hip hop', 'portuguese indie rock', 'malagasy folk', 'french oi', 'arizona punk',
              'musica colombiana instrumental', 'russian romance', 'japanese death metal', 'rautalanka', 'gabonese pop',
              'rock cearense', 'heligonka', 'greek folk', 'lounge house', 'mexican experimental',
              'northwest china indie', 'mexican hardcore', 'singaporean indie', 'baja indie', 'jazz flute',
              'liechtenstein', 'german post-punk', 'native american hip hop', 'deep psychobilly',
              'classical jazz fusion', 'go-go', 'sesotho hip hop', 'uzbek hip hop', 'muzica populara', 'perth hip hop',
              'anthem', 'bulgarian r&b', 'lawrence ks indie', 'death doom', 'bal-musette', 'dutch death metal',
              'deep darkpsy', 'rock paraibano', 'balinese traditional', 'kritika', 'doomcore', 'ugandan gospel',
              'australian post-rock', 'metal catala', 'musica eletronica brasileira', 'native american spiritual',
              'schwyzerorgeli', 'khmer', 'italian pop punk', 'canadian drill', 'old school uk hip hop', 'indian metal',
              'ethiopian hip hop', 'murga', 'tigrigna pop', 'hull indie', 'grunneger muziek', 'power noise',
              'musica etnica', 'norwegian doom metal', 'whale song', 'danish punk', 'hardcore breaks', 'ostschlager',
              'new tejano', 'beninese pop', 'prog quebec', 'black speed metal', 'japanese techno', 'swedish post-punk',
              'prepared piano', 'norman ok indie', 'australian death metal', 'german renaissance', 'brass ensemble',
              'dundee indie', 'taiwanese indigenous music', 'deep punk rock', 'classic sudanese pop',
              'rap sureno chileno', 'estonian indie', 'chaabi algerien', 'balkan folk metal', 'hypnosis', 'fado antigo',
              'comptine africaine', 'argentine jazz', 'finnish folk', 'xhosa hip hop', 'goa hip hop', 'jumptek',
              'musique mahoraise', 'surinamese hip hop', 'serbian indie', 'medieval black metal', 'punk mexicano',
              'meenawati', 'mongolian folk', 'persian neo-traditional', 'swedish pop punk',
              'russian experimental electronic', 'jazz accordion', 'australian post-punk', 'hampton roads indie',
              'indie salvadoreno', 'saraiki pop', 'contemporary choir', 'norwegian psychedelic', 'west yorkshire indie',
              'uk rockabilly', 'cambodian rock', 'harmonica jazz', 'chilean metal', 'nisiotika', 'kerkkoor',
              'scottish indie folk', 'deep vocal jazz', 'juju', 'japanese progressive house', 'czech electronic',
              'orquesta tropical', 'czsk electropop', 'mexican classical', 'cocuk masallari', 'rap salvadoreno',
              'symphonic melodic death metal', 'experimental psych', 'icelandic jazz', 'bloco', 'dansk lovsang',
              'musiikkia lapista', 'neo soul-jazz', 'indie michoacano', 'bulgarian electronic', 'turkmen pop',
              'carnatic instrumental', 'baltic folk', 'icelandic metal', 'rock goiano', 'chinese electronic',
              'konkani pop', 'chennai indie', 'chant basque', 'christian deathcore', 'lao hip hop',
              'classic tunisian pop', 'maltese pop', 'blackened hardcore', 'scottish gaelic folk', 'steel guitar',
              'chabad niggunim', 'norwegian experimental', 'slovenian folk', 'coventry indie', 'quarteto gospel',
              'arpa grande', 'musica sul-mato-grossense', 'nz jazz', 'string quartet', 'burundian pop',
              'malaysian metal', 'free folk', 'honky-tonk piano', 'musica andorra', 'britcore', 'mezwed',
              'modular techno', 'gotlandsk musik', 'meyxana', 'sean-nos singing', 'old school ebm', 'mluvene slovo',
              'skinhead oi', 'basque folk', 'igbo worship', 'gospel blues', 'deep sunset lounge', 'detski pesnichki',
              'ukrainian ccm', 'musique mandingue', 'nueva ola peruana', 'scottish fiddle', 'welsh folk', 'weightless',
              'spanish renaissance', 'danish experimental', 'portuguese black metal', 'swiss jazz', 'nu electro',
              'heavy gothic rock', 'lao pop', 'tavern', 'iowa indie', 'north alabama indie', 'bohemian baroque',
              'banjara pop', 'dubstep product', 'rap norteno chileno', 'japanoise', 'uae indie', 'indie cantabria',
              'epic black metal', 'israeli metal', 'inuit pop', 'nz hardcore', 'spanish electropop', 'yorkshire folk',
              'georgian folk', 'drikkelek', 'geinin song', 'japanese prog', 'garage rock mexicano',
              'progressive black metal', 'korean metal', 'classic afrobeat', 'boston electronic',
              'brazilian lo-fi rock', 'cambridge choir', 'haur kantak', 'afrikaans gospel', 'musica purepecha',
              'albanian alternative', 'birthday', 'wind symphony', 'italian stoner rock', 'kaseko', 'taiwan metal',
              'serbian alternative rock', 'chinese metalcore', 'sebene', 'sulawesi indie', 'japanese choir',
              'barnasogur', 'slaskie piosenki', 'funeral doom', 'swedish rock-and-roll', 'duduk', 'musica wixarika',
              'industrial black metal', 'polka', 'screamocore', 'comfy synth', 'fado de coimbra', 'university choir',
              'classical saxophone', 'banda de viento', 'georgian electronic', 'psytech', 'bleakgaze',
              'finnish idol pop', 'taiwanese pop', 'guam indie', 'galician jazz', 'musica guineense',
              'nova musica amazonense', 'swansea indie', 'rap guineen', 'seggae', 'maracatu', 'pohadky',
              'vintage taiwan pop', 'old-time fiddle', 'psicodelia mexicana', 'deep discofox', 'maloya',
              'afro-cuban traditional', 'musica brasiliense', 'telugu hip hop', 'slovenian hip hop',
              'south carolina metal', 'rondalla', 'choro contemporaneo', 'siberian folk', 'polish ambient',
              'heavy psych', 'russian folk metal', 'cajun', 'irish techno', 'experimental black metal',
              'wellington indie', 'shakuhachi', 'muzica lautareasca', 'kinderliedjies', 'hammered dulcimer',
              'faroese rock', 'belgian blues', 'korean hyperpop', 'icelandic black metal', 'ambient fusion',
              'classical organ', 'finnish blues', 'hot jazz', 'starogradska', 'war metal', 'adelaide punk',
              'kashmiri hip hop', 'progressive technical death metal', 'traditional bluegrass',
              'tennessee experimental', 'khasi pop', 'panamanian indie', 'jazzcore', 'oriental classical', 'yu-mex',
              'musica chiapaneca', 'musica indigena brasileira', 'austrian techno', 'scottish jazz', 'goa trance',
              'sludgecore', 'atmospheric post-rock', 'mexican thrash metal', 'mevlevi sufi', 'hard glam',
              'burkinabe pop', 'musica otavalena', 'indian jazz', 'nova musica maranhense', 'acid idm',
              'polish modern jazz', 'mexican post-rock', 'hazaragi pop', 'estonian folk', 'pittsburgh indie rock',
              'chamorro pop', 'aggro chileno', 'melodic doom', 'greek indie rock', 'french stoner rock',
              'lapland hip hop', 'italian emo', 'rap mocambicana', 'native american metal', 'hypnotic techno',
              'vietnamese electronic', 'dambora', 'shanghai indie', 'viola da gamba', 'convent', 'deep psytrance',
              'poznan indie', 'serbian folk', 'surabaya indie', 'triangle indie', 'french emo', 'portuguese jazz',
              'slovenian metal', 'haryanvi ragni', 'indie canario', 'son jarocho', 'japanese concert band',
              'lovecraftian metal', 'classic psychedelic rock', 'reading', 'deep downtempo fusion', 'ngoni',
              'dicsoites', 'austrian jazz', 'cape breton folk', 'ambient industrial', 'guzheng', 'namibian pop',
              'latin shoegaze', 'rap euskera', 'dutch classical piano', 'german post-rock', 'bosnian electronic',
              'banda militar', 'protest folk', 'belgian contemporary classical', 'classical mandolin',
              'bluegrass fiddle', 'belgian black metal', 'modern string quartet', 'free improvisation',
              'maltese hip hop', 'melodic progressive metal', 'nordnorsk rap', 'trap boliviano', 'lastelaulud',
              'icelandic punk', 'deep classic garage rock', 'chapman stick', 'gumbe', 'norwegian hardcore',
              'women\'s choir', 'koledy', 'polish psychedelia', 'italian experimental', 'musica queretana',
              'australian black metal', 'norwegian techno', 'concertina', 'bandolim', 'sacred steel',
              'metal ecuatoriano', 'dusseldorf indie', 'downtempo fusion', 'marathi hip hop', 'swedish classical',
              'macedonian folk', 'boeremusiek', 'forest black metal', 'swiss country', 'full on groove',
              'haitian dance', 'finnish modern jazz', 'vocal ensemble', 'chechen pop', 'arpa paraguaya', 'merida indie',
              'latvian folk', 'hawaiian indie', 'sunset lounge', 'tibetan hip hop', 'deep g funk',
              'new hampshire indie', 'vaikiskos dainos', 'italian black metal', 'thai shoegaze',
              'spanish progressive rock', 'slovenske chvaly', 'indiana indie', 'early american folk',
              'rap ecuatoguineano', 'basel indie', 'brazilian black metal', 'lowercase', 'rap malien', 'korean jazz',
              'scottish americana', 'rap nica', 'dark minimal techno', 'arab metal', 'rotterdam indie',
              'death industrial', 'musica tradicional dominicana', 'indonesian shoegaze', 'finnish post-punk',
              'lagu iban', 'south african modern jazz', 'british classical piano', 'viet instrumental',
              'combos nacionales', 'benga', 'rock caipira', 'medway sound', 'edo old school', 'karbi pop',
              'techno argentina', 'ukrainian metalcore', 'folk siciliana', 'nyckelharpa', 'malang punk', 'noise', 'via',
              'cuban funk', 'british brass band', 'sufi chant', 'brazilian metalcore', 'experimental dub', 'greek punk',
              'vintage reggae', 'contemporary classical piano', 'dutch punk', 'finnish tango', 'salzburg indie',
              'musica cearense', 'irish accordion', 'mathgrind', 'canti alpini', 'bhutanese pop', 'frankfurt indie',
              'barrelhouse piano', 'tongan pop', 'black sludge', 'shoegaze chileno', 'peruvian metal',
              'math rock latinoamericano', 'c64', 'fado instrumental', 'danish classical', 'rap gabonais',
              'rwandan hip hop', 'demoscene', 'tajik pop', 'rez country', 'veena', 'power electronics',
              'musica morelense', 'russian hardcore', 'south african metal', 'leon gto indie', 'indie fuzzpop',
              'oeteldonk', 'chamber choir', 'seychelles pop', 'german rockabilly', 'djecje pjesme',
              'folk metal latinoamericano', 'baps', 'steelpan', 'sda choir', 'rio grande do sul indie', 'illbient',
              'ryukoka', 'occult black metal', 'lesotho traditional', 'denver rap', 'sundanese traditional',
              'coptic hymn', 'marrabenta', 'belgian death metal', 'irish black metal', 'latvian electronic',
              'cuatro puertorriqueno', 'spanish post-rock', 'italian contemporary classical', 'deep hardtechno',
              'tuna universitaria', 'neo-manele', 'finnish choir', 'greek techno', 'uk post-metal',
              'vintage country folk', 'japanese dub', 'qanun', 'trikiti', 'latin surf rock', 'japanese orchestra',
              'alternative metalcore', 'italogaze', 'australian classical piano', 'nz alternative rock', 'guitar case',
              'metal gaucho', 'derry indie', 'lowlands hardcore', 'chamame brasilero', 'ritual ambient',
              'chinese post-rock', 'french post-rock', 'classic australian country', 'yoik', 'german orchestra',
              'classical clarinet', 'russian contemporary classical', 'galician indie', 'dub poetry', 'dortmund indie',
              'brno indie', 'myanmar gospel', 'ugandan hip hop', 'pops orchestra', 'belgian post-rock',
              'baroque ensemble', 'norwegian folk', 'russian orchestra', 'gaita', 'mexican techno', 'swedish fiddle',
              'macedonian electronic', 'italian doom metal', 'yakut pop', 'brockton hip hop', 'nz punk', 'irish fiddle',
              'finnish experimental', 'coldwave', 'portsmouth indie', 'romanian metal', 'french renaissance', 'sarod',
              'fort wayne indie', 'turkish death metal', 'volkstumliche musik', 'firenze indie',
              'canadian classical piano', 'musica sergipana', 'indonesian neo-psychedelia', 'keller synth', 'cifteli',
              'gothic doom', 'tarantella', 'drama', 'finnish hardcore', 'quebec hardcore', 'swedish emo',
              'swedish contemporary classical', 'rap toscana', 'sotalaulut', 'deep filthstep', 'deep eurodance',
              'brass band brasileiro', 'modern chamber music', 'south african punk', 'medimeisterschaften',
              'indie poblano', 'trondheim indie', 'israeli punk', 'dutch underground hip hop', 'chinese reggae',
              'isle of man indie', 'magyar musicalek', 'bernu dziesmas', 'radio symphony', 'decije pesme', 're:techno',
              'raw black metal', 'metal paranaense', 'oulu indie', 'ancient mediterranean', 'ohangla', 'idol game',
              'cello ensemble', 'indie paraense', 'rap alagoano', 'musica prehispanica', 'taiwan classical performance',
              'clawhammer banjo', 'romanian punk', 'missouri indie', 'spanish classical piano',
              'polish experimental electronic', 'italian hardcore', 'classic latvian pop', 'jazz dominicano',
              'botswana hip hop', 'shib', 'electroacoustic improvisation', 'west virginia metal', 'lute',
              'indie boliviano', 'oratory', 'austrian punk', 'karen pop', 'syro-aramaic chant', 'chill-out trance',
              'balalaika', 'vintage norwegian pop', 'kompa chretien', 'instrumental death metal', 'mizo gospel',
              'bern indie', 'san antonio indie', 'rap sergipano', 'japanese melodic hardcore', 'fisarmonica',
              'jug band', 'drone rock', 'post-punk brasileiro', 'musica folk asturiana', 'swedish ebm',
              'french rock-and-roll', 'oxford choir', 'lombok indie', 'tamburica', 'austrian stoner rock',
              'luxembourgian pop', 'modern mod', 'reggae boliviano', 'tuvan folk', 'canadian shoegaze',
              'hong kong tv drama', 'chinese new year', 'skweee', 'diy pop punk', 'italian classical piano',
              'swedish choir', 'muzica bisericeasca', 'galway indie', 'new england hardcore', 'rock catracho',
              'chinese metal', 'neo-trad prog', 'iraqi hip hop', 'jazz chileno', 'bosstown sound',
              'japanese black metal', 'rominimal', 'ohio hardcore', 'hungarian contemporary classical',
              'finnish psychedelic rock', 'rap paraguayo', 'hypertrance', 'canzone siciliane', 'christian death metal',
              'irish contemporary classical', 'swazi pop', 'australian shoegaze', 'nubian traditional',
              'classic ukrainian pop', 'staff band', 'traditional southern folk', 'rock alagoano',
              'indie sudcaliforniano', 'trap kreyol', 'catalan folk', 'jazz tico', 'russian black metal', 'ringtone',
              'danish folk', 'singaporean metal', 'muzica ardeleneasca', 'russian choir', 'cuban electronic',
              'austrian orchestra', 'icelandic traditional', 'bulgarian folk', 'kannada indie', 'musica piauiense',
              'kol isha', 'terrorcore', 'lagu maluku', 'houston indie', 'rap nortista', 'cathedral choir',
              'folclore portugues', 'croatian metal', 'svensk indie', 'paraguayan indie', 'musique urbaine brazzaville',
              'cumbia funk', 'industrial hardcore', 'pilates', 'armenian indie', 'zarzuela', 'korean musicals',
              'faroese folk', 'libyan hip hop', 'russian power metal', 'tibetan traditional', 'viet edm',
              'chamber ensemble', 'polish post-rock', 'indian ambient', 'deep hardcore', 'belgian punk',
              'new jack smooth', 'mountain dulcimer', 'pontian folk', 'musica campista', 'turkish experimental',
              'deep melodic metalcore', 'arkansas metal', 'japanese hardcore', 'wisconsin metal', 'paracana',
              'italo beats', 'dub product', 'pinoy shoegaze', 'prague indie', 'jazz tuba', 'norwegian punk',
              'native american black metal', 'irish flute', 'baton rouge indie', 'guitarra portuguesa', 'tabla',
              'wuhan indie', 'indian violin', 'dansk comedy', 'colombian hardcore', 'horror punk brasileiro',
              'colorado hardcore', 'new brunswick indie', 'chinese post-punk', 'grisly death metal',
              'indie psychedelic rock', 'dungeon rap', 'swedish grindcore', 'avant-rock', 'colombian electronic',
              'vintage french psychedelic', 'bulgarian indie', 'animegrind', 'musique mauritanienne',
              'hungarian classical piano', 'neo-industrial rock', 'goa psytrance', 'finnish electronic',
              'modern electroacoustic', 'chinese classical', 'guatemalan metal', 'musica menorquina',
              'indie hidalguense', 'poetry', 'kinderchor', 'tar', 'deep jazz fusion', 'nagaland indie',
              'australian thrash metal', 'italian post-rock', 'hardingfele', 'vintage spanish pop', 'dechovka',
              'trekkspill', 'south sudanese pop', 'musica ecuatoguineana', 'irish underground rap',
              'japanese buddhist chant', 'christian thrash metal', 'botswana pop', 'historically informed performance',
              'spanish blues', 'american early music', 'baithak gana', 'xenharmonic', 'neo honky tonk',
              'indie trujillano', 'utah metal', 'oromo pop', 'german shoegaze', 'metal tico',
              'rock progresivo mexicano', 'bahamian folk', 'eastern bloc groove', 'greek jazz', 'afghan traditional',
              'gotico brasileiro', 'musica rapa nui', 'deep full on', 'vintage swing', 'bengali folk', 'candombe',
              'covertrance', 'spanish psychedelic rock', 'indonesian experimental', 'santoor', 'belgian stoner rock',
              'arab experimental', 'dragspel', 'abstractro', 'caucasian classical piano', 'irish gaelic folk',
              'balafon', 'unblack metal', 'chinese experimental', 'javanese gamelan', 'garifuna folk', 'lai hla',
              'marcha funebre', 'indie hidrocalido', 'totalism', 'spanish baroque', 'classic konkani pop',
              'norwegian blues', 'streichquartett', 'yuri', 'belarusian metal', 'st petersburg fl indie',
              'musique concrete', 'rajasthani folk', 'swiss punk', 'mainland se asia metal', 'circassian folk', 'taiko',
              'canadian choir', 'jazz colombiano', 'medieval ensemble', 'scottish drill', 'indie arequipeno',
              'minimal synth', 'classical flute', 'latin american heavy psych', 'lithuanian folk', 'irish trap',
              'molam', 'bolivian metal', 'grunge revival', 'classic female blues', 'batswana traditional', 'jugendchor',
              'alandsk musik', 'muzica maramureseana', 'duhovne pjesme', 'gaddiyali pop', 'min\'yo', 'rap gasy',
              'korean experimental', 'australian rockabilly', 'aberdeen indie', 'romanian black metal', 'thai worship',
              'israeli traditional', 'christian symphonic metal', 'andalusian classical', 'folclore castilla y leon',
              'folk cantabria', 'men\'s choir', 'marinera', 'himalayan folk', 'luxembourgian hip hop', 'raga rock',
              'trio cubano', 'classical mezzo-soprano', 'brazilian rockabilly', 'russian death metal',
              'italian screamo', 'kosovan indie', 'brazilian stoner rock', 'macedonian indie', 'garo pop',
              'nhac thieu nhi', 'dutch folk', 'cape breton indie', 'classical percussion', 'rock potiguar',
              'pinoy traditional', 'senegalese traditional', 'classical countertenor',
              'brazilian contemporary classical', 'koto', 'bangla gojol', 'korean punk', 'croatian folk', 'dombra',
              'rap potiguar', 'sindhi', 'hula', 'grim death metal', 'prank', 'neo-proto', 'danish electro',
              'novos talentos brasileiros', 'israeli classical', 'classical baritone', 'rhythm rock',
              'colombian death metal', 'german choir', 'classic assamese pop', 'finnish techno', 'zeuhl',
              'colombian black metal', 'portuguese contemporary classical', 'lagu betawi', 'kinnauri pop',
              'korean classical performance', 'rock nica', 'french classical piano', 'otroske pesmice',
              'dutch punk rock', 'umea indie', 'cantonese opera', 'dutch contemporary classical', 'sinhala edm',
              'metal noir quebecois', 'danish hardcore', 'mising pop', 'polynesian traditional', 'deep free jazz',
              'glitter trance', 'scottish smallpipe', 'deep vocal house', 'post-punk colombiano', 'brass quintet',
              'canadian contemporary classical', 'maghreb', 'musique peule', 'indonesian bamboo', 'slc hardcore',
              'rock sergipano', 'malawian folk', 'finnish rockabilly', 'hakkapop', 'portuguese death metal',
              'dutch stoner rock', 'saxophone trio', 'marimba', 'vintage finnish jazz', 'dhrupad', 'western ny metal',
              'euro hi-nrg', 'russian jazz', 'musica colimense', 'deep northern soul', 'indian instrumental rock',
              'minnesota metal', 'northamptonshire indie', 'canadian stoner rock', 'epic collage', 'ho munda',
              'nyahbinghi', 'kentucky mountain folk', 'mento', 'irish ballad', 'italian blues', 'estonian metal',
              'muzica banateana', 'piada', 'dytyachi pisni', 'classical trombone', 'italian progressive metal',
              'appalachian black metal', 'zither', 'hangoskonyvek', 'swiss experimental', 'metal salvadoreno',
              'guggenmusik', 'izvorna muzika', 'experimental percussion', 'dark black metal', 'bikutsi',
              'tanzorchester', 'lok dohori', 'american classical piano', 'singaporean punk', 'anime game',
              'eletronica underground brasileira', 'italian modern prog', 'salon music', 'classical accordion',
              'iranian experimental', 'thrash-groove metal', 'polish classical piano', 'kikuyu pop', 'chilean techno',
              'hungarian black metal', 'kolo', 'welsh choir', 'bulgarian metal', 'edinburgh metal', 'dogri pop',
              'guatemalan indie', 'dutch baroque', 'czsk black metal', 'quebec metal', 'borneo traditional',
              'rozpravky', 'vintage radio show', 'alabama hardcore', 'kikuyu gospel', 'moravian folk',
              'experimental big band', 'macedonian rock', 'dutch experimental', 'norwegian choir', 'musique soninke',
              'orquesta cubana', 'chinese wind', 'pipa', 'cerkes muzikleri', 'rakugo', 'delaware indie',
              'sardinia indie', 'punk ecuatoriano', 'tulum', 'african metal', 'autoharp', 'assamese hip hop',
              'musique ancienne', 'kapa haka', 'classic nz country', 'croatian electronic', 'rock dominicano',
              'indie asturiana', 'musica blumenauense', 'stubenmusik', 'synthetic classical', 'rock in opposition',
              'frafra', 'field recording', 'ceske chvaly', 'middle eastern traditional', 'albanian folk',
              'vintage hawaiian', 'deep indie singer-songwriter', 'detskie rasskazy', 'chinese punk',
              'rock pernambucano', 'blues band', 'christian doom metal', 'spanish death metal', 'santur',
              'folklore panameno', 'early french punk', 'italian soprano', 'mapouka', 'deep italo disco',
              'rock catarinense', 'french experimental rock', 'serbian metal', 'rongmei pop', 'black noise', 'ceilidh',
              'caucasian folk', 'russian thrash metal', 'sound collage', 'irish experimental electronic',
              'indonesian thrash metal', 'haitian traditional', 'slovak metal', 'gwoka', 'indie queretano',
              'metalcore espanol', 'belgian hardcore', 'korean traditional', 'malaysian hardcore', 'lithuanian metal',
              'italian baritone', 'ukrainian choir', 'shehnai', 'german contemporary classical',
              'finnish contemporary classical', 'musica mato-grossense', 'beat poetry', 'brazilian heavy metal',
              'deep swedish rock', 'belgian experimental', 'macau pop', 'kosovan folk', 'djembe',
              'instrumental black metal', 'alpenpanorama', 'baroque singing', 'slash punk', 'musica amapaense',
              'trombone brasileiro', 'pontianak indie', 'african experimental', 'suomisaundi', 'vapor house',
              'dweilorkest', 'indie nica', 'nordic orchestra', 'electroacoustic composition', 'musica acoriana',
              'saxony metal', 'ladakhi pop', 'normal indie', 'alaska hip hop', 'mexican power metal',
              'musica campineira', 'bandura', 'lincoln ne indie', 'soda pop', 'danish choir', 'guqin', 'recorder',
              'vintage classical singing', 'british electroacoustic', 'georgian polyphony',
              'latin american classical piano', 'spanish stoner rock', 'humour francais', 'chill groove',
              'historic classical performance', 'antilliaanse folklore', 'bohol indie', 'idaho hip hop',
              'cimbalova muzika', 'theremin', 'deep surf music', 'luxembourgian metal', 'dutch idol pop',
              'deep hardcore punk', 'kantele', 'turkish black metal', 'french contemporary classical',
              'modern performance', 'brazilian post-rock', 'musica rondoniense', 'deep space rock', 'charred death',
              'rock sul-mato-grossense', 'moorish traditional', 'organetto', 'punk tico', 'bury st edmunds indie',
              'orkney and shetland folk', 'string orchestra', 'h8000', 'latin american baroque', 'tan co',
              'south borneo indie', 'modern free jazz', 'italian rockabilly', 'classical bass', 'russian modern jazz',
              'taiwan graduation song', 'brazilian surf rock', 'czech classical piano', 'tibetan folk pop',
              'aghani lil-atfal', 'jazz composition', 'hip hop mauritanien', 'classical bassoon', 'karntner volksmusik',
              'gayageum', 'gong', 'esperanto', 'new england experimental', 'glass', 'italian occult psychedelia',
              'malaysian traditional', 'czech jazz', 'indie catracho', 'folclore extremeno', 'brazilian grindcore',
              'italian baroque ensemble', 'extratone', 'indie tucumano', 'naturjodel', 'rock abc paulista',
              'neo-trad doom metal', 'austrian choir', 'musica londrinense', 'rabm', 'polish noise rock',
              'jazz caraibes', 'marsmuziek', 'musica caririense', 'lithuanian jazz', 'metal galego', 'russian screamo',
              'somatik techno', 'icelandic choir', 'belfast metal', 'chaotic black metal', 'zohioliin duu',
              'greek clarinet', 'gospel papiamento', 'classical oboe', 'vintage old-time', 'italian bass', 'proto-rap',
              'jota aragonesa', 'liberian pop', 'vintage gospel', 'jazz boliviano', 'irish experimental',
              'danish contemporary classical', 'german grindcore', 'skiffle', 'chakma pop', 'polish metalcore',
              'taiwan experimental', 'hipco', 'deep active rock', 'turkmen hip hop', 'indian techno',
              'egyptian traditional', 'folclore navarra', 'romanian contemporary classical', 'cimbalom',
              'belfast indie', 'historic orchestral performance', 'contra dance', 'flashcore', 'czech swing',
              'austrian classical piano', 'mexican electronic', 'latvian metal', 'folklore quebecois',
              'french orchestra', 'lion city hardcore', 'zomi pop', 'orkiestra symfoniczna', 'landler', 'hard chime',
              'metal cristao', 'magyar kabare', 'thai traditional', 'swazi hip hop', 'deep pop emo', 'cante alentejano',
              'cryptic black metal', 'czech psychedelic', 'spanish black metal', 'italian industrial', 'band organ',
              'afrikaans folk', 'moroccan traditional', 'rock paraense', 'thai psychedelic', 'ethnomusicology',
              'ainu folk', 'northumbrian folk', 'deep orgcore', 'karelian folk', 'italian classical guitar',
              'mexican black metal', 'portuguese post-rock', 'rap paraense', 'viola', 'nadaswaram',
              'italian heavy metal', 'korean minyo', 'gypsy', 'classical piano trio', 'minnesang', 'classical tuba',
              'rap burkinabe', 'baltic black metal', 'maldivian pop', 'czech hardcore', 'musica piemonteisa',
              'indonesian black metal', 'musique traditionnelle congolaise', 'metal paraguayo', 'french rockabilly',
              'portuguese hardcore', 'palm wine guitar', 'frevo', 'korean hardcore', 'experimental dubstep',
              'baltic choir', 'musica roraimense', 'baoule', 'metal uruguayo', 'ethiopian traditional',
              'post-rock latinoamericano', 'fife and drum', 'metal balear', 'classical guitar duo', 'troubadour',
              'spoken word', 'portuguese early music', 'persian poetry', 'italian orchestra', 'song poem',
              'boy soprano', 'korean contemporary classical', 'deep indie rock', 'appenzeller folk',
              'indie nordeste argentino', 'deep neo-synthpop', 'kadongo kamu', 'irish death metal', 'metal catarinense',
              'central american metal', 'turkish hardcore', 'animal singing', 'trombone ensemble', 'tatar folk',
              'metal cearense', 'baltic classical piano', 'marathi balgeet', 'deep southern soul', 'balochi folk',
              'pansori', 'dizi', 'brazilian classical piano', 'musique traditionnelle comorienne', 'inuit traditional',
              'south african techno', 'lagu jambi', 'sarangi', 'euphonium', 'spanish contemporary classical',
              'experimental poetry', 'rock nacional feminino', 'yiddish folk', 'accordion band', 'musica sinfonica',
              'trecento', 'sacred harp', 'portuguese experimental', 'deep r&b', 'polish experimental',
              'grunge argentina', 'akordeon', 'hard dance', 'metal baiano', 'harmonikka', 'black metal argentino',
              'kamba pop', 'ghanaian traditional', 'taarab', 'nordnorsk ponk', 'industrial noise', 'hard stoner rock',
              'venezuelan metal', 'traditional irish singing', 'luxembourgian electronic', 'malaysian post-rock',
              'chinese black metal', 'santa fe indie', 'malian traditional', 'grunge brasileiro', 'kazakh traditional',
              'vietnamese traditional', 'tanzanian traditional', 'classical guitar quartet', 'deep delta blues',
              'ethereal gothic', 'maltese metal', 'estonian jazz', 'historical keyboard', 'jaw harp', 'irish hardcore',
              'musica puntana', 'alphorn', 'alternative hardcore', 'deep latin jazz', 'classical contralto',
              'bulgarian experimental', 'trouvere', 'classical piano duo', 'deep chill-out', 'punk ska', 'police band',
              'czech contemporary classical', 'balkan classical piano', 'uyghur folk', 'swedish jazz orkester',
              'jewish cantorial', 'musica urbana oaxaquena', 'school choir', 'ars subtilior', 'necrogrind',
              'musique tchadienne', 'montana metal', 'irish modern jazz', 'cypriot metal', 'portuguese classical',
              'australian choir', 'ghoststep', 'new zealand classical', 'iranian metal', 'puerto rican metal',
              'indonesian electronic', 'canto a tenore', 'chilean black metal', 'lagu lampung', 'bells',
              'south african dnb', 'jangle rock', 'huqin', 'romanian classical piano', 'peruvian death metal',
              'brazilian doom metal', 'deep indie pop', 'art song', 'metis fiddle', 'classical horn',
              'central asian folk', 'rock cristao fluminense', 'pygmy music', 'shantykoren', 'cosmic uplifting trance',
              'hawaiian punk', 'deep motown', 'pibroch', 'russian oi', 'caribbean metal', 'school ensemble',
              'twee indie pop', 'vanuatu music', 'horo', 'tahitian traditional', 'metal nortista', 'handbells',
              'polish early music', 'musica ponta-grossense', 'schrammelmusik', 'indie tabasqueno',
              'metal pernambucano', 'classical saxophone quartet', 'czech experimental', 'deep symphonic black metal',
              'musica mogiana', 'opera chorus', 'albanian iso polyphony', 'drone psych', 'draaiorgel', 'sirmauri pop',
              'twin cities indie', 'austrian contemporary classical', 'clarinet ensemble', 'baroque woodwind',
              'indonesian indigenous traditional', 'burkinabe traditional', 'musica maringaense', 'harsh noise wall',
              'chip hop', 'swiss contemporary classical', 'modern downshift', 'polish choir', 'baroque violin',
              'lagu madura', 'deep smooth r&b', 'trad jazz catala', 'dark electro-industrial', 'kaba gaida',
              'rock noise', 'wagnerian singing', 'indie emo rock', 'peruvian experimental', 'musique alsacienne',
              'cantonese traditional', 'belgian classical piano', 'deep power-pop punk', 'deep deep tech house',
              'rwandan traditional', 'kyrgyz traditional', 'burmese traditional', 'chinese opera',
              'burundian traditional', 'baroque cello', 'cambodian traditional', 'vintage swoon',
              'musique centrafricaine', 'faroese jazz', 'bruneian indie', 'korean classical piano',
              'vintage rockabilly', 'rhythm and boogie', 'marci brijuzi', 'papuan traditional', 'macedonian metal',
              'lao traditional', 'gay chorus', 'wind quintet', 'polish free jazz', 'deep breakcore', 'tanci',
              'balikpapan indie', 'uzbek traditional', 'musica timor-leste', 'italian violin', 'wandelweiser',
              'bothy ballad', 'metal piauiense', 'kenyan traditional', 'quatuor a cordes', 'italian choir', 'zampogna',
              'ugandan traditional', 'yemeni traditional', 'tajik traditional', 'wind ensemble', 'hungarian choir',
              'swiss classical piano', 'mazandarani folk', 'historic string quartet', 'italian mezzo-soprano',
              'swazi traditional', 'trallalero', 'baroque brass', 'himene tarava', 'vintage western',
              'classical string trio', 'cinematic dubstep', 'quartetto d\'archi', 'yunnan traditional',
              'classical piano quartet', 'string quintet', 'youth orchestra']

    random_genre = random.choice(genres)
    results = sp.search(q=f'genre:"{random_genre}"', type='track', limit=50)
    tracks = results['tracks']['items']

    if not tracks:
        print("No tracks found.")
        return

    random_track = random.choice(tracks)
    track_uri = random_track['uri']
    sp.add_to_queue(uri=track_uri)


def adding_thread(num):
    for i in range(num):
        add_random_track_to_queue()


def get_random_queue_input(user_input, frame):
    destroy_frame(frame)
    user_input_to_int = int(user_input)
    processing_frame(adding_thread, user_input_to_int)
    to_destroy = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    finished_frame()
    restart(to_destroy)
    pass


def random_queue(frame):
    destroy_frame(frame)
    input_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    input_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(input_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)
    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)
    buttons_text = ["My Profile", "How to Use", "Change Config", "Return"]
    buttons_x = [355, 509, 677, 844]
    buttons_command = [my_profile, how_to_use, lambda: change_config, lambda: restart(input_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0, text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    middle_frame = ctk.CTkFrame(input_frame, fg_color='#000000', bg_color='#000000', border_width=0, border_color='#000000', width=1000, height=888)
    middle_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    queue_label = ctk.CTkLabel(middle_frame, text="How many tracks do you want to\nadd to queue?", font=("Roboto", 44, 'bold'), text_color="#FFFFFF", width=700, height=157, anchor='center')
    queue_label.place(x=150, y=75)

    user_input = ctk.CTkEntry(input_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20), width=400, height=50)
    user_input.place(x=300, y=400)
    user_input.bind('<KeyRelease>', lambda event: update_slider(event, slider))
    user_input.insert(0, 50)
    slider = ctk.CTkSlider(input_frame, from_=1, to=100, number_of_steps=99, command=lambda value: slider_activity(value, input_frame, user_input), width=400, height=40, fg_color='#2e2e2e', bg_color='#000000', button_hover_color='#FFFFFF', button_color='#FFFFFF', progress_color='light grey')
    slider.place(relx=0.5, rely=0.6, anchor='center')
    submit_button = ctk.CTkButton(input_frame, text="Submit", command=lambda: get_random_queue_input(user_input.get(), input_frame), width=227, height=64, fg_color='#FFFFFF', bg_color='#000000', border_width=0, text_color="#000000", font=("Roboto", 20, "bold"))
    submit_button.place(x=386, y=750)

    pass


def slider_activity(value, input_frame, user_input):
    user_input.delete(0, 'end')
    user_input.insert(0, int(value))


def update_slider(event, slider):
    value = event.widget.get()
    if value.isdigit():
        slider.set(int(value))


def get_config(start):
    config_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    config_frame.pack()
    top_frame = ctk.CTkFrame(config_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.BOTH)

    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)

    buttons_text = ["My Profile", "How to Use", "Change Config"]
    buttons_x = [357, 562, 758]
    buttons_command = [my_profile, how_to_use, change_config]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0, text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    middle_frame = ctk.CTkFrame(config_frame, fg_color='#000000', bg_color='#000000', border_width=0, border_color='#000000', width=1000, height=888)
    middle_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    configurator_label = ctk.CTkLabel(middle_frame, text="Configurator", font=("Roboto", 48, "bold"),
                                      text_color="#FFFFFF", width=200, height=50)
    configurator_label.pack_propagate(0)
    configurator_label.pack(pady=(30, 0))

    client_id_label = ctk.CTkLabel(middle_frame, text="Enter your client id", font=("Roboto", 40), text_color="#FFFFFF", anchor='w')
    client_id_label.pack(padx=51, pady=(173-30, 0), anchor='w')

    client_secret_label = ctk.CTkLabel(middle_frame, text="Enter your client id", font=("Roboto", 40), text_color="#FFFFFF", anchor='w')
    client_secret_label.pack(padx=51, pady=(125, 0), anchor='w')

    client_id_label = ctk.CTkLabel(middle_frame, text="Enter your client id", font=("Roboto", 40), text_color="#FFFFFF", anchor='w')
    client_id_label.pack(padx=51, pady=(125, 0), anchor='w')

    client_id_entry = ctk.CTkEntry(middle_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0,
                                   text_color="#000000", font=("Roboto", 20), width=417, height=75)
    client_id_entry.insert(0, "Client id")
    client_id_entry.place(relx=0.75, rely=0.29, anchor=ctk.CENTER)

    client_secret_entry = ctk.CTkEntry(middle_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0,
                                       text_color="#000000", font=("Roboto", 20), width=417, height=75)
    client_secret_entry.insert(0, "Client secret")
    client_secret_entry.place(relx=0.75, rely=0.48, anchor=ctk.CENTER)

    redirect_uri_entry = ctk.CTkEntry(middle_frame, fg_color='#FFFFFF', bg_color='#000000', border_width=0,
                                      text_color="#000000", font=("Roboto", 20), width=417, height=75)
    redirect_uri_entry.insert(0, "Redirect uri")
    redirect_uri_entry.place(relx=0.75, rely=0.675, anchor=ctk.CENTER)

    submit_button = ctk.CTkButton(middle_frame, text="Submit", fg_color='#FFFFFF', bg_color='#000000', border_width=0,
                                  text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: save_config(client_id_entry.get(), client_secret_entry.get(), redirect_uri_entry.get(), config_frame, start))
    submit_button.pack(side=ctk.BOTTOM, pady=100)

    app.mainloop()
    pass


def setup_multispot():
    lobby_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000')
    lobby_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)
    top_frame = ctk.CTkFrame(lobby_frame, width=1000, height=112, border_width=0, border_color='#000000')
    top_frame.configure(fg_color='#000000', bg_color='#000000')
    top_frame.pack_propagate(0)
    top_frame.pack(side=ctk.TOP, fill=ctk.X)

    ms_label = ctk.CTkLabel(top_frame, text="MultiSpot", font=("Roboto", 48, "bold"), text_color="#FFFFFF")
    ms_label.place(x=63, y=28)

    buttons_text = ["My Profile", "How to Use", "Change Config"]
    buttons_x = [357, 562, 758]
    buttons_command = [my_profile, how_to_use, lambda: change_config(lobby_frame)]

    for i, text in enumerate(buttons_text):
        button = ctk.CTkButton(top_frame, text=text, fg_color='#000000', bg_color='#000000', border_width=0, text_color="#FFFFFF", font=("Roboto", 16), command=buttons_command[i])
        button.place(x=buttons_x[i], y=44)

    middle_frame = ctk.CTkFrame(lobby_frame, fg_color='#000000', bg_color='#000000', border_width=0, border_color='#000000', width=1000, height=888)
    middle_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    task_label = ctk.CTkLabel(middle_frame, text="Select Task", font=("Roboto", 48), text_color="#FFFFFF", width=200, height=50)
    task_label.pack(pady=(50, 0))

    random_queue_button = ctk.CTkButton(middle_frame, text="Random Queue", fg_color='#FFFFFF', bg_color='#000000', text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: random_queue(lobby_frame))
    random_queue_button.place(relx=0.134, rely=0.256)

    track_playlist_button = ctk.CTkButton(middle_frame, text="Track to Playlist", fg_color='#FFFFFF', bg_color='#000000', text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: track_to_playlist(lobby_frame))
    track_playlist_button.place(relx=0.134, rely=0.5)

    queue_set_button = ctk.CTkButton(middle_frame, text="Queue Setter", fg_color='#FFFFFF', bg_color='#000000', text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: queue_setter(lobby_frame))
    queue_set_button.place(relx=0.134, rely=0.75)

    shuffler_button = ctk.CTkButton(middle_frame, text="Playlist Shuffler", fg_color='#FFFFFF', bg_color='#000000', text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: playlist_shuffler(lobby_frame))
    shuffler_button.place(relx=0.866, rely=0.256, anchor='ne')

    recommender_button = ctk.CTkButton(middle_frame, text="Magic Recommender", fg_color='#FFFFFF', bg_color='#000000', text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: magic_recommender(lobby_frame))
    recommender_button.place(relx=0.866, rely=0.5, anchor='ne')

    random_button = ctk.CTkButton(middle_frame, text="Random Activity", fg_color='#FFFFFF', bg_color='#000000', text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64, command=lambda: random_activity(lobby_frame))
    random_button.place(relx=0.866, rely=0.75, anchor='ne')

    app.mainloop()
    pass


def processing_frame(func, args):
    process_fame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000', bg_color='#000000', fg_color='#000000')
    process_fame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    working_label = ctk.CTkLabel(process_fame, text="Work in progress...", font=("Roboto", 64), text_color="#FFFFFF", width=522, height=77, anchor='center')
    working_label.place(x=239, y=116)

    loading_frame = ctk.CTkFrame(process_fame, width=498, height=497, border_width=0, border_color='#000000', bg_color='#000000', fg_color='#000000')
    loading_frame.place(x=251, y=272)
    loading_label = AnimatedGif(loading_frame, 'ezgif-5-08f6354a96.gif', delay=0.04)
    loading_label.pack()
    loading_label.start_thread()

    thread = threading.Thread(target=func, args=(args,))
    thread.start()

    def wait_for_thread():
        thread.join()
        loading_label.stop_thread()
        destroy_frame(process_fame)

    waiting_thread = threading.Thread(target=wait_for_thread)
    waiting_thread.start()


def finished_frame():
    finished_frame = ctk.CTkFrame(app, width=1000, height=1000, border_width=0, border_color='#000000', bg_color='#000000', fg_color='#000000')
    finished_frame.pack(side=ctk.TOP, fill=ctk.BOTH, expand=True)

    finished_label = ctk.CTkLabel(finished_frame, text="Finished!", font=("Roboto", 64), text_color="#FFFFFF", width=522, height=77, anchor='center')
    finished_label.place(x=239, y=116)

    done_frame = ctk.CTkFrame(finished_frame, width=498, height=497, border_width=0, border_color='#000000', bg_color='#000000', fg_color='#000000')
    done_frame.place(x=251, y=272)

    finished_label = AnimatedGif(done_frame, 'orchestrated-orchestratednl.gif', delay=0.04)
    finished_label.pack()
    finished_label.start_thread()

    def on_button_click():
        finished_label.stop_thread()
        destroy_frame(finished_frame)
        app.quit()

    def on_quit_button_click():
        finished_label.stop_thread()
        destroy_frame(finished_frame)
        app.quit()
        app.quit()
        quit()

    continue_button = ctk.CTkButton(finished_frame, text="Continue", fg_color='#FFFFFF', bg_color='#000000',
                                    text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64,
                                    command=on_button_click)
    continue_button.place(x=100, y=750)

    quit_button = ctk.CTkButton(finished_frame, text="Quit", fg_color='#FFFFFF', bg_color='#000000',
                                    text_color="#000000", font=("Roboto", 20, "bold"), width=227, height=64,
                                    command=on_quit_button_click)
    quit_button.place(x=673, y=750)
    app.mainloop()

ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

config_file = 'config.sg'
config = configparser.ConfigParser()

# ctk.set_default_color_theme("DaynNight.json")
app = ctk.CTk()
app.title('MultiSpot')
app.geometry('1000x1000+0+0')
app.protocol('WM_DELETE_WINDOW', end_all)
app.configure(background='#000000', bg='#000000', fg_color='#000000', bg_color='#000000')
app.resizable(False, False)


if not os.path.exists(config_file):
    get_config(True)
else:
    load_config(True)


# Autoryzacja
scope = 'playlist-read-private user-modify-playback-state playlist-modify-public playlist-modify-private user-top-read'
auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)
sp = spotipy.Spotify(auth_manager=auth_manager)

setup_multispot()
