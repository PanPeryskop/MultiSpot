# MultiSpot

MultiSpot is a Python application that combines the functionalities of my few Spotify-related projects into one tool. It allows Spotify users to manage their music in various ways, such as creating a playlist based on their top tracks, adding random tracks to their queue,  and more. The application uses the Spotify API to interact with user's Spotify data.

This project combines my following repositories:

- [SpotiQueue](https://github.com/PanPeryskop/SpotiQueue)
- [RandomQueue](https://github.com/PanPeryskop/RandomQueue)
- [Track-to-Playlist](https://github.com/PanPeryskop/Track-to-Playlist)
- [Magic-Recommender](https://github.com/PanPeryskop/Magic-Recommender)

In addition to the features provided by these projects, MultiSpot also includes some additional functionalities.

## Resources used
- Spotipy
- Customtkinter
- [AnimatedGIF](https://github.com/olesk75/AnimatedGIF)
- [DayNight theme](https://github.com/s-liwka/customtkinter-themes/tree/main/themes)


## Features

- Generate a playlist based on the user's top tracks
- Generate a playlist based on track
- Add several playlists to queue
- Add random tracks to the user's queue
- Shuffle user's and not user's playlists

## Before you install

Before you can use MultiSpot, you need to create a Spotify Developer application to get your `client_id`, `client_secret`, and `redirect_uri`. Here's how you can do it:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Log in with your Spotify account.
3. Click on 'Create an App'.
4. Fill in the 'Name', 'Description' and redirect_uri (I recommend using http://localhost:3000/) for your new app, then click 'Create'.
5. On the next page, you will see your `client_id` and `client_secret`. You will need these to authenticate your application.
6. Click on 'Edit Settings'.
7. In the 'Redirect URIs' field, enter the URI where you want Spotify to redirect you after a successful login.
8. Click 'Save'.

## Installation

1. Make sure you have Python 3.9 or later installed. If not you can download it from the [official website](https://www.python.org/downloads/). Make sure to add python to PATH during installation.
2. Clone the repository or download the ZIP file and extract it.
2. Open the MultiSpot folder.
3. Run setup.bat file to install required packages.
    

## Usage
1. Open folder in cmd and type python.exe main.py or open run.bat file in MultiSpot folder (If it doesn't work, modify bat file in notepad and change python.exe to direct path to your python.exe)
2. The application will ask you to enter your `client_id`, `client_secret`, and `redirect_uri`. Enter the values from the Spotify Developer Dashboard.
3. Select desired action from the menu.

*More detailed instruction are available in the [WIKI](https://github.com/PanPeryskop/MultiSpot/wiki/How-to-Use)*

Enjoy your music!