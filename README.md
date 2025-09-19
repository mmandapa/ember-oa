# Cigna Policy Scraper with OpenAI

A modern web scraper for Cigna policy updates using OpenAI's API for intelligent content analysis and extraction.

## Features

- **AI-Powered Analysis**: Uses OpenAI GPT-4 to intelligently extract structured data from policy documents
- **Comprehensive Data Extraction**: Captures Title, URL, Published Date, Category, Body Content, Referenced Documents, Medical Codes, and Document Changes
- **Beautiful Dashboard**: Modern, responsive Next.js interface with real-time statistics
- **Database Integration**: Supabase PostgreSQL database for data storage
- **Smart Deduplication**: Prevents duplicate entries with intelligent URL matching

## Project Structure

```
ember-oa/
├── backend/                  # Python backend with Celery + Redis
│   ├── scraper.py           # Main scraper with Celery integration
│   ├── start_worker.py      # Celery worker startup script
│   ├── start_scrape_task.py # Task initiation script
│   ├── check_task_status.py # Task status checker
│   ├── requirements.txt     # Python dependencies
│   ├── schema.sql          # Database schema
│   ├── test_openai.py      # OpenAI testing script
│   ├── TESTING.md          # Testing documentation
│   └── README.md           # Backend documentation
├── frontend/                # Next.js frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx                    # Landing page
│   │   │   ├── beautiful-dashboard.tsx      # Main dashboard
│   │   │   └── api/
│   │   │       ├── scrape-async.ts          # Async scraping API
│   │   │       └── task-status/[taskId].ts  # Task status API
│   │   ├── utils/
│   │   │   └── supabase.ts                 # Supabase client
│   │   └── types/
│   │       └── policy.ts                   # TypeScript types
│   └── package.json
├── .env                     # Environment variables
├── env.example             # Environment variables template
└── README.md
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- Supabase account
- OpenAI API key

## Setup

### 1. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd ember-oa

# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Install Node.js dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Configuration

Copy the environment template and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` with your credentials:
```
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Frontend Environment Variables
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
```

### 3. Database Setup

Run the SQL commands in `backend/schema.sql` in your Supabase SQL Editor to create the database tables.

### 4. Run the Application

#### Background Processing System (Recommended)

For large-scale scraping with background processing:

```bash
# Start Redis server
redis-server

# Start Celery worker (in a new terminal)
cd backend
source ../venv/bin/activate
python start_worker.py

# Start scraping task (in another terminal)
cd backend
source ../venv/bin/activate
python start_scrape_task.py

# Monitor tasks at http://localhost:5555 (Flower UI)
```

#### Frontend Only

```bash
# Start the frontend
cd frontend
npm run dev

# The dashboard will be available at http://localhost:3000
```

## Usage

### Dashboard

1. Open http://localhost:3000
2. Click "Open Dashboard" to access the main interface
3. Use the sidebar to navigate between different views:
   - **Dashboard**: Statistics overview
   - **All Policies**: Complete policy list
   - **Recent Updates**: Policies updated this week
   - **Medical/Pharmacy/Behavioral**: Category-specific views
   - **Medical Codes**: All extracted codes
   - **Document Changes**: All policy changes

### Running the Scraper

**Option 1: High-Performance Setup (Recommended)**
1. Start the complete high-performance system: `python start_high_performance_system.py`
2. Open your frontend dashboard
3. Click "Run Scraper" button
4. Enjoy 50-100 PDFs/minute processing speed!

**Option 2: Standard Setup**
1. Start the complete system: `cd backend && python start_complete_system.py`
2. Open your frontend dashboard
3. Click "Run Scraper" button

**Option 3: Manual Setup**
1. Start Redis: `redis-server`
2. Start Celery workers: `cd backend && python start_worker.py`
3. Start Flask API: `cd backend && python start_flask_server.py`
4. Open frontend dashboard and click "Run Scraper"

### Data Extraction

The OpenAI-powered scraper extracts the following data for each policy:

- **Title**: Policy title/headline
- **URL**: Direct link to the policy document
- **Published Date**: When the policy was published
- **Category**: Policy classification (New, Updated, Retired)
- **Body Content**: Full text content
- **Referenced Documents**: Related policy documents
- **Medical Codes**: CPT/HCPCS/ICD-10 codes with descriptions
- **Document Changes**: Specific changes made

## Performance Features

### High-Performance Architecture

- **Multiple Flask Workers**: 4 workers with nginx load balancing
- **High-Performance Celery Workers**: Up to 16 workers with 8 concurrency each
- **Nginx Load Balancer**: Intelligent request distribution and caching
- **Redis Optimization**: Memory-efficient caching and connection pooling
- **Async Processing**: Non-blocking I/O with gevent workers
- **Auto-scaling**: Workers restart automatically to prevent memory leaks

### Expected Performance

- **High-end Systems (16+ GB RAM)**: 50-100 PDFs/minute
- **Medium Systems (8-16 GB RAM)**: 30-60 PDFs/minute  
- **Standard Systems (4-8 GB RAM)**: 20-40 PDFs/minute

### Monitoring & Management

- **Flower UI**: http://localhost:5555 (Celery task monitoring)
- **System Status**: Real-time performance metrics
- **Health Checks**: Automatic failover and recovery
- **Rate Limiting**: Protection against overload

## Technical Details

### OpenAI Integration

- **Model**: GPT-4o-mini for cost-effective analysis
- **Prompt Engineering**: Structured prompts for consistent data extraction
- **Error Handling**: Robust error handling for API failures
- **Rate Limiting**: Built-in delays to respect API limits

### Dashboard Features

- **Modern UI**: Clean, professional interface
- **Responsive Design**: Works on all screen sizes
- **Real-time Updates**: Live data refresh
- **Advanced Search**: Search across all policy fields
- **Filtering**: Filter by category, date, and status
- **Detail Panel**: Comprehensive policy information display

## API Endpoints (High-Performance Setup)

**Via Nginx Load Balancer (Recommended):**
- `POST http://localhost/api/scrape-async` - Initiates background scraping task
- `GET http://localhost/api/task-status/<taskId>` - Checks task status
- `GET http://localhost/api/health` - Health check
- `GET http://localhost/api/system-status` - Detailed system status

**Direct Flask Workers:**
- `POST http://localhost:8000-8003/api/scrape-async` - Direct worker access
- `GET http://localhost:8000-8003/api/task-status/<taskId>` - Direct worker status

## Database Schema

The application uses the following main tables:

- `policy_updates` - Main policy information
- `medical_codes` - Extracted medical codes
- `referenced_documents` - Related documents
- `document_changes` - Policy changes
- `scraping_logs` - Scraping operation logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is for educational purposes. Please respect Cigna's terms of service and robots.txt when scraping their website.