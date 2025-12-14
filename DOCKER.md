# Docker Deployment Guide

This guide covers running the Epic Games Free Games Notifier using Docker.

## Quick Start

### Using Docker Run

```bash
# Build the image
docker build -t epic-games-notifier .

# Run the container
docker run -d \
  --name epic-games-notifier \
  -p 8080:8080 \
  -e DISCORD_WEBHOOK_URL='https://discord.com/api/webhooks/YOUR_WEBHOOK' \
  -e EPIC_LOCALE='en-US' \
  -e EPIC_COUNTRY='US' \
  epic-games-notifier

# Check logs
docker logs -f epic-games-notifier

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

# Stop service
docker-compose down
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for notifications | None (required) |
| `DISCORD_MENTION_ROLE_ID` | Discord role ID to mention | None |
| `EPIC_LOCALE` | Game information locale | `en-US` |
| `EPIC_COUNTRY` | Country code | `US` |
| `PORT` | HTTP server port | `8080` |

## Volumes

### Persistent Logs

Mount a volume to persist logs:

```bash
docker run -d \
  -v $(pwd)/logs:/app/logs \
  -e DISCORD_WEBHOOK_URL='your-webhook' \
  epic-games-notifier
```

### Custom Configuration

Mount a custom config file:

```bash
docker run -d \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -e DISCORD_WEBHOOK_URL='your-webhook' \
  epic-games-notifier
```

## Multi-Architecture Builds

Build for multiple platforms:

```bash
# Enable buildx
docker buildx create --use

# Build for multiple architectures
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t epic-games-notifier:multi-arch \
  --push \
  .
```

## Production Deployment

### Docker Swarm

```yaml
# stack.yml
version: '3.8'

services:
  epic-games-notifier:
    image: epic-games-notifier:latest
    ports:
      - "8080:8080"
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
    secrets:
      - discord_webhook
    deploy:
      replicas: 1
      restart_policy:
        condition: on-failure
      resources:
        limits:
          cpus: '1'
          memory: 512M

secrets:
  discord_webhook:
    external: true
```

Deploy:
```bash
docker stack deploy -c stack.yml epic-games
```

### Kubernetes

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: epic-games-notifier
spec:
  replicas: 1
  selector:
    matchLabels:
      app: epic-games-notifier
  template:
    metadata:
      labels:
        app: epic-games-notifier
    spec:
      containers:
      - name: epic-games-notifier
        image: epic-games-notifier:latest
        ports:
        - containerPort: 8080
        env:
        - name: DISCORD_WEBHOOK_URL
          valueFrom:
            secretKeyRef:
              name: discord-webhook
              key: url
        - name: EPIC_LOCALE
          value: "en-US"
        - name: EPIC_COUNTRY
          value: "US"
        resources:
          limits:
            memory: "512Mi"
            cpu: "1"
          requests:
            memory: "256Mi"
            cpu: "0.5"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: epic-games-notifier
spec:
  selector:
    app: epic-games-notifier
  ports:
  - port: 80
    targetPort: 8080
  type: LoadBalancer
---
apiVersion: batch/v1
kind: CronJob
metadata:
  name: epic-games-check
spec:
  schedule: "0 9 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: curl
            image: curlimages/curl:latest
            args:
            - -X
            - POST
            - http://epic-games-notifier/check
          restartPolicy: OnFailure
```

## Health Checks

The container includes health checks:

```bash
# Docker health check
docker inspect --format='{{.State.Health.Status}}' epic-games-notifier

# Manual health check
curl http://localhost:8080/health
```

## Endpoints

- `GET /` or `GET /health` - Health check endpoint
- `POST /check` - Trigger game check and notifications
- `GET /check` - Also triggers check (for easier testing)

## Logging

### View Logs

```bash
# Follow logs
docker logs -f epic-games-notifier

# Last 100 lines
docker logs --tail 100 epic-games-notifier

# Logs since timestamp
docker logs --since 2024-01-01T00:00:00 epic-games-notifier
```

### Log Drivers

Use different log drivers for production:

```bash
# JSON file (default)
docker run -d \
  --log-driver json-file \
  --log-opt max-size=10m \
  --log-opt max-file=3 \
  epic-games-notifier

# Syslog
docker run -d \
  --log-driver syslog \
  --log-opt syslog-address=tcp://192.168.0.42:514 \
  epic-games-notifier

# Fluentd
docker run -d \
  --log-driver fluentd \
  --log-opt fluentd-address=localhost:24224 \
  epic-games-notifier
```

## Security

### Run as Non-Root

The Dockerfile already runs as non-root user (appuser, UID 1000).

### Scan for Vulnerabilities

```bash
# Using Docker Scout
docker scout cves epic-games-notifier

# Using Trivy
trivy image epic-games-notifier
```

### Read-Only Root Filesystem

```bash
docker run -d \
  --read-only \
  --tmpfs /tmp \
  -v $(pwd)/logs:/app/logs \
  epic-games-notifier
```

## Troubleshooting

### Container Exits Immediately

```bash
# Check logs
docker logs epic-games-notifier

# Run interactively
docker run -it --rm epic-games-notifier /bin/bash
```

### Port Already in Use

```bash
# Use different port
docker run -d -p 8081:8080 epic-games-notifier
```

### Permission Issues

```bash
# Fix volume permissions
chown -R 1000:1000 ./logs

# Or run with specific user
docker run -d --user 1000:1000 epic-games-notifier
```

### Network Issues

```bash
# Check container network
docker inspect epic-games-notifier | grep -A 20 NetworkSettings

# Use host network (not recommended for production)
docker run -d --network host epic-games-notifier
```

## Performance Tuning

### Resource Limits

```bash
docker run -d \
  --memory=512m \
  --memory-swap=512m \
  --cpus=1 \
  epic-games-notifier
```

### Optimize Image Size

Current image size: ~150MB (after multi-stage build)

Further optimization:
```dockerfile
# Use alpine base (example)
FROM python:3.11-alpine

# Remove unnecessary packages
RUN pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker image
        run: docker build -t epic-games-notifier .

      - name: Run tests
        run: docker run --rm epic-games-notifier pytest

      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker tag epic-games-notifier username/epic-games-notifier:latest
          docker push username/epic-games-notifier:latest
```

### GitLab CI

```yaml
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t epic-games-notifier .
    - docker tag epic-games-notifier $CI_REGISTRY_IMAGE:latest
    - docker push $CI_REGISTRY_IMAGE:latest
```

## Backup and Restore

### Backup Configuration

```bash
# Backup volumes
docker run --rm \
  -v epic-games-notifier_logs:/source:ro \
  -v $(pwd)/backup:/backup \
  alpine tar -czf /backup/logs-$(date +%Y%m%d).tar.gz -C /source .
```

### Export/Import Images

```bash
# Export
docker save epic-games-notifier | gzip > epic-games-notifier.tar.gz

# Import
gunzip -c epic-games-notifier.tar.gz | docker load
```

## Advanced Usage

### Multi-Container Setup

```yaml
version: '3.8'

services:
  app:
    build: .
    environment:
      - DISCORD_WEBHOOK_URL=${DISCORD_WEBHOOK_URL}
    depends_on:
      - redis
    networks:
      - app-network

  redis:
    image: redis:alpine
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### Scheduled Execution with Cron

Instead of running as a server, use cron:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/ ./src/
COPY config.yaml run.py ./

# Install cron
RUN apt-get update && apt-get install -y cron

# Add cron job
RUN echo "0 9 * * * cd /app && python run.py --send-discord >> /var/log/cron.log 2>&1" | crontab -

CMD ["cron", "-f"]
```
