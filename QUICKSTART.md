# Quick Start Guide

Get up and running with the Epic Games Free Games Notifier in 5 minutes.

## Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## First Run

Run the script to see current and upcoming free games:

```bash
python run.py
```

Example output:
```
############################################################
# CURRENTLY FREE GAMES
############################################################

============================================================
Title: Hogwarts Legacy
Publisher: Warner Bros. Games
Status: ACTIVE
Description: Hogwarts Legacy is an immersive, open-world action RPG...
Store URL: https://store.epicgames.com/en-US/p/hogwarts-legacy
Available From: 2025-11-11 16:00 UTC
Available Until: 2025-11-18 16:00 UTC
Thumbnail: https://cdn1.epicgames.com/offer/...
============================================================

############################################################
# UPCOMING FREE GAMES
############################################################

No games found.
```

## Enable Discord Notifications

1. **Get Discord Webhook URL**
   - Go to your Discord server → Server Settings → Integrations → Webhooks
   - Click "New Webhook"
   - Copy the webhook URL

2. **Configure**

   Create `.env` file:
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
   ```

   Or edit `config.yaml`:
   ```yaml
   discord:
     enabled: true
     webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
   ```

3. **Test Discord Integration**
   ```bash
   python run.py --send-discord
   ```

## Set Up Cron Job

Run daily at 9 AM to check for new free games:

1. **Find your Python path**
   ```bash
   which python  # while venv is activated
   # Example: /Users/bidoof/Developer/Projects/Personal/epic-games-free-games-notification/venv/bin/python
   ```

2. **Edit crontab**
   ```bash
   crontab -e
   ```

3. **Add cron job**
   ```cron
   0 9 * * * cd /Users/bidoof/Developer/Projects/Personal/epic-games-free-games-notification && /Users/bidoof/Developer/Projects/Personal/epic-games-free-games-notification/venv/bin/python run.py --send-discord
   ```

## Common Commands

```bash
# Show only currently free games
python run.py --active-only

# Show only upcoming games
python run.py --upcoming-only

# Send Discord notification
python run.py --send-discord

# Enable debug logging
python run.py --log-level DEBUG

# Use custom config file
python run.py --config /path/to/config.yaml
```

## Troubleshooting

### ImportError or ModuleNotFoundError

Make sure you activated the virtual environment:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### No games found

- Check your internet connection
- Verify Epic Games Store is accessible
- Check the logs: `cat epic_games_notifier.log`

### Discord notifications not working

- Verify webhook URL is correct
- Check `discord.enabled` is `true` in `config.yaml`
- Test webhook manually: `python run.py --send-discord --log-level DEBUG`

## Next Steps

- **Customize notifications**: Edit `config.yaml` to control what gets notified
- **Add role mentions**: Set `DISCORD_MENTION_ROLE_ID` in `.env`
- **Change locale/country**: Modify `epic_games` settings in `config.yaml`
- **Run tests**: `pytest tests/`
- **Format code**: `make format`

## Example Cron Schedules

```cron
# Every day at 9 AM
0 9 * * * cd /path/to/project && /path/to/venv/bin/python run.py --send-discord

# Every Thursday at 10 AM (Epic's typical free game release day)
0 10 * * 4 cd /path/to/project && /path/to/venv/bin/python run.py --send-discord

# Twice a day (9 AM and 5 PM)
0 9,17 * * * cd /path/to/project && /path/to/venv/bin/python run.py --send-discord
```

## Support

For issues or questions:
- Check the main README.md
- Review logs in `epic_games_notifier.log`
- Use `--log-level DEBUG` for more details
