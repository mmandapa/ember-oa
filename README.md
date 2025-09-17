# Cigna Policy Scraper

A comprehensive web scraper to extract policy updates from Cigna's provider news website with a web-based display system.

## Overview

This project extracts all available policy update information from Cigna's provider news site, including:
- Policy titles and URLs
- Published dates and categories
- Full body content
- Referenced documents
- Medical codes (CPT/HCPCS, ICD-10)
- Document changes

## Features

- **Comprehensive Coverage**: Extracts ALL policies, including expanded monthly updates
- **Robust Error Handling**: Handles network issues, missing data, and parsing errors
- **Data Validation**: Validates extracted data and handles edge cases
- **Web Interface**: Clean, responsive display system for viewing scraped data
- **Medical Code Extraction**: Automatically identifies CPT/HCPCS and ICD-10 codes
- **Document Change Tracking**: Extracts specific content changes mentioned in updates

## Project Structure

```
ember-oa/
├── backend/
│   ├── scraper/
│   │   ├── __init__.py
│   │   ├── main_scraper.py      # Main scraping logic
│   │   ├── data_extractor.py    # Data extraction utilities
│   │   ├── error_handler.py     # Error handling and logging
│   │   └── validators.py        # Data validation
│   ├── database/
│   │   ├── __init__.py
│   │   ├── supabase_client.py   # Supabase connection
│   │   ├── models.py            # Database models/schemas
│   │   └── migrations/          # Database migrations
│   └── utils/
│       ├── __init__.py
│       ├── config.py            # Configuration settings
│       └── helpers.py           # Utility functions
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── services/            # API services
│   │   └── utils/               # Frontend utilities
│   ├── public/
│   └── package.json
├── data/                        # Local data storage
├── logs/                        # Log files
├── tests/                       # Unit tests
├── .env.example                 # Environment variables template
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 18+
- Supabase account (for database)

### 1. Clone and Setup Backend

```bash
git clone https://github.com/mmandapa/ember-oa.git
cd ember-oa

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Setup Supabase Database

1. Create a new Supabase project at [supabase.com](https://supabase.com)
2. Copy your project URL and API keys
3. Create a `.env` file from the example:
   ```bash
   cp env.example .env
   ```
4. Update `.env` with your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
   ```

### 3. Initialize Database Schema

Run the SQL commands from `backend/database/models.py` in your Supabase SQL editor to create the required tables.

### 4. Setup Frontend

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

Update `frontend/.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 5. Run the Application

**Backend (Scraper):**
```bash
# From project root
python backend/scraper/main_scraper.py
```

**Frontend (Web Interface):**
```bash
# From frontend directory
npm run dev
```

### 6. View Results

Open your browser and navigate to `http://localhost:3000`

## Usage

### Running the Scraper
```bash
python src/scraper/main_scraper.py
```

### Viewing Results
The web interface provides:
- Policy listing with search and filter capabilities
- Detailed policy view with all extracted information
- Medical codes highlighting
- Document change tracking
- Export functionality

## Technical Details

### Data Extraction
- **Title**: Policy headline/title
- **URL**: Direct link to full policy document
- **Published Date**: Release/publication date
- **Category**: Policy classification
- **Body Content**: Full text content (HTML format for tables)
- **Referenced Documents**: Links to medical policies, clinical guidelines
- **Medical Codes**: CPT/HCPCS codes, ICD-10 codes with descriptions
- **Document Changes**: Specific content modifications mentioned

### Error Handling
- Network timeout and retry logic
- Missing data field handling
- HTML parsing error recovery
- Comprehensive logging system

### Data Validation
- Required field validation
- Date format validation
- URL format validation
- Medical code format validation

## Limitations and Assumptions

### Limitations
- Website structure changes may require scraper updates
- Dynamic content loading may need Selenium for JavaScript-heavy pages
- Rate limiting to respect server resources
- Some policy documents may require authentication

### Assumptions
- Website HTML structure remains relatively stable
- Policy updates follow consistent formatting patterns
- Medical codes follow standard formatting conventions
- Policy documents are publicly accessible

## Compliance

This scraper is designed to:
- Respect robots.txt directives
- Implement reasonable request delays
- Use appropriate User-Agent headers
- Follow ethical web scraping practices

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is for educational and demonstration purposes.
