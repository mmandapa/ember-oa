#!/bin/bash

# Define colors for output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${RED}🛑 Stopping Ember OA Backend Services...${NC}"

# Function to kill a process by PID file
kill_process_by_pidfile() {
    if [ -f "$1" ]; then
        PID=$(cat "$1")
        if ps -p $PID > /dev/null; then
            echo -e "   Stopping $2 (PID: $PID)..."
            kill $PID
            # Wait for the process to terminate
            for i in $(seq 1 10); do
                if ! ps -p $PID > /dev/null; then
                    echo -e "   ${GREEN}✅ $2 stopped${NC}"
                    rm "$1"
                    return 0
                fi
                sleep 1
            done
            echo -e "   ${YELLOW}⚠️  $2 did not stop gracefully, killing...${NC}"
            kill -9 $PID
            rm "$1"
            return 0
        else
            echo -e "   ${YELLOW}⚠️  $2 PID file found but process not running. Cleaning up PID file.${NC}"
            rm "$1"
        fi
    else
        echo -e "   ${YELLOW}⚠️  $2 PID file not found.${NC}"
    fi
    return 1
}

# Function to kill a process by name (fallback)
kill_process_by_name() {
    PIDS=$(pgrep -f "$1")
    if [ -n "$PIDS" ]; then
        echo -e "   Stopping $2 (PIDs: $PIDS)..."
        kill $PIDS
        for PID in $PIDS; do
            for i in $(seq 1 10); do
                if ! ps -p $PID > /dev/null; then
                    break
                fi
                sleep 1
            done
            if ps -p $PID > /dev/null; then
                echo -e "   ${YELLOW}⚠️  $2 (PID: $PID) did not stop gracefully, killing...${NC}"
                kill -9 $PID
            fi
        done
        echo -e "   ${GREEN}✅ $2 stopped${NC}"
        return 0
    else
        echo -e "   ${YELLOW}⚠️  $2 process not found.${NC}"
    fi
    return 1
}

# 1. Stop Flask Backend
kill_process_by_pidfile flask_backend.pid "Flask" || kill_process_by_name "python app.py" "Flask"

# 2. Stop Celery Workers
kill_process_by_name "celery -A scraper worker" "Celery workers"

# 3. Stop Redis Server
kill_process_by_pidfile redis.pid "Redis" || kill_process_by_name "redis-server" "Redis"

echo -e "${GREEN}✅ All backend services stopped${NC}"