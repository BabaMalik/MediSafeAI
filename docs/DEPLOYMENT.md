# MediSafeAI Deployment Guide

Complete guide for deploying MediSafeAI to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Docker Deployment](#docker-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Database Setup](#database-setup)
6. [Security Configuration](#security-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup and Recovery](#backup-and-recovery)

## Prerequisites

### System Requirements

- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB+ for database and logs
- **OS**: Linux (Ubuntu 20.04+, CentOS 8+) or macOS

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- PostgreSQL 14+ (if not using Docker)
- Redis 7+ (if not using Docker)
- Node.js 18+ (for frontend)
- Python 3.10+ (for backend)

## Environment Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Configure Essential Variables

Edit `.env` with production values:

```env
# Application
APP_ENV=production
DEBUG=False
SECRET_KEY=<generate-strong-secret-key>

# Database
DATABASE_URL=postgresql://medisafe_user:STRONG_PASSWORD@postgres:5432/medisafe_db

# JWT
JWT_SECRET_KEY=<generate-strong-jwt-secret>

# Redis
REDIS_URL=redis://:REDIS_PASSWORD@redis:6379/0

# API
API_HOST=0.0.0.0
API_PORT=5000

# CORS (set to your frontend domain)
CORS_ORIGINS=https://app.medisafe.ai

# Privacy
MAX_EPSILON=10.0
DEFAULT_EPSILON=1.0
```

### 3. Generate Strong Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Docker Deployment

### Quick Start (Development)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

1. **Build Production Images**

```bash
# Build API image
docker build -f docker/Dockerfile.api -t medisafe-api:latest .

# Build frontend
cd frontend
npm install
npm run build
cd ..
```

2. **Start Services**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

3. **Initialize Database**

```bash
docker-compose exec api python -m src.cli.main db init
docker-compose exec api python -m src.cli.main db migrate
```

4. **Create Admin User**

```bash
docker-compose exec api python -m src.cli.main user create-admin
```

### Service Endpoints

- **API**: http://localhost:5000
- **Frontend**: http://localhost:3000
- **Airflow**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Kubernetes Deployment

### 1. Create Namespace

```bash
kubectl create namespace medisafe
```

### 2. Create Secrets

```bash
kubectl create secret generic medisafe-secrets \
  --from-literal=SECRET_KEY='your-secret-key' \
  --from-literal=JWT_SECRET_KEY='your-jwt-secret' \
  --from-literal=DATABASE_URL='postgresql://...' \
  --namespace=medisafe
```

### 3. Apply Manifests

```bash
kubectl apply -f k8s/postgres.yaml -n medisafe
kubectl apply -f k8s/redis.yaml -n medisafe
kubectl apply -f k8s/api.yaml -n medisafe
kubectl apply -f k8s/frontend.yaml -n medisafe
kubectl apply -f k8s/ingress.yaml -n medisafe
```

### 4. Verify Deployment

```bash
kubectl get pods -n medisafe
kubectl get services -n medisafe
```

## Database Setup

### Manual PostgreSQL Setup

```sql
-- Create database and user
CREATE DATABASE medisafe_db;
CREATE USER medisafe_user WITH ENCRYPTED PASSWORD 'strong_password';
GRANT ALL PRIVILEGES ON DATABASE medisafe_db TO medisafe_user;

-- Create Airflow database
CREATE DATABASE airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow TO medisafe_user;
```

### Run Migrations

```bash
# Using CLI
python -m src.cli.main db migrate

# Or via Docker
docker-compose exec api python -m src.cli.main db migrate
```

### Backup Database

```bash
# Backup
docker-compose exec postgres pg_dump -U medisafe_user medisafe_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U medisafe_user medisafe_db < backup.sql
```

## Security Configuration

### 1. SSL/TLS Setup

Configure reverse proxy (Nginx) with SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name api.medisafe.ai;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Firewall Rules

```bash
# Allow only necessary ports
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

### 3. Security Headers

Already configured in `src/api/app.py`:
- X-Content-Type-Options
- X-Frame-Options
- X-XSS-Protection

### 4. Rate Limiting

Configure in `.env`:
```env
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
```

## Monitoring Setup

### Prometheus & Grafana

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d
```

Access:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (admin/admin)

### Application Logs

```bash
# View API logs
docker-compose logs -f api

# View all logs
docker-compose logs -f

# Export logs
docker-compose logs --no-color > logs.txt
```

### Health Monitoring

```bash
# Check API health
curl http://localhost:5000/health

# Check all services
docker-compose ps
```

## Backup and Recovery

### Automated Backups

Create a backup script:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/var/backups/medisafe

# Backup database
docker-compose exec -T postgres pg_dump -U medisafe_user medisafe_db | \
  gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup volumes
docker run --rm -v medisafe_postgres-db-volume:/data -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/postgres_volume_$DATE.tar.gz /data

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

Schedule with cron:
```bash
0 2 * * * /path/to/backup.sh
```

### Recovery

```bash
# Restore database
gunzip < backup.sql.gz | \
  docker-compose exec -T postgres psql -U medisafe_user medisafe_db

# Restore volumes
docker run --rm -v medisafe_postgres-db-volume:/data -v /path/to/backup:/backup \
  alpine tar xzf /backup/postgres_volume_20231201.tar.gz -C /
```

## Production Checklist

- [ ] Strong secrets configured in `.env`
- [ ] SSL/TLS certificates installed
- [ ] Firewall configured
- [ ] Database backups automated
- [ ] Monitoring enabled (Prometheus/Grafana)
- [ ] Log rotation configured
- [ ] Rate limiting enabled
- [ ] CORS configured for production domains
- [ ] Admin user created
- [ ] Health checks passing
- [ ] Audit logging verified
- [ ] Privacy budget monitoring active

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec api python -c "from src.models.base import check_database_connection; print(check_database_connection())"
```

### Redis Connection Issues

```bash
# Check Redis
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### API Not Starting

```bash
# Check logs
docker-compose logs api

# Check dependencies
docker-compose exec api pip list

# Restart service
docker-compose restart api
```

## Support

For issues and support:
- GitHub Issues: https://github.com/medisafe/medisafe-ai/issues
- Email: support@medisafe.ai
- Documentation: https://docs.medisafe.ai
