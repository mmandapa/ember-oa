import { useState, useEffect } from 'react'
import Head from 'next/head'
import { supabase } from '../utils/supabase'

interface PolicyUpdate {
  id: string
  title: string
  policy_url: string
  monthly_pdf_url: string
  policy_number: string
  published_date: string | null
  effective_date: string | null
  category: string
  status: string
  body_content: string
  month_year: string
  created_at: string
  updated_at: string
}

interface ReferencedDocument {
  id: string
  policy_update_id: string
  document_title: string
  document_url: string
  document_type: string
  created_at: string
}

interface MedicalCode {
  id: string
  policy_update_id: string
  code: string
  code_type: string
  description: string
  is_covered: boolean | null
  created_at: string
}

interface DocumentChange {
  id: string
  policy_update_id: string
  document_title: string
  change_type: string
  change_description: string
  section_affected: string
  created_at: string
}

interface PolicyWithDetails extends PolicyUpdate {
  referenced_documents: ReferencedDocument[]
  medical_codes: MedicalCode[]
  document_changes: DocumentChange[]
}

export default function BeautifulDashboard() {
  const [policies, setPolicies] = useState<PolicyWithDetails[]>([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyWithDetails | null>(null)
  const [currentView, setCurrentView] = useState('dashboard')
  const [activeFilter, setActiveFilter] = useState('all')

  useEffect(() => {
    fetchPoliciesWithDetails()
  }, [])

  const fetchPoliciesWithDetails = async () => {
    try {
      setLoading(true)
      
      // Fetch policies
      const { data: policiesData, error: policiesError } = await supabase
        .from('policy_updates')
        .select('*')
        .order('published_date', { ascending: false })
        .limit(200)

      if (policiesError) throw policiesError

      // Fetch related data for each policy
      const policiesWithDetails: PolicyWithDetails[] = []
      
      for (const policy of policiesData || []) {
        // Fetch referenced documents
        const { data: docsData } = await supabase
          .from('referenced_documents')
          .select('*')
          .eq('policy_update_id', policy.id)

        // Fetch medical codes
        const { data: codesData } = await supabase
          .from('medical_codes')
          .select('*')
          .eq('policy_update_id', policy.id)

        // Fetch document changes
        const { data: changesData } = await supabase
          .from('document_changes')
          .select('*')
          .eq('policy_update_id', policy.id)

        policiesWithDetails.push({
          ...policy,
          referenced_documents: docsData || [],
          medical_codes: codesData || [],
          document_changes: changesData || []
        })
      }

      setPolicies(policiesWithDetails)
    } catch (error) {
      console.error('Error fetching policies:', error)
    } finally {
      setLoading(false)
    }
  }

  const runScraper = async () => {
    try {
      setScraping(true)
      
      // Start the async scraping task via Flask backend
      const response = await fetch('http://localhost:8000/api/scrape-async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const result = await response.json()

      if (result.success) {
        // Start polling for task status
        pollTaskStatus(result.task_id)
      } else {
        alert(`Failed to start scraper: ${result.message}`)
        setScraping(false)
      }
    } catch (error) {
      console.error('Error running scraper:', error)
      alert('Failed to start scraper')
      setScraping(false)
    }
  }

  const pollTaskStatus = async (taskId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/task-status/${taskId}`)
      const status = await response.json()

      if (status.status === 'SUCCESS') {
        alert('Scraper completed successfully!')
        setScraping(false)
        // Refresh the policies list
        await fetchPoliciesWithDetails()
      } else if (status.status === 'FAILURE') {
        alert(`Scraper failed: ${status.info}`)
        setScraping(false)
      } else if (status.status === 'PROGRESS') {
        // Update progress (you could show this in the UI)
        console.log(`Progress: ${status.info?.current || 0}/${status.info?.total || 0}`)
        // Continue polling
        setTimeout(() => pollTaskStatus(taskId), 2000)
      } else {
        // Still processing, continue polling
        setTimeout(() => pollTaskStatus(taskId), 2000)
      }
    } catch (error) {
      console.error('Error checking task status:', error)
      alert('Failed to check scraper status')
      setScraping(false)
    }
  }

  const clearAllData = async () => {
    if (!confirm('Are you sure you want to delete ALL data? This cannot be undone.')) {
      return
    }

    try {
      setClearing(true)
      
      // Delete all data from all tables
      const { error: policiesError } = await supabase
        .from('policy_updates')
        .delete()
        .neq('id', '00000000-0000-0000-0000-000000000000')

      const { error: codesError } = await supabase
        .from('medical_codes')
        .delete()
        .neq('id', '00000000-0000-0000-0000-000000000000')

      const { error: docsError } = await supabase
        .from('referenced_documents')
        .delete()
        .neq('id', '00000000-0000-0000-0000-000000000000')

      const { error: changesError } = await supabase
        .from('document_changes')
        .delete()
        .neq('id', '00000000-0000-0000-0000-000000000000')

      const { error: logsError } = await supabase
        .from('scraping_logs')
        .delete()
        .neq('id', '00000000-0000-0000-0000-000000000000')

      if (policiesError || codesError || docsError || changesError || logsError) {
        throw new Error('Failed to delete some data')
      }

      await fetchPoliciesWithDetails()
      alert('All data cleared successfully!')
      
    } catch (error) {
      console.error('Error clearing data:', error)
      alert('Failed to clear data')
    } finally {
      setClearing(false)
    }
  }

  const getCategoryBadgeClass = (category: string) => {
    switch (category.toLowerCase()) {
      case 'medical policy':
      case 'new policy':
      case 'updated policy':
        return 'category-medical'
      case 'pharmacy':
        return 'category-pharmacy'
      case 'behavioral':
        return 'category-behavioral'
      case 'dental':
        return 'category-dental'
      case 'vision':
        return 'category-vision'
      default:
        return 'category-default'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'new':
        return 'fas fa-plus-circle'
      case 'updated':
        return 'fas fa-edit'
      case 'retired':
        return 'fas fa-times-circle'
      default:
        return 'fas fa-check-circle'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'new':
        return '#10b981'
      case 'updated':
        return '#f59e0b'
      case 'retired':
        return '#ef4444'
      default:
        return '#10b981'
    }
  }

  const filteredPolicies = policies.filter(policy => {
    const matchesSearch = policy.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        policy.body_content.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        policy.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
                        policy.policy_number.includes(searchQuery)
    
    const matchesFilter = activeFilter === 'all' || 
                         (activeFilter === 'recent' && policy.published_date && 
                          new Date(policy.published_date) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)) ||
                         (activeFilter === 'medical' && policy.category.toLowerCase().includes('medical')) ||
                         (activeFilter === 'pharmacy' && policy.category.toLowerCase().includes('pharmacy'))
    
    return matchesSearch && matchesFilter
  })

  const stats = {
    totalPolicies: policies.length,
    recentUpdates: policies.filter(p => p.published_date && 
      new Date(p.published_date) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)).length,
    totalCodes: policies.reduce((sum, policy) => sum + policy.medical_codes.length, 0),
    totalChanges: policies.reduce((sum, policy) => sum + policy.document_changes.length, 0),
    totalDocuments: policies.reduce((sum, policy) => sum + policy.referenced_documents.length, 0),
    categories: Array.from(new Set(policies.map(p => p.category))).length
  }

  const showView = (viewName: string) => {
    setCurrentView(viewName)
  }

  const setFilter = (filterType: string) => {
    setActiveFilter(filterType)
  }

  const showPolicyDetail = (policy: PolicyWithDetails) => {
    setSelectedPolicy(policy)
  }

  const getValidPolicyUrl = (policy: PolicyUpdate) => {
    // If we have a constructed policy URL, use it
    if (policy.policy_url && policy.policy_url.includes('mm_')) {
      return policy.policy_url
    }
    
    // Otherwise, use the monthly PDF URL as fallback
    return policy.monthly_pdf_url
  }

  return (
    <>
      <Head>
        <title>Cigna Policy Management</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet" />
      </Head>

      <div className="app-container">
        {/* Sidebar */}
        <nav className="sidebar">
          <div className="sidebar-header">
            <div className="logo">
              <i className="fas fa-shield-alt"></i>
              Cigna Policy Hub
            </div>
          </div>
          <div className="nav-menu">
            <button 
              className={`nav-item ${currentView === 'dashboard' ? 'active' : ''}`} 
              onClick={() => showView('dashboard')}
            >
              <i className="fas fa-chart-bar"></i>
              Dashboard
            </button>
            <button 
              className={`nav-item ${currentView === 'policies' ? 'active' : ''}`} 
              onClick={() => showView('policies')}
            >
              <i className="fas fa-file-alt"></i>
              All Policies
            </button>
            <button 
              className={`nav-item ${currentView === 'recent' ? 'active' : ''}`} 
              onClick={() => showView('recent')}
            >
              <i className="fas fa-clock"></i>
              Recent Updates
            </button>
            <button 
              className={`nav-item ${currentView === 'medical' ? 'active' : ''}`} 
              onClick={() => showView('medical')}
            >
              <i className="fas fa-stethoscope"></i>
              Medical Policies
            </button>
            <button 
              className={`nav-item ${currentView === 'pharmacy' ? 'active' : ''}`} 
              onClick={() => showView('pharmacy')}
            >
              <i className="fas fa-pills"></i>
              Pharmacy
            </button>
            <button 
              className={`nav-item ${currentView === 'behavioral' ? 'active' : ''}`} 
              onClick={() => showView('behavioral')}
            >
              <i className="fas fa-brain"></i>
              Behavioral Health
            </button>
            <button 
              className={`nav-item ${currentView === 'codes' ? 'active' : ''}`} 
              onClick={() => showView('codes')}
            >
              <i className="fas fa-code"></i>
              Medical Codes
            </button>
            <button 
              className={`nav-item ${currentView === 'changes' ? 'active' : ''}`} 
              onClick={() => showView('changes')}
            >
              <i className="fas fa-edit"></i>
              Document Changes
            </button>
          </div>
        </nav>

        {/* Main Content */}
        <main className="main-content">
          <header className="main-header">
            <h1 className="page-title">
              {currentView === 'dashboard' ? 'Dashboard' :
               currentView === 'policies' ? 'All Policies' :
               currentView === 'recent' ? 'Recent Updates' :
               currentView === 'medical' ? 'Medical Policies' :
               currentView === 'pharmacy' ? 'Pharmacy Policies' :
               currentView === 'behavioral' ? 'Behavioral Health' :
               currentView === 'codes' ? 'Medical Codes' :
               'Document Changes'}
            </h1>
            <div className="search-container">
              <i className="fas fa-search search-icon"></i>
              <input 
                type="text" 
                className="search-input" 
                placeholder="Search policies, codes, or changes..." 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="filters">
              <button 
                className={`filter-btn ${activeFilter === 'all' ? 'active' : ''}`} 
                onClick={() => setFilter('all')}
              >
                All
              </button>
              <button 
                className={`filter-btn ${activeFilter === 'recent' ? 'active' : ''}`} 
                onClick={() => setFilter('recent')}
              >
                Recent
              </button>
              <button 
                className={`filter-btn ${activeFilter === 'medical' ? 'active' : ''}`} 
                onClick={() => setFilter('medical')}
              >
                Medical
              </button>
              <button 
                className={`filter-btn ${activeFilter === 'pharmacy' ? 'active' : ''}`} 
                onClick={() => setFilter('pharmacy')}
              >
                Pharmacy
              </button>
            </div>
            <div className="actions">
              <button
                onClick={runScraper}
                disabled={scraping || clearing}
                className={`action-btn ${scraping ? 'loading' : 'success'}`}
              >
                {scraping ? '⏳ Scraping...' : '🚀 Run Scraper'}
              </button>
              <button
                onClick={clearAllData}
                disabled={scraping || clearing}
                className={`action-btn ${clearing ? 'loading' : 'danger'}`}
              >
                {clearing ? '🗑️ Clearing...' : '🗑️ Clear Data'}
              </button>
            </div>
          </header>

          <div className="content-area">
            {/* Dashboard View */}
            {currentView === 'dashboard' && (
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-number">{stats.totalPolicies}</div>
                  <div className="stat-label">Total Policies Scraped</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.recentUpdates}</div>
                  <div className="stat-label">Updated This Week</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.totalCodes}</div>
                  <div className="stat-label">Medical Codes Extracted</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.totalChanges}</div>
                  <div className="stat-label">Document Changes</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.totalDocuments}</div>
                  <div className="stat-label">Referenced Documents</div>
                </div>
                <div className="stat-card">
                  <div className="stat-number">{stats.categories}</div>
                  <div className="stat-label">Policy Categories</div>
                </div>
              </div>
            )}

            {/* Policies List */}
            {currentView !== 'dashboard' && (
              <div className="policy-list">
                {loading ? (
                  <div className="loading">
                    <i className="fas fa-spinner fa-spin"></i>
                    Loading policies...
                  </div>
                ) : (
                  <table className="policy-table">
                    <thead>
                      <tr>
                        <th>Policy Title</th>
                        <th>Category</th>
                        <th>Published Date</th>
                        <th>Policy URL</th>
                        <th>Body Content</th>
                        <th>Medical Codes</th>
                        <th>Referenced Docs</th>
                        <th>Document Changes</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPolicies.map((policy) => (
                        <tr 
                          key={policy.id} 
                          className="policy-row"
                          onClick={() => showPolicyDetail(policy)}
                        >
                          <td>
                            <div className="policy-title">{policy.title}</div>
                            {policy.policy_number && (
                              <div className="policy-number">Policy #{policy.policy_number}</div>
                            )}
                          </td>
                          <td>
                            <span className={`category-badge ${getCategoryBadgeClass(policy.category)}`}>
                              {policy.category}
                            </span>
                            <div className="status-badge">
                              {policy.status || 'Active'}
                            </div>
                          </td>
                          <td className="date-text">
                            <div className="published-date">
                              {policy.published_date ? new Date(policy.published_date).toLocaleDateString() : 'N/A'}
                            </div>
                            {policy.effective_date && (
                              <div className="effective-date">
                                Effective: {new Date(policy.effective_date).toLocaleDateString()}
                              </div>
                            )}
                          </td>
                          <td>
                            <a 
                              href={policy.policy_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="policy-link"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <i className="fas fa-external-link-alt"></i>
                              View Policy
                            </a>
                          </td>
                          <td>
                            <div className="body-content-preview">
                              {policy.body_content ? 
                                (policy.body_content.length > 100 
                                  ? `${policy.body_content.substring(0, 100)}...`
                                  : policy.body_content) : 
                                'No content available'
                              }
                            </div>
                          </td>
                          <td>
                            <div className="codes-count">
                              {policy.medical_codes?.length || 0} codes
                              {policy.medical_codes?.length > 0 && (
                                <div className="code-types">
                                  {Array.from(new Set(policy.medical_codes.map(c => c.code_type))).join(', ')}
                                </div>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="docs-count">
                              {policy.referenced_documents?.length || 0} documents
                            </div>
                          </td>
                          <td>
                            <div className="changes-count">
                              {policy.document_changes?.length || 0} changes
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        </main>

        {/* Detail Panel */}
        {selectedPolicy && (
          <aside className="detail-panel active">
            <div className="detail-header">
              <div className="detail-title">{selectedPolicy.title}</div>
              <div className="detail-meta">
                <div className="meta-item">
                  <i className="fas fa-calendar"></i>
                  <span>
                    {selectedPolicy.published_date 
                      ? `Updated ${new Date(selectedPolicy.published_date).toLocaleDateString()}`
                      : 'No date available'
                    }
                  </span>
                </div>
                <div className="meta-item">
                  <i className="fas fa-tag"></i>
                  <span className={`category-badge ${getCategoryBadgeClass(selectedPolicy.category)}`}>
                    {selectedPolicy.category}
                  </span>
                </div>
                <div className="meta-item">
                  <i className="fas fa-external-link-alt"></i>
                  <a 
                    href={getValidPolicyUrl(selectedPolicy)} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ color: '#0066cc' }}
                  >
                    View Original Document
                  </a>
                </div>
                {selectedPolicy.effective_date && (
                  <div className="meta-item">
                    <i className="fas fa-clock"></i>
                    <span>Effective: {new Date(selectedPolicy.effective_date).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
            <div className="detail-content">

              {selectedPolicy.medical_codes.length > 0 && (
                <>
                  <div className="section-title">
                    <i className="fas fa-code"></i>
                    Medical Codes ({selectedPolicy.medical_codes.length})
                  </div>
                  <div className="code-list scrollable-section">
                    {selectedPolicy.medical_codes.map((code) => (
                      <div key={code.id} className="code-item">
                        <div className="code-info">
                          <span className="code-value">{code.code}</span>
                          <span className="code-type">{code.code_type}</span>
                        </div>
                        {code.description && (
                          <div className="code-description">{code.description}</div>
                        )}
                        {code.is_covered !== null && (
                          <div className={`coverage-status ${code.is_covered ? 'covered' : 'not-covered'}`}>
                            {code.is_covered ? 'Covered' : 'Not Covered'}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}

              {selectedPolicy.document_changes.length > 0 && (
                <>
                  <div className="section-title">
                    <i className="fas fa-edit"></i>
                    Document Changes ({selectedPolicy.document_changes.length})
                  </div>
                  <div className="changes-list scrollable-section">
                    {selectedPolicy.document_changes.map((change) => (
                      <div key={change.id} className="change-item">
                        <div className="change-header">
                          <span className="change-type">{change.change_type}</span>
                          {change.section_affected && (
                            <span className="section-affected">{change.section_affected}</span>
                          )}
                        </div>
                        <div className="change-description">{change.change_description}</div>
                      </div>
                    ))}
                  </div>
                </>
              )}

              {selectedPolicy.referenced_documents.length > 0 && (
                <>
                  <div className="section-title">
                    <i className="fas fa-file-alt"></i>
                    Referenced Documents ({selectedPolicy.referenced_documents.length})
                  </div>
                  <div className="documents-list scrollable-section">
                    {selectedPolicy.referenced_documents.map((doc) => (
                      <div key={doc.id} className="document-item">
                        <div className="document-title" title={doc.document_title}>
                          {doc.document_title}
                        </div>
                        <div className="document-type">{doc.document_type}</div>
                        {doc.document_url && (
                          <a 
                            href={doc.document_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="document-link"
                          >
                            <i className="fas fa-external-link-alt"></i>
                            View Document
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              )}

              <div className="section-title">
                <i className="fas fa-info-circle"></i>
                Policy Content
              </div>
              <div className="policy-content">
                {selectedPolicy.body_content}
              </div>
            </div>
          </aside>
        )}
      </div>

      <style jsx>{`
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
          background: #fafbfc;
          color: #1a1a1a;
          line-height: 1.6;
        }

        .app-container {
          display: flex;
          height: 100vh;
          overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
          width: 280px;
          background: #ffffff;
          border-right: 1px solid #e1e4e8;
          display: flex;
          flex-direction: column;
          z-index: 100;
        }

        .sidebar-header {
          padding: 20px 24px;
          border-bottom: 1px solid #e1e4e8;
        }

        .logo {
          font-size: 20px;
          font-weight: 700;
          color: #0066cc;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .nav-menu {
          flex: 1;
          padding: 16px 0;
        }

        .nav-item {
          display: flex;
          align-items: center;
          padding: 12px 24px;
          color: #6b7280;
          text-decoration: none;
          transition: all 0.2s ease;
          border: none;
          background: none;
          width: 100%;
          font-size: 14px;
          cursor: pointer;
        }

        .nav-item:hover {
          background: #f3f4f6;
          color: #1f2937;
        }

        .nav-item.active {
          background: #eff6ff;
          color: #0066cc;
          border-right: 3px solid #0066cc;
        }

        .nav-item i {
          width: 20px;
          margin-right: 12px;
        }

        /* Main Content */
        .main-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .main-header {
          background: #ffffff;
          border-bottom: 1px solid #e1e4e8;
          padding: 16px 24px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 20px;
        }

        .page-title {
          font-size: 24px;
          font-weight: 600;
          color: #1a1a1a;
        }

        .search-container {
          position: relative;
          flex: 1;
          max-width: 400px;
        }

        .search-input {
          width: 100%;
          padding: 10px 16px 10px 40px;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          font-size: 14px;
          background: #f9fafb;
          transition: all 0.2s ease;
        }

        .search-input:focus {
          outline: none;
          border-color: #0066cc;
          background: #ffffff;
          box-shadow: 0 0 0 3px rgba(0, 102, 204, 0.1);
        }

        .search-icon {
          position: absolute;
          left: 12px;
          top: 50%;
          transform: translateY(-50%);
          color: #6b7280;
        }

        .filters {
          display: flex;
          gap: 12px;
        }

        .filter-btn {
          padding: 8px 16px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          background: #ffffff;
          color: #374151;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .filter-btn:hover {
          border-color: #0066cc;
          color: #0066cc;
        }

        .filter-btn.active {
          background: #0066cc;
          color: white;
          border-color: #0066cc;
        }

        .actions {
          display: flex;
          gap: 12px;
        }

        .action-btn {
          padding: 8px 16px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          background: #ffffff;
          color: #374151;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .action-btn.success {
          background: #10b981;
          color: white;
          border-color: #10b981;
        }

        .action-btn.danger {
          background: #ef4444;
          color: white;
          border-color: #ef4444;
        }

        .action-btn.loading {
          background: #f59e0b;
          color: white;
          border-color: #f59e0b;
          cursor: not-allowed;
        }

        .action-btn:hover:not(.loading) {
          opacity: 0.9;
        }

        /* Content Area */
        .content-area {
          flex: 1;
          display: flex;
          overflow: hidden;
        }

        /* Policy List */
        .policy-list {
          flex: 1;
          background: #ffffff;
          overflow-y: auto;
        }

        .policy-table {
          width: 100%;
          border-collapse: collapse;
        }

        .policy-table th {
          background: #f9fafb;
          padding: 12px 16px;
          text-align: left;
          font-weight: 600;
          font-size: 12px;
          color: #6b7280;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border-bottom: 1px solid #e5e7eb;
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .policy-table td {
          padding: 12px 8px;
          border-bottom: 1px solid #f3f4f6;
          vertical-align: top;
          font-size: 14px;
        }

        .policy-row {
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .policy-row:hover {
          background: #f9fafb;
        }

        .policy-title {
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 4px;
          line-height: 1.4;
        }

        .policy-preview {
          color: #6b7280;
          font-size: 14px;
          line-height: 1.4;
          max-width: 400px;
        }

        .policy-number {
          color: #0066cc;
          font-size: 12px;
          font-weight: 500;
          margin-top: 4px;
        }

        .status-badge {
          font-size: 11px;
          color: #6b7280;
          margin-top: 4px;
          font-style: italic;
        }

        .published-date {
          font-weight: 500;
          color: #1a1a1a;
        }

        .effective-date {
          font-size: 12px;
          color: #6b7280;
          margin-top: 2px;
        }

        .policy-link {
          color: #0066cc;
          text-decoration: none;
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .policy-link:hover {
          text-decoration: underline;
        }

        .body-content-preview {
          max-width: 200px;
          color: #6b7280;
          font-size: 13px;
          line-height: 1.4;
        }

        .codes-count, .docs-count, .changes-count {
          font-size: 12px;
          color: #374151;
          font-weight: 500;
        }

        .code-types {
          font-size: 11px;
          color: #6b7280;
          margin-top: 2px;
          font-style: italic;
        }


        .code-info {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .code-description {
          font-size: 12px;
          color: #6b7280;
          margin-top: 4px;
          font-style: italic;
        }

        .coverage-status {
          font-size: 11px;
          padding: 2px 6px;
          border-radius: 4px;
          margin-top: 4px;
          display: inline-block;
        }

        .coverage-status.covered {
          background: #dcfce7;
          color: #166534;
        }

        .coverage-status.not-covered {
          background: #fee2e2;
          color: #dc2626;
        }

        .documents-list {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
        }

        .document-item {
          padding: 16px 12px;
          border-bottom: 1px solid #e2e8f0;
          background: #ffffff;
          border-radius: 6px;
          margin-bottom: 8px;
          border: 1px solid #e2e8f0;
          transition: all 0.2s ease;
        }

        .document-item:hover {
          border-color: #0066cc;
          box-shadow: 0 2px 8px rgba(0, 102, 204, 0.1);
        }

        .document-item:last-child {
          border-bottom: 1px solid #e2e8f0;
          margin-bottom: 0;
        }

        .document-title {
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 4px;
          word-wrap: break-word;
          word-break: break-word;
          line-height: 1.4;
          white-space: normal;
          overflow-wrap: break-word;
        }

        .document-type {
          font-size: 12px;
          color: #6b7280;
          margin-bottom: 8px;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .document-link {
          color: #0066cc;
          text-decoration: none;
          font-size: 12px;
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 4px;
          background: #f0f9ff;
          border: 1px solid #e0f2fe;
          transition: all 0.2s ease;
        }

        .document-link:hover {
          background: #0066cc;
          color: white;
          border-color: #0066cc;
          text-decoration: none;
        }

        .change-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
        }

        .section-affected {
          font-size: 11px;
          color: #6b7280;
          background: #f3f4f6;
          padding: 2px 6px;
          border-radius: 4px;
        }

        .category-badge {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.025em;
        }

        .category-medical { background: #fef3c7; color: #92400e; }
        .category-pharmacy { background: #dbeafe; color: #1e40af; }
        .category-behavioral { background: #f3e8ff; color: #7c3aed; }
        .category-dental { background: #dcfce7; color: #166534; }
        .category-vision { background: #fed7e2; color: #be185d; }
        .category-default { background: #f3f4f6; color: #374151; }

        .date-text {
          color: #6b7280;
          font-size: 14px;
        }

        /* Detail Panel */
        .detail-panel {
          width: 400px;
          background: #ffffff;
          border-left: 1px solid #e1e4e8;
          overflow-y: auto;
          display: none;
        }

        .detail-panel.active {
          display: block;
        }

        .detail-header {
          padding: 24px;
          border-bottom: 1px solid #e5e7eb;
        }

        .detail-title {
          font-size: 18px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 8px;
          line-height: 1.4;
        }

        .detail-meta {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .meta-item {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #6b7280;
        }

        .detail-content {
          padding: 24px;
        }

        .section-title {
          font-size: 16px;
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .code-list {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
        }

        .scrollable-section {
          max-height: 400px;
          overflow-y: auto;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
          background: #ffffff;
        }

        .scrollable-section::-webkit-scrollbar {
          width: 8px;
        }

        .scrollable-section::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 4px;
        }

        .scrollable-section::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
          border: 1px solid #e2e8f0;
        }

        .scrollable-section::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
          border-color: #cbd5e1;
        }

        .code-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 8px 0;
          border-bottom: 1px solid #e2e8f0;
        }

        .code-item:last-child {
          border-bottom: none;
        }

        .code-value {
          font-family: 'Monaco', 'Menlo', monospace;
          font-weight: 600;
          color: #0066cc;
        }

        .code-type {
          font-size: 12px;
          padding: 2px 6px;
          background: #e5e7eb;
          border-radius: 4px;
          color: #374151;
        }

        .changes-list {
          margin-bottom: 20px;
        }

        .change-item {
          padding: 12px;
          background: #fef9e7;
          border-left: 4px solid #f59e0b;
          border-radius: 4px;
          margin-bottom: 12px;
        }

        .change-type {
          font-size: 12px;
          font-weight: 600;
          color: #92400e;
          text-transform: uppercase;
          margin-bottom: 4px;
        }

        .change-description {
          color: #374151;
          font-size: 14px;
        }

        .documents-list {
          margin-bottom: 20px;
        }

        .document-item {
          padding: 12px;
          background: #f0f9ff;
          border-left: 4px solid #0066cc;
          border-radius: 4px;
          margin-bottom: 12px;
        }

        .document-title {
          font-weight: 600;
          color: #1a1a1a;
          margin-bottom: 4px;
        }

        .document-type {
          font-size: 12px;
          color: #6b7280;
        }

        .policy-content {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 16px;
          color: #374151;
          font-size: 14px;
          line-height: 1.6;
          max-height: 400px;
          overflow-y: auto;
        }

        .policy-content::-webkit-scrollbar {
          width: 6px;
        }

        .policy-content::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }

        .policy-content::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }

        .policy-content::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }

        /* Statistics Dashboard */
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: 24px;
          padding: 24px;
        }

        .stat-card {
          background: #ffffff;
          border: 1px solid #e5e7eb;
          border-radius: 12px;
          padding: 24px;
          transition: all 0.2s ease;
        }

        .stat-card:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }

        .stat-number {
          font-size: 32px;
          font-weight: 700;
          color: #0066cc;
          margin-bottom: 8px;
        }

        .stat-label {
          color: #6b7280;
          font-size: 14px;
          font-weight: 500;
        }

        .loading {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: #6b7280;
          gap: 12px;
        }

        /* Responsive */
        @media (max-width: 1024px) {
          .detail-panel {
            position: fixed;
            right: 0;
            top: 0;
            height: 100vh;
            z-index: 200;
            box-shadow: -4px 0 12px rgba(0, 0, 0, 0.1);
          }
          
          .sidebar {
            width: 240px;
          }
        }

        @media (max-width: 768px) {
          .sidebar {
            position: fixed;
            left: -280px;
            z-index: 300;
            transition: left 0.3s ease;
          }
          
          .sidebar.open {
            left: 0;
          }
          
          .main-header {
            padding-left: 60px;
            flex-wrap: wrap;
          }
          
          .actions {
            order: -1;
            width: 100%;
            justify-content: center;
            margin-bottom: 16px;
          }
        }
      `}</style>
    </>
  )
}
