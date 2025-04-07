Telegram Movie Downloader Bot
================================

Description:
-------------
This is a Telegram bot that allows users to download movie previews.
Before using the bot, users must join a required channel. Once subscribed,
users get access to a selection of movies, can search among available movies,
and view the top rated movies based on the IMDb score.

Features:
-----------
1. Channel Subscription:
   - On /start, the bot instructs the user (in Persian) to subscribe to a fixed channel.
   - The user sees a “Join Channel” button and a “Member” button.
   - The bot checks whether the user has joined before enabling further commands.

2. Movie Selection:
   - Once membership is confirmed, the bot displays available movies with a Persian and emojified interface.
   - Selecting a movie shows detailed information including its IMDb rating, description, and preview video.

3. Commands:
   - /start: Launches the bot and prompts for channel subscription.
   - /search: Users can search for movies by name. (Example usage: "/search داستان")
     (Persian explanation is provided in response messages.)
   - /bestmovies: Displays a list of movies sorted by IMDb rating.
     (Persian explanation is provided in response messages.)

Usage:
-------
1. Install Python 3.8 or later.
2. Install dependencies using the provided requirements.txt file.
3. Run the bot script: python bot.py
4. Interact with the bot in Telegram by sending /start and following the on-screen instructions.

Configuration:
---------------
- Edit TOKEN in bot.py with your actual bot token.
- Update MOVIES dictionary with actual movies (URLs, ratings, descriptions).
- Adjust FIXED_CHANNEL_URL and FIXED_CHANNEL_USERNAME as needed.

Notes:
-------
The user interface messages are emojified and provided in Persian to enhance user experience.
Commands use English aliases (/search, /bestmovies) with Persian explanations in responses.

Enjoy your movie previews experience!
