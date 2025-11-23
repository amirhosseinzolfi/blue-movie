# Telegram Movie Preview Bot

A Telegram bot for browsing and viewing movie previews with IMDb ratings and descriptions.

## Features

- **Channel Subscription**: Users must join a required channel before using the bot
- **Movie Preview**: Browse, search, and watch movie previews with detailed information
- **IMDb Ratings**: Sort movies by IMDb ratings
- **Search Functionality**: Search for movies by title
- **File Server**: Built-in HTTP server for efficient movie file streaming
- **Rich Logging**: Comprehensive logging with Rich formatting for debugging

## Commands

- `/start` - Begin interaction with the bot
- `/search` - Search for movies by title
- `/bestmovies` - Show the top-rated movies based on IMDb scores

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/amirhosseinzolfi/blue-movie.git
   cd blue-movie
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your configuration:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   SERVER_HOST=your_server_ip
   SERVER_PORT=8004
   REQUIRED_CHANNEL=https://t.me/your_channel_name
   ```

5. Run the bot:
   ```bash
   python bot.py
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- `SERVER_HOST` - IP address or hostname of your file server
- `SERVER_PORT` - Port for the file server (default: 8004)
- `REQUIRED_CHANNEL` - Telegram channel URL that users must join

### Movie Database

Movies are stored in `movie_database.json`. Each movie entry includes:
- Title, year, genre, director, cast
- Duration, language, quality options
- IMDb rating and description
- Download link and cover image path

## Project Structure

```
blue-movie/
├── bot.py                 # Main bot application
├── logger_config.py       # Rich logging configuration
├── movie_database.json    # Movie database
├── movies/                # Movie files and covers
│   ├── movies cover/      # Movie cover images
│   └── *.mkv/*.mp4        # Movie files
├── .env                   # Environment variables (not in git)
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── .gitignore             # Git ignore rules
```

## Security

- **Credentials**: All sensitive data (bot token, server config) is stored in `.env` file
- **Git Safety**: `.env` file is excluded from version control via `.gitignore`
- **Environment Variables**: Use `.env.example` as a template for configuration

## Logging

The bot uses Rich library for beautiful, structured logging:
- Console output with color-coded messages
- File logging to `bot.log`
- Separate logging for user actions, movie operations, and server events

## File Server

The bot includes a built-in HTTP file server for efficient movie streaming:
- Serves files from the `movies/` directory
- Supports concurrent downloads with threading
- Optimized for large file transfers (64MB chunks)
- Automatic Content-Disposition headers for downloads

## Troubleshooting

### Bot not responding
- Check that `TELEGRAM_BOT_TOKEN` is correctly set in `.env`
- Verify bot is running: `python bot.py`
- Check `bot.log` for error messages

### Users can't access movies
- Ensure users are subscribed to the required channel
- Verify `REQUIRED_CHANNEL` is correctly set in `.env`
- Check file server is running on the correct port

### File server not accessible
- Verify `SERVER_HOST` and `SERVER_PORT` in `.env`
- Check firewall allows connections on the specified port
- Ensure movie files exist in `movies/` directory

## License

This project is open-source and available under the MIT License.

## Support

For issues and questions, please open an issue on the GitHub repository.
