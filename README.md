# Telegram Movie Preview Bot

A Telegram bot for browsing and viewing movie previews with IMDb ratings and descriptions.

## Features

- **Channel Subscription**: Users must join a required channel before using the bot
- **Movie Preview**: Browse, search, and watch movie previews (10-second auto-delete feature)
- **IMDb Ratings**: Sort movies by IMDb ratings
- **Search Functionality**: Search for movies by title

## Commands

- `/start` - Begin interaction with the bot
- `/search` - Search for movies by title
- `/bestmovies` - Show the top-rated movies based on IMDb scores

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/amirhosseinzolfi/blue-movie.git
   cd blue-movie
   ```

2. Create a virtual environment:
   ```
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your bot token:
   - Get a bot token from [@BotFather](https://t.me/BotFather)
   - Update the `TOKEN` variable in the code or use environment variables

5. Run the bot:
   ```
   python bot.py
   ```

## Configuration

You can customize:
- Movie data (titles, descriptions, preview URLs)
- Required subscription channels
- Preview display time

## License

This project is open-source and available under the MIT License.
