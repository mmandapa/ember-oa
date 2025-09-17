# Testing Guide for Cigna Policy Scraper

## Overview
This document outlines how to test the Cigna Policy Scraper system to ensure it meets all requirements.

## Prerequisites
- Python 3.8+ with virtual environment activated
- Node.js 18+ 
- Supabase project configured
- Chrome browser (for Selenium)

## Testing Checklist

### ✅ Core Requirements Validation

#### 1. Target Website Access
- [ ] Verify access to main page: https://static.cigna.com/assets/chcp/resourceLibrary/coveragePolicies/latestUpdatesListing.html
- [ ] Confirm monthly policy update links are accessible
- [ ] Test individual policy page access

#### 2. Data Extraction Requirements
- [ ] **Title**: Policy title/headline extracted correctly
- [ ] **URL**: Direct link to full policy document captured
- [ ] **Published Date**: Publication date parsed and stored
- [ ] **Category**: Policy category/classification identified
- [ ] **Body Content**: Full text content extracted (HTML format for tables)
- [ ] **Referenced Documents**: Policy documents referenced in updates
- [ ] **Medical Codes**: CPT/HCPCS codes, ICD-10 codes with descriptions
- [ ] **Document Changes**: Content changes made to referenced policies

#### 3. Comprehensive Coverage
- [ ] All monthly pages scraped (2023-2025)
- [ ] Individual policy updates within each month extracted
- [ ] No policies missed due to pagination or dynamic loading

#### 4. Technical Requirements
- [ ] Robust error handling for network issues
- [ ] Data validation for extracted information
- [ ] Graceful handling of missing data
- [ ] Rate limiting implemented (2-second delays)

### 🧪 Testing Procedures

#### Backend Testing

1. **Environment Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Database Connection Test**
   ```bash
   python -c "
   import os
   from dotenv import load_dotenv
   load_dotenv()
   from database.supabase_client import supabase_client
   print('Supabase connection:', supabase_client.url)
   "
   ```

3. **Scraper Test**
   ```bash
   python scraper/main_scraper.py
   ```

4. **Data Validation Test**
   ```bash
   python -c "
   from scraper.validators import DataValidator
   validator = DataValidator()
   test_data = {'title': 'Test Policy', 'url': 'https://example.com'}
   result = validator.validate_policy_data(test_data)
   print('Validation result:', result['is_valid'])
   "
   ```

#### Frontend Testing

1. **Environment Setup**
   ```bash
   cd frontend
   npm install
   ```

2. **Development Server**
   ```bash
   npm run dev
   ```

3. **Access Interface**
   - Open http://localhost:3000
   - Verify dashboard loads
   - Test search functionality
   - Test filtering options
   - Verify policy cards display correctly

#### Integration Testing

1. **End-to-End Workflow**
   - Run scraper to populate database
   - Verify data appears in frontend
   - Test search and filter functionality
   - Verify medical codes are highlighted
   - Check document change tracking

2. **Data Quality Checks**
   - Verify no duplicate policies
   - Check medical code format validation
   - Ensure URLs are properly formatted
   - Validate date parsing accuracy

### 🐛 Common Issues and Solutions

#### Issue: Selenium WebDriver Errors
**Solution**: Ensure Chrome browser is installed and ChromeDriver is compatible
```bash
pip install --upgrade webdriver-manager
```

#### Issue: Supabase Connection Errors
**Solution**: Verify environment variables are set correctly
```bash
echo $SUPABASE_URL
echo $SUPABASE_KEY
```

#### Issue: Missing Dependencies
**Solution**: Reinstall requirements
```bash
pip install -r requirements.txt
npm install
```

#### Issue: CORS Errors in Frontend
**Solution**: Check Supabase RLS policies and API keys

### 📊 Performance Testing

1. **Scraping Performance**
   - Monitor memory usage during scraping
   - Check execution time for full scrape
   - Verify rate limiting effectiveness

2. **Frontend Performance**
   - Test with large datasets (1000+ policies)
   - Verify search performance
   - Check page load times

### 🔍 Data Quality Validation

#### Sample Data Checks
- [ ] At least 10 policies scraped successfully
- [ ] Medical codes extracted (CPT, HCPCS, ICD-10)
- [ ] Referenced documents identified
- [ ] Document changes captured
- [ ] Dates parsed correctly
- [ ] URLs are valid and accessible

#### Error Rate Monitoring
- [ ] Error rate < 5% for successful scrapes
- [ ] Critical errors logged appropriately
- [ ] Recovery from network timeouts

### 📝 Test Results Documentation

Record test results in the following format:

```
Test Date: [DATE]
Environment: [OS/Browser]
Backend Status: [PASS/FAIL]
Frontend Status: [PASS/FAIL]
Policies Scraped: [NUMBER]
Errors Encountered: [NUMBER]
Performance: [EXECUTION_TIME]
```

### 🚀 Deployment Testing

1. **Production Environment**
   - Test with production Supabase instance
   - Verify environment variable configuration
   - Test with actual Cigna website

2. **Scalability Testing**
   - Test with multiple concurrent scrapers
   - Verify database performance under load
   - Check frontend responsiveness

## Success Criteria

The system passes testing when:
- ✅ All required data fields are extracted
- ✅ Comprehensive coverage of all policy updates
- ✅ Robust error handling and recovery
- ✅ Clean, responsive web interface
- ✅ Medical codes properly identified and categorized
- ✅ Document changes tracked accurately
- ✅ Performance meets requirements (< 30 seconds per monthly page)
- ✅ Error rate < 5%

## Next Steps After Testing

1. Document any limitations or assumptions
2. Create deployment guide for production
3. Set up monitoring and alerting
4. Schedule regular scraping runs
5. Implement data backup procedures
