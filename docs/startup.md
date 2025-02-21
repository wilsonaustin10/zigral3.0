# Zigral Startup Guide

## Prerequisites
- Docker and Docker Compose installed
- Git repository cloned
- `.env` file configured with proper credentials

## Directory Structure Setup
```bash
# Create required directories
mkdir -p docker/config docker/scripts logs/agents shared

# Copy configuration files
cp docker/config/nginx.conf docker/config/
cp docker/config/supervisord.conf docker/config/
cp docker/scripts/start.sh docker/scripts/
chmod +x docker/scripts/start.sh
```

## Environment Configuration
1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Update the following variables in `.env`:
```ini
# VNC Configuration
VNC_PASSWORD=your_secure_password
VNC_HOST=34.174.193.245
VNC_PORT=6080

# Grafana Configuration
GRAFANA_PASSWORD=your_grafana_password
GRAFANA_DOMAIN=localhost
GRAFANA_PORT=3000

# Other credentials as needed...
```

## Starting Zigral

### Development Mode
```bash
# Build containers with development configuration
docker-compose -f docker-compose.yml -f docker-compose.dev.yml build

# Start services in development mode
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Production Mode
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d
```

## Verifying Services
After startup, verify that all services are running:
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## Access Points
- Zigral API: http://localhost:8000
- VNC Web Client: http://localhost:6080
- Grafana Dashboard: http://localhost:3000
- Prometheus Metrics: http://localhost:9090

## Service Health Checks
```bash
# Check API health
curl http://localhost:8000/health

# Check VNC connectivity
nc -zv localhost 6080

# Check Redis
docker-compose exec redis redis-cli ping
```

## Common Operations

### Restart a Specific Service
```bash
docker-compose restart [service_name]
# Example: docker-compose restart agent-vm
```

### View Service Logs
```bash
docker-compose logs [service_name]
# Example: docker-compose logs zigral-api
```

### Scale Services
```bash
docker-compose up -d --scale agent-vm=2
```

### Stop All Services
```bash
docker-compose down
```

### Clean Up
```bash
# Remove all containers and volumes
docker-compose down -v

# Remove all built images
docker-compose down --rmi all
```

## Troubleshooting

### VNC Connection Issues
1. Check if the VNC service is running:
```bash
docker-compose logs agent-vm
```

2. Verify VNC port is accessible:
```bash
nc -zv localhost 5900
nc -zv localhost 6080
```

### Agent Issues
1. Check agent logs:
```bash
docker-compose exec agent-vm tail -f /var/log/agents/lincoln.log
docker-compose exec agent-vm tail -f /var/log/agents/shaun.log
```

2. Restart agents:
```bash
docker-compose exec agent-vm supervisorctl restart lincoln shaun
```

### Redis Issues
1. Check Redis connection:
```bash
docker-compose exec redis redis-cli ping
```

2. Monitor Redis:
```bash
docker-compose exec redis redis-cli monitor
```

## Maintenance

### Backup Volumes
```bash
# Create a backup directory
mkdir -p backups

# Backup Redis data
docker run --rm -v zigral_redis-data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis-backup.tar.gz /data
```

### Update Services
```bash
# Pull latest changes
git pull

# Rebuild and restart services
docker-compose build
docker-compose up -d
```

## Security Notes
- Always change default passwords in production
- Use secure VNC passwords
- Keep `.env` file secure and never commit it to version control
- Regularly update dependencies and base images

## Architecture Overview

### Components
1. **Zigral API Service**
   - Main FastAPI application
   - Handles request routing and orchestration
   - Communicates with agents through Redis

2. **Agent VM**
   - Debian-based container with VNC support
   - Runs Lincoln (LinkedIn) and Shaun (Google Sheets) agents
   - Managed by supervisord
   - Accessible via VNC/noVNC

3. **Redis**
   - State management and caching
   - Inter-service communication
   - Session storage

4. **Monitoring Stack**
   - Prometheus for metrics collection
   - Grafana for visualization
   - Health checks and alerts

### Network Flow
```
Client -> Zigral API -> Redis -> Agent VM
                    -> Prometheus -> Grafana
```

### Volume Management
- `redis-data`: Persistent Redis storage
- `prometheus-data`: Metric storage
- `grafana-data`: Dashboard configurations
- `shared`: Shared data between services
- `logs`: Application and service logs

## Development Guidelines

### Adding New Agents
1. Create agent module in `src/agents/`
2. Add supervisor configuration in `docker/config/supervisord.conf`
3. Update Docker configuration if needed
4. Add health checks and monitoring

### Modifying Existing Agents
1. Update agent code in `src/agents/`
2. Rebuild and restart services:
```bash
docker-compose build agent-vm
docker-compose up -d agent-vm
```

### Testing
1. Run unit tests:
```bash
docker-compose exec zigral-api pytest tests/unit
```

2. Run integration tests:
```bash
docker-compose exec zigral-api pytest tests/integration
```

## Production Deployment

### Prerequisites
- Domain name configured
- SSL certificates obtained
- Production environment variables set

### Deployment Steps
1. Configure production environment:
```bash
cp .env.example .env.prod
# Edit .env.prod with production values
```

2. Deploy with production configuration:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### SSL Configuration
1. Update nginx configuration for SSL
2. Configure secure WebSocket connections
3. Update environment variables for HTTPS

### Monitoring Setup
1. Configure Prometheus alerts
2. Set up Grafana dashboards
3. Configure log aggregation

### Backup Strategy
1. Regular volume backups
2. Database backups
3. Configuration backups

## Support and Resources
- GitHub Repository: [Zigral Repository]
- Documentation: [Zigral Docs]
- Issue Tracker: [GitHub Issues]
- Contact: support@zigral.ai 