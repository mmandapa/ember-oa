# High-Performance Setup Guide

This guide will help you set up the high-performance Cigna Policy Scraper with nginx load balancing and multiple workers.

## Prerequisites

### 1. Install nginx

**macOS (using Homebrew):**
```bash
brew install nginx
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nginx
```

**CentOS/RHEL:**
```bash
sudo yum install nginx
# or
sudo dnf install nginx
```

### 2. Install Redis

**macOS:**
```bash
brew install redis
```

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
```

**CentOS/RHEL:**
```bash
sudo yum install redis
# or
sudo dnf install redis
```

## Quick Start

### 1. One-Click High-Performance Setup

```bash
# Clone and setup
git clone <your-repo>
cd ember-oa

# Install Python dependencies
source venv/bin/activate
pip install -r backend/requirements.txt

# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/cigna-scraper
sudo ln -s /etc/nginx/sites-available/cigna-scraper /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration

# Start the high-performance system
python start_high_performance_system.py
```

### 2. Test the Setup

```bash
# Run performance tests
python test_high_performance.py
```

## Manual Setup

### 1. Start Redis
```bash
redis-server
```

### 2. Start High-Performance Celery Workers
```bash
cd backend
python start_high_performance_workers.py
```

### 3. Start Multiple Flask Workers
```bash
cd backend
python start_multiple_flask_workers.py
```

### 4. Configure and Start nginx
```bash
# Copy nginx config
sudo cp nginx.conf /etc/nginx/sites-available/cigna-scraper
sudo ln -s /etc/nginx/sites-available/cigna-scraper /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Start nginx
sudo systemctl start nginx
# or
sudo service nginx start
```

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

## Performance Monitoring

### 1. Flower (Celery Monitoring)
- URL: http://localhost:5555
- Shows active workers, task queues, and performance metrics

### 2. System Status API
```bash
curl http://localhost/api/system-status
```

### 3. Health Checks
```bash
curl http://localhost/api/health
```

## Expected Performance

| System Specs | Celery Workers | Flask Workers | Expected Speed |
|---------------|----------------|---------------|----------------|
| 16+ GB RAM    | 16 workers     | 4 workers     | 50-100 PDFs/min |
| 8-16 GB RAM   | 12 workers     | 3 workers     | 30-60 PDFs/min |
| 4-8 GB RAM    | 8 workers      | 2 workers     | 20-40 PDFs/min |

## Troubleshooting

### nginx Issues
```bash
# Check nginx status
sudo systemctl status nginx

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Redis Issues
```bash
# Check Redis status
redis-cli ping

# Check Redis memory usage
redis-cli info memory

# Restart Redis
sudo systemctl restart redis
```

### Celery Issues
```bash
# Check Celery workers
cd backend
python -c "from scraper import celery_app; print(celery_app.control.inspect().active())"

# Restart workers
pkill -f celery
python start_high_performance_workers.py
```

### Flask Issues
```bash
# Check Flask workers
curl http://localhost:8000/api/health
curl http://localhost:8001/api/health
curl http://localhost:8002/api/health
curl http://localhost:8003/api/health

# Restart Flask workers
pkill -f gunicorn
cd backend
python start_multiple_flask_workers.py
```

## Performance Optimization

### 1. System-Level Optimizations

**Increase file limits:**
```bash
# Add to /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536
```

**Optimize Redis:**
```bash
# Add to /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
```

**Optimize nginx:**
```bash
# Add to /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 1024;
```

### 2. Application-Level Optimizations

- **Prefetch multiplier**: Set to 1 for better load balancing
- **Worker restarts**: Every 1000 tasks to prevent memory leaks
- **Connection pooling**: Keep-alive connections for better performance
- **Rate limiting**: Protect against overload

## Security Considerations

- **Rate limiting**: Built-in protection against abuse
- **CORS**: Properly configured for frontend access
- **Security headers**: XSS protection, content type validation
- **Input validation**: All API endpoints validate input

## Scaling

### Horizontal Scaling
- Add more Flask workers by increasing port range
- Add more Celery workers on different machines
- Use Redis Cluster for distributed caching

### Vertical Scaling
- Increase worker concurrency
- Add more CPU cores and RAM
- Use faster storage (SSD)

## Monitoring

### Key Metrics to Monitor
- **Request rate**: Requests per second
- **Response time**: Average response time
- **Worker utilization**: Active vs idle workers
- **Memory usage**: Redis and worker memory
- **Queue depth**: Pending tasks in Celery

### Alerting
Set up alerts for:
- High response times (>5 seconds)
- Worker failures
- Memory usage (>80%)
- Queue depth (>1000 tasks)
