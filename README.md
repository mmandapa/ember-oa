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
├── scraper.py                 # OpenAI-powered scraper
├── requirements.txt           # Python dependencies
├── schema.sql                # Database schema
├── .env                       # Environment variables
├── env.example               # Environment variables template
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── pages/
│   │   │   ├── index.tsx                    # Landing page
│   │   │   ├── beautiful-dashboard.tsx      # Main dashboard
│   │   │   └── api/
│   │   │       └── scrape.ts               # API endpoint
│   │   ├── utils/
│   │   │   └── supabase.ts                 # Supabase client
│   │   └── types/
│   │       └── policy.ts                   # TypeScript types
│   └── package.json
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
pip install -r requirements.txt

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

Run the SQL commands in `schema.sql` in your Supabase SQL Editor to create the database tables.

### 4. Run the Application

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

1. In the dashboard, click "Run Scraper" button
2. The OpenAI-powered scraper will analyze policy documents
3. Progress will be shown in real-time
4. Data will automatically refresh when complete

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

## API Endpoints

- `POST /api/scrape` - Runs the OpenAI-powered scraper

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