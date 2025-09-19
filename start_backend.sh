#!/bin/bash

# Define colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Ember OA Backend Services...${NC}"

# Function to check if a process is running
check_process() {
    pgrep -f "$1" > /dev/null
}

# Function to get PID of a process
get_pid() {
    pgrep -f "$1"
}

# 1. Activate virtual environment
echo -e "${BLUE}📦 Activating virtual environment...${NC}"
source venv/bin/activate

# 2. Start Redis Server
echo -e "${RED}🔴 Starting Redis server...${NC}"
if check_process "redis-server"; then
    echo -e "${YELLOW}⚠️  Redis is already running${NC}"
else
    # Start Redis in background
    redis-server --daemonize yes --pidfile redis.pid
    sleep 1
    if check_process "redis-server"; then
        echo -e "${GREEN}✅ Redis started successfully (PID: $(get_pid "redis-server"))${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
        exit 1
    fi
fi

# 3. Start Celery Workers (but don't process tasks yet)
echo -e "${BLUE}⚙️  Starting Celery workers...${NC}"
if check_process "celery.*worker"; then
    echo -e "${YELLOW}⚠️  Celery workers are already running${NC}"
else
        # Start multiple Celery workers in background
        cd backend
        source ../venv/bin/activate
        nohup celery -A scraper worker --hostname=worker1@%h --loglevel=info > ../worker1.log 2>&1 &
        nohup celery -A scraper worker --hostname=worker2@%h --loglevel=info > ../worker2.log 2>&1 &
        nohup celery -A scraper worker --hostname=worker3@%h --loglevel=info > ../worker3.log 2>&1 &
        nohup celery -A scraper worker --hostname=worker4@%h --loglevel=info > ../worker4.log 2>&1 &
        cd ..
    
    sleep 3
    
    # Verify Celery workers are running
    if check_process "celery.*worker"; then
        echo -e "${GREEN}✅ Celery workers started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Celery workers${NC}"
        exit 1
    fi
fi

# 4. Start Flask Backend
echo -e "${BLUE}🐍 Starting Flask backend...${NC}"
if check_process "python app.py"; then
    echo -e "${YELLOW}⚠️  Flask backend is already running${NC}"
else
    # Start Flask in background
    cd backend
    source ../venv/bin/activate
    nohup python app.py > ../flask_backend.log 2>&1 &
    FLASK_PID=$!
    echo "$FLASK_PID" > ../flask_backend.pid
    cd ..
    sleep 3
    
    # Verify Flask is running
    sleep 5  # Give Flask more time to start
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Flask backend started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start Flask backend${NC}"
        echo -e "${YELLOW}📋 Checking Flask logs...${NC}"
        if [ -f "../flask_backend.log" ]; then
            tail -10 ../flask_backend.log
        fi
        exit 1
    fi
fi

# 5. Health Check
echo -e "${BLUE}🏥 Running health check...${NC}"
sleep 2

HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/health)
if echo "$HEALTH_RESPONSE" | grep -q '"status": "healthy"'; then
    echo -e "${GREEN}✅ All services are healthy!${NC}"
    echo -e "${BLUE}📊 Health Status:${NC}"
    echo "$HEALTH_RESPONSE" | python -m json.tool
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
    exit 1
fi

echo -e "\n${GREEN}🎉 Backend services started successfully!${NC}"
echo -e "${BLUE}📡 Services:${NC}"
echo "   • Redis: localhost:6379"
echo "   • Flask API: http://localhost:8000"
echo "   • Celery Workers: Active"
echo -e "\n${YELLOW}💡 Use './stop_backend.sh' to stop all services${NC}"