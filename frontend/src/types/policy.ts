export interface PolicyUpdate {
  id: string
  title: string
  url: string
  published_date: string | null
  category: string
  body_content: string
  month_year: string
  created_at: string
  updated_at: string
}

export interface ReferencedDocument {
  id: string
  policy_update_id: string
  document_title: string
  document_url: string
  document_type: string
  created_at: string
}

export interface MedicalCode {
  id: string
  policy_update_id: string
  code: string
  code_type: string
  description: string
  created_at: string
}

export interface DocumentChange {
  id: string
  policy_update_id: string
  document_title: string
  change_type: string
  change_description: string
  section_affected: string
  created_at: string
}

export interface PolicyWithDetails extends PolicyUpdate {
  referenced_documents: ReferencedDocument[]
  medical_codes: MedicalCode[]
  document_changes: DocumentChange[]
}

export interface ScrapingStats {
  totalPolicies: number
  totalMedicalCodes: number
  lastScraped: string | null
}

export interface ScrapingLog {
  id: string
  url: string
  status: string
  error_message: string | null
  records_scraped: number
  execution_time: number
  timestamp: string
}
