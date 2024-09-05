import customtkinter as tk
from customtkinter import CTkImage
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from PIL import Image
from io import BytesIO
import time
import threading
import os
import configparser

playlist_count = None
current_url = None
playlist_frame = None
selected_playlist = None
is_from_profile = []


def prepere_display(select_frame):
    global playlist_frame
    playlist_frame = tk.CTkFrame(app, fg_color='#000000', bg_color='#000000')
    
    playlist_frame.pack(fill=tk.BOTH, expand=True)

    disp_playlists(select_frame)

def get_user_input(input_frame):
    
    s_label = tk.CTkLabel(master=input_frame, text="How many playlists do you want to add?", font=("Roboto", 18, "bold"), text_color="#FFFFFF", bg_color='#000000')
    s_label.pack(pady=(30, 0), anchor='s')
    user_input = tk.CTkEntry(input_frame, fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
    user_input.pack(pady=15)
    user_input.bind('<KeyRelease>', lambda event: update_slider(event, slider))
    slider = tk.CTkSlider(input_frame, from_=1, to=15, number_of_steps=14, command=lambda value: slider_activity(value, input_frame, user_input), fg_color='#2e2e2e', bg_color='#000000', button_hover_color='#FFFFFF', button_color='#FFFFFF', progress_color='light grey')
    slider.pack(pady=15)
    submit_button = tk.CTkButton(input_frame, text="Submit", command=lambda: process_user_input(user_input.get(), user_input, submit_button), fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
    submit_button.place(relx=0.5, rely=0.5, anchor='center')
    app.mainloop()

def slider_activity(value, input_frame, user_input):
    user_input.delete(0, 'end')
    user_input.insert(0, int(value))

def update_slider(event, slider):
    value = event.widget.get()
    if value.isdigit():
        slider.set(int(value))

def process_user_input(input, user_input, submit_button):
    global playlist_count
    if input.isdigit():
        playlist_count = int(input)
        user_input.destroy()
        submit_button.destroy()
        app.quit()
    else:
        error_label = tk.CTkLabel(app, text="Please enter a number.", text_color="#FFFFFF")
        error_label.pack()
        app.after(5000, error_label.destroy)

def disp_playlists(select_frame):
    global prev_button, next_button, current_page, images, playlist_frame
    select_frame.destroy()
    playlist_frame.pack()

    if 'prev_button' not in globals():
        prev_button = tk.CTkButton(app, text="<", command=prev_page, fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
        prev_button.pack(side="left")
    if 'next_button' not in globals():
        next_button = tk.CTkButton(app, text=">", command=next_page, fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
        next_button.pack(side="right")

    current_page = 0
    images = []
    update_page()

def get_url(select_frame):
    global is_from_profile
    is_from_profile.append(False)
    select_frame.destroy()
    url = tk.CTkEntry(app, fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
    url.place(relx=0.5, rely=0.4, anchor='center')
    submit_button = tk.CTkButton(app, text="Submit", command=lambda: process_url(url.get(), url, submit_button), fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
    submit_button.place(relx=0.5, rely=0.5, anchor='center')

def process_url(input, url, submit_button):
    if input.startswith("https://open.spotify.com/"):
        global current_url
        current_url = input
        url.destroy()
        submit_button.destroy()
        app.quit()
    else:
        error_label = tk.CTkLabel(app, text="Please enter a valid URL.", text_color="#000000")
        error_label.pack()
        app.after(5000, error_label.destroy)


def select_source():
    select_frame = tk.CTkFrame(app, fg_color='#000000', bg_color='#FFFFFF')
    select_frame.pack(pady=20, padx=60, fill="both", expand=True)
    s_label = tk.CTkLabel(master=select_frame, text="Select source", font=("Roboto", 18, "bold"), text_color="#FFFFFF")
    s_label.pack(pady=(30, 0), anchor='s')
    playlists_frame = tk.CTkFrame(app, fg_color='#FFFFFF', bg_color='#000000')
    profile_button = tk.CTkButton(select_frame, text="From Profile", command=lambda: [prepere_display(select_frame)], fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
    profile_button.place(relx=0.025, rely=0.5, relwidth=0.45)
    url_button = tk.CTkButton(select_frame, text="From URL", command=lambda: get_url(select_frame), fg_color='#FFFFFF', bg_color='#000000', text_color="#000000")
    url_button.place(relx=0.55-0.025, rely=0.5, relwidth=0.45)
    app.mainloop()


def next_page():
    global current_page, playlist_frame
    if playlist_frame is None:
        playlist_frame = tk.CTkFrame(app, fg_color='#FFFFFF', bg_color='#000000')
        playlist_frame.pack()
    if current_page < len(pages) - 1:
        current_page += 1
        update_page()


def prev_page():
    global current_page, playlist_frame
    if playlist_frame is None:
        playlist_frame = tk.CTkFrame(app)
        playlist_frame.pack()
    if current_page > 0:
        current_page -= 1
        update_page()


def get_playlist_from_profile(playlist_url):
    global current_url, is_from_profile, playlist_frame
    if playlist_frame is not None:
        for widget in playlist_frame.winfo_children():
            widget.destroy()
        playlist_frame.pack_forget()

    if 'prev_button' in globals() and prev_button is not None:
        prev_button.pack_forget()
    if 'next_button' in globals() and next_button is not None:
        next_button.pack_forget()

    is_from_profile.append(True)
    current_url = playlist_url
    app.quit()


def update_page():
    global images, playlist_frame

    if playlist_frame.winfo_exists():
        for widget in playlist_frame.winfo_children():
            widget.destroy()

        images = []

        for playlist in pages[current_page]:
            playlist_url = playlist['external_urls']['spotify']
            image_url = playlist['images'][0]['url']
            response = requests.get(image_url)
            img_data = response.content

            img = Image.open(BytesIO(img_data))
            name = playlist['name'][:20]

            photo = CTkImage(img)
            images.append(photo)

            playlist_button = tk.CTkButton(playlist_frame, image=photo, text=name, anchor="w", command=lambda playlist_url=playlist_url: get_playlist_from_profile(playlist_url), fg_color='#000000', bg_color='#000000', text_color="#FFFFFF") 
            playlist_button.pack(fill="x")

        if current_page > 0:
            prev_button["state"] = "normal"
        else:
            prev_button["state"] = "disabled"
        if current_page < len(pages) - 1:
            next_button["state"] = "normal"
        else:
            next_button["state"] = "disabled"
        app.update_idletasks()


def get_tracks_from_playlist(playlist_url, from_profile, index):
    if from_profile[index] is True:
        playlist_id = playlist_url.split('/')[-1]
    else:
        playlist_id = playlist_url.split('/')[-1].split('?')[0]
    results = sp.playlist_items(playlist_id)
    track_ids = [item['track']['id'] for item in results['items']]
    return track_ids


def set_queue(playlist_arr):
    queue_arr = []
    max_arr = max(playlist_arr, key=len)
    max_length = len(max_arr)
    for i in range (max_length):
        for j in range(len(playlist_arr)):
            if i < len(playlist_arr[j]):
                queue_arr.append(playlist_arr[j][i])
    return queue_arr


def add_to_queue_fixed(sp, track_id, device_id=None):
    while True:
        try:
            sp.add_to_queue(track_id, device_id)
            break
        except spotipy.exceptions.SpotifyException as e:
            if e.http_status == 429:
                wait_time = int(e.headers.get('Retry-After', 1))
                time.sleep(wait_time)
            else:
                raise


def queue_setter(queue_arr):
    for i in range(len(queue_arr)):
        add_to_queue_fixed(sp, queue_arr[i], device_id=None)
    # s_label.destroy()


def go_to_set_queue(playlist_count, list_of_playlists, is_from_profile):
    playlist_arr = []
    for i in range(playlist_count):
        playlist_arr.append(get_tracks_from_playlist(list_of_playlists[i], is_from_profile, i))
    queue_arr = set_queue(playlist_arr)
    queue_setter(queue_arr)

    app.after(0, s_label.destroy)
    app.after(0, create_end_label)


def create_end_label():
    end_label = tk.CTkLabel(master=app ,text="Enjoy your music!", font=("Roboto", 18, "bold"), text_color="green")
    end_label.place(relx=0.5, rely=0.5, anchor='center')
    app.after(5000, app.quit)


def get_user_input_config():
    input_frame = tk.CTkFrame(app, fg_color='#000000', bg_color='#000000')
    input_frame.pack(fill=tk.BOTH, expand=True)

    client_id_label = tk.CTkLabel(input_frame, text="Enter your client_id:", font=("Roboto", 16, "bold"), text_color="white")
    client_id_label.pack(pady=(40, 0))
    client_id_entry = tk.CTkEntry(input_frame)
    client_id_entry.pack(pady=5)

    client_secret_label = tk.CTkLabel(input_frame, text="Enter your client_secret:", font=("Roboto", 16, "bold"), text_color="white")
    client_secret_label.pack(pady=(30, 0))
    client_secret_entry = tk.CTkEntry(input_frame)
    client_secret_entry.pack(pady=5)

    redirect_uri_label = tk.CTkLabel(input_frame, text="Enter your redirect_uri:", font=("Roboto", 16, "bold"), text_color="white")
    redirect_uri_label.pack(pady=(30, 0))
    redirect_uri_entry = tk.CTkEntry(input_frame)
    redirect_uri_entry.pack(pady=5)

    submit_button = tk.CTkButton(input_frame, text="Submit", font=("Roboto", 10), text_color="white", command=lambda: process_user_input_config(client_id_entry.get(), client_secret_entry.get(), redirect_uri_entry.get(), input_frame))
    submit_button.place(relx=0.5, rely=0.9, anchor='s')
    app.mainloop()


def end_all():
    app.quit()
    quit()


app = tk.CTk()
app.title("Queue Setter")
app.geometry("420x600")
app.protocol("WM_DELETE_WINDOW", end_all)
app.configure(background='#000000', bg='#000000', fg_color='#000000', bg_color='#000000')



#Dane autoryzacyjne
config_file = 'config.sg'
config = configparser.ConfigParser()

config.read(config_file)
client_id = config.get('Spotify', 'client_id')
client_secret = config.get('Spotify', 'client_secret')
redirect_uri = config.get('Spotify', 'redirect_uri')

# Autoryzacja
scope = 'playlist-read-private user-modify-playback-state'
auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope)
sp = spotipy.Spotify(auth_manager=auth_manager)

playlists = sp.current_user_playlists()['items']
playlists_per_page = 15
pages = [playlists[i:i + playlists_per_page] for i in range(0, len(playlists), playlists_per_page)]

input_frame = tk.CTkFrame(app, fg_color='#000000', bg_color='#000000')
input_frame.pack(fill=tk.BOTH, expand=True)

get_user_input(input_frame)

input_frame.destroy()

if playlist_count > 0:
    list_of_playlists = [None]*playlist_count
    current_playlist = 0
    while current_playlist < playlist_count:
        select_source()
        list_of_playlists[current_playlist] = current_url
        current_playlist += 1
        if playlist_frame is not None:
            for widget in playlist_frame.winfo_children():
                widget.destroy()
            playlist_frame.pack_forget()

        if 'prev_button' in globals() and prev_button is not None:
            prev_button.pack_forget()
        if 'next_button' in globals() and next_button is not None:
            next_button.pack_forget()

    s_label = tk.CTkLabel(master=app ,text="Setting your queue", font=("Roboto", 20, "bold"), text_color="cyan")
    s_label.place(relx=0.5, rely=0.5, anchor='center')

    thread = threading.Thread(target=go_to_set_queue, args=(playlist_count, list_of_playlists, is_from_profile))
    thread.start()

    app.mainloop()
else:
    ending_label = tk.CTkLabel(master=app, text="No playlists to add", font=("Roboto", 20, "bold"), text_color="red")
    ending_label.pack(pady=(30, 0), anchor='s')
    time.sleep(5)
    app.quit()
