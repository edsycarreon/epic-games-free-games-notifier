# Epic Games Free Games Notification System

A Python application that fetches current and upcoming free games from the Epic Games Store and sends notifications via Discord webhooks.

## Features

- **Fetch Free Games**: Retrieves current and upcoming free games from Epic Games Store
- **Rich Game Information**: Gets title, description, publisher, availability dates, images, and store URLs
- **Discord Integration**: Send notifications to Discord via webhooks (configurable)
- **Flexible Configuration**: YAML config file with environment variable overrides
- **Robust Error Handling**: Retry logic, proper exception handling, and logging
- **Type Safety**: Full type hints using Pydantic models
- **Production Ready**: Designed for cron jobs and automated execution
- **Docker Support**: Full Docker and Docker Compose support
- **Cloud Ready**: Optimized for Google Cloud Run deployment

## Deployment Options

- **Local**: Run directly with Python
- **Docker**: Run in containers locally or on any Docker host
- **Google Cloud Run**: Serverless deployment with Cloud Scheduler
- **Kubernetes**: Production-grade orchestration

See detailed guides:
- [Quick Start Guide](QUICKSTART.md) - Get started in 5 minutes
- [Docker Deployment](DOCKER.md) - Containerized deployment
- [GCP Deployment](GCP_DEPLOYMENT.md) - Google Cloud Platform deployment

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd epic-games-free-games-notification
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure the application:
```bash
cp .env.example .env
# Edit .env and config.yaml with your settings
```

## Configuration

### config.yaml

The main configuration file controls all aspects of the application:

```yaml
epic_games:
  locale: "en-US"
  country: "US"
  allow_countries: "US"

discord:
  enabled: false
  webhook_url: ""
  mention_role_id: ""

notifications:
  notify_current_games: true
  notify_upcoming_games: true
  include_game_images: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "epic_games_notifier.log"
```

### Environment Variables

You can override settings using environment variables in `.env`:

```env
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_MENTION_ROLE_ID=123456789
EPIC_LOCALE=en-US
EPIC_COUNTRY=US
```

## Usage

### Basic Usage

Fetch and display all free games:
```bash
python run.py
```

### Show Only Active Games

```bash
python run.py --active-only
```

### Show Only Upcoming Games

```bash
python run.py --upcoming-only
```

### Send Discord Notifications

```bash
python run.py --send-discord
```

### Custom Config File

```bash
python run.py --config /path/to/config.yaml
```

### Override Log Level

```bash
python run.py --log-level DEBUG
```

## Running with Cron

To run the script daily and send Discord notifications:

1. Make the script executable:
```bash
chmod +x run.py
```

2. Edit your crontab:
```bash
crontab -e
```

3. Add a cron job (example: run daily at 9 AM):
```cron
0 9 * * * cd /path/to/epic-games-free-games-notification && /path/to/venv/bin/python run.py --send-discord >> /var/log/epic-games-notifier.log 2>&1
```

### Example Cron Schedules

```cron
# Every day at 9:00 AM
0 9 * * * cd /path/to/project && /path/to/venv/bin/python run.py --send-discord

# Every Thursday at 10:00 AM (when Epic releases new free games)
0 10 * * 4 cd /path/to/project && /path/to/venv/bin/python run.py --send-discord

# Every 6 hours
0 */6 * * * cd /path/to/project && /path/to/venv/bin/python run.py --send-discord
```

## Docker Deployment

### Quick Start with Docker

```bash
# Build the image
docker build -t epic-games-notifier .

# Run the container
docker run -d \
  --name epic-games-notifier \
  -p 8080:8080 \
  -e DISCORD_WEBHOOK_URL='your-webhook-url' \
  -e EPIC_LOCALE='en-US' \
  -e EPIC_COUNTRY='US' \
  epic-games-notifier

# Test the endpoints
curl http://localhost:8080/health
curl -X POST http://localhost:8080/check
```

### Using Docker Compose

```bash
# Create .env file
cp .env.example .env
# Edit .env with your Discord webhook URL

# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Trigger a check
curl -X POST http://localhost:8080/check

# Stop service
docker-compose down
```

See [DOCKER.md](DOCKER.md) for complete Docker deployment guide.

## Google Cloud Run Deployment

Deploy to GCP Cloud Run with automated scheduling:

### Prerequisites

- GCP account with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed
- Discord webhook URL

### Quick Deploy

```bash
# Set your GCP project ID
export GCP_PROJECT_ID="your-gcp-project-id"

# Store Discord webhook in Secret Manager
echo -n 'YOUR_WEBHOOK_URL' | \
  gcloud secrets create discord-webhook-url \
  --project="$GCP_PROJECT_ID" \
  --data-file=-

# Deploy (runs build, push, and scheduler setup)
./deploy.sh
```

The deployment includes:
- Docker image built and pushed to Google Container Registry
- Cloud Run service with 512Mi memory, 1 CPU
- Cloud Scheduler job (daily at 9 AM by default)
- Auto-scaling from 0 to 1 instance

### Estimated Cost

With daily execution: **~$0.25/month**
- Cloud Run: ~$0.10/month (mostly free tier)
- Cloud Scheduler: $0.10/month
- Container Registry: ~$0.05/month

### Manual Trigger

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe epic-games-notifier \
  --region=us-central1 \
  --format='value(status.url)')

# Trigger check
curl -X POST "${SERVICE_URL}/check"

# Manually run scheduler
gcloud scheduler jobs run epic-games-notifier-daily-check --location=us-central1
```

### View Logs

```bash
# Real-time logs
gcloud run logs tail epic-games-notifier --region=us-central1

# Recent logs
gcloud run logs read epic-games-notifier --region=us-central1 --limit=50
```

See [GCP_DEPLOYMENT.md](GCP_DEPLOYMENT.md) for complete deployment guide.

## Game Information Retrieved

For each free game, the system fetches:

- **Title**: Game name
- **Description**: Game description
- **Publisher**: Game publisher/developer
- **Status**: Current status (ACTIVE, UPCOMING, EXPIRED)
- **Available From**: Start date/time of the promotion
- **Available Until**: End date/time of the promotion
- **Store URL**: Direct link to the Epic Games Store page
- **Thumbnail**: Game image URL
- **Price Information**: Original and discounted prices
- **Promotional Details**: Discount percentage and type

## Project Structure

```
epic-games-free-games-notification/
├── src/
│   ├── __init__.py
│   ├── api_client.py       # Epic Games API client
│   ├── config.py            # Configuration management
│   ├── discord_notifier.py  # Discord webhook integration
│   ├── exceptions.py        # Custom exceptions
│   ├── main.py              # Main application logic
│   └── models.py            # Pydantic data models
├── tests/
│   ├── __init__.py
│   └── test_api_client.py  # Unit tests
├── config.yaml              # Configuration file
├── .env.example             # Environment variables template
├── .gitignore
├── .dockerignore            # Docker ignore file
├── requirements.txt         # Python dependencies
├── run.py                   # Convenience runner script
├── server.py                # Web server for Cloud Run
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker Compose configuration
├── deploy.sh                # GCP deployment script
├── cloudbuild.yaml          # Cloud Build CI/CD configuration
├── setup.py                 # Package setup
├── pyproject.toml           # Python project configuration
├── Makefile                 # Development tasks
├── README.md                # This file
├── QUICKSTART.md            # Quick start guide
├── DOCKER.md                # Docker deployment guide
└── GCP_DEPLOYMENT.md        # GCP deployment guide
```

## Discord Webhook Setup

1. Go to your Discord server settings
2. Navigate to Integrations → Webhooks
3. Click "New Webhook"
4. Copy the webhook URL
5. Add it to your `.env` file:
   ```env
   DISCORD_WEBHOOK_URL=your_webhook_url_here
   ```
6. Enable Discord in `config.yaml`:
   ```yaml
   discord:
     enabled: true
   ```

## Error Handling

The application includes comprehensive error handling:

- **Network Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Proper detection and error reporting
- **Invalid Responses**: Graceful handling of malformed data
- **Logging**: All errors are logged to file and console

## Development

### Code Quality Tools

Format code:
```bash
black src/
```

Lint code:
```bash
ruff check src/
```

Type checking:
```bash
mypy src/
```

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=src
```

## API Information

The application uses the Epic Games Store REST API:

- **Endpoint**: `https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions`
- **Method**: GET
- **Authentication**: None required (public endpoint)
- **Rate Limiting**: Built-in retry logic handles rate limits

## Best Practices Implemented

- **Type Safety**: Full Pydantic models with type hints
- **Error Handling**: Custom exceptions and proper error propagation
- **Logging**: Structured logging with configurable levels
- **Configuration**: Separation of config from code
- **Separation of Concerns**: Clean architecture with distinct modules
- **Resource Management**: Context managers for proper cleanup
- **Retry Logic**: Automatic retry for transient failures
- **Documentation**: Comprehensive docstrings and README

## Troubleshooting

### No games found

- Check your internet connection
- Verify the API endpoint is accessible
- Check logs for errors

### Discord notifications not working

- Verify webhook URL is correct
- Ensure `discord.enabled` is `true` in config
- Check Discord server permissions

### Rate limit errors

- Reduce cron job frequency
- Check logs for retry attempts

## License

MIT License

## Contributing

Contributions are welcome! Please follow the existing code style and add tests for new features.

## Future Enhancements

- Database storage for game history
- Web interface for configuration
- Multiple notification channels (Email, Slack, Telegram)
- Game filtering by genre/publisher
- Price tracking and alerts
