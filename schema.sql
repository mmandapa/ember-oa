-- Cigna Policy Updates Database Schema
-- Run this in your Supabase SQL Editor

-- Main policy updates table
CREATE TABLE IF NOT EXISTS policy_updates (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    policy_url TEXT UNIQUE NOT NULL,
    monthly_pdf_url TEXT NOT NULL,
    policy_number TEXT,
    published_date TIMESTAMP WITH TIME ZONE,
    effective_date TIMESTAMP WITH TIME ZONE,
    category TEXT,
    status TEXT,
    body_content TEXT,
    month_year TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Referenced documents table
CREATE TABLE IF NOT EXISTS referenced_documents (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
    document_title TEXT,
    document_url TEXT,
    document_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Medical codes table
CREATE TABLE IF NOT EXISTS medical_codes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
    code TEXT,
    code_type TEXT,
    description TEXT,
    is_covered BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Document changes table
CREATE TABLE IF NOT EXISTS document_changes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    policy_update_id UUID REFERENCES policy_updates(id) ON DELETE CASCADE,
    document_title TEXT,
    change_type TEXT,
    change_description TEXT,
    section_affected TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scraping logs table
CREATE TABLE IF NOT EXISTS scraping_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    log_level TEXT,
    message TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_policy_updates_published_date ON policy_updates(published_date);
CREATE INDEX IF NOT EXISTS idx_policy_updates_category ON policy_updates(category);
CREATE INDEX IF NOT EXISTS idx_policy_updates_month_year ON policy_updates(month_year);
CREATE INDEX IF NOT EXISTS idx_medical_codes_code ON medical_codes(code);
CREATE INDEX IF NOT EXISTS idx_medical_codes_type ON medical_codes(code_type);

-- Enable Row Level Security
ALTER TABLE policy_updates ENABLE ROW LEVEL SECURITY;
ALTER TABLE referenced_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE medical_codes ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_changes ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_logs ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations (for development)
CREATE POLICY "Allow all operations on policy_updates" ON policy_updates FOR ALL USING (true);
CREATE POLICY "Allow all operations on referenced_documents" ON referenced_documents FOR ALL USING (true);
CREATE POLICY "Allow all operations on medical_codes" ON medical_codes FOR ALL USING (true);
CREATE POLICY "Allow all operations on document_changes" ON document_changes FOR ALL USING (true);
CREATE POLICY "Allow all operations on scraping_logs" ON scraping_logs FOR ALL USING (true);
