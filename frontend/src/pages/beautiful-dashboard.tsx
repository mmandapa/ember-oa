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

interface PolicyOption {
  value: string
  label: string
  url: string
  category: string
  is_pdf: boolean
}

export default function BeautifulDashboard() {
  const [policies, setPolicies] = useState<PolicyWithDetails[]>([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [selectedPolicy, setSelectedPolicy] = useState<PolicyWithDetails | null>(null)
  const [currentView, setCurrentView] = useState('policies')
  const [jobHistory, setJobHistory] = useState<Array<{id: string, startTime: Date, endTime?: Date, status: 'completed' | 'failed' | 'aborted', policiesProcessed: number, totalPolicies: number}>>([])
  const [policyOptions, setPolicyOptions] = useState<PolicyOption[]>([])
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])
  const [loadingOptions, setLoadingOptions] = useState(false)
  const [optionFilter, setOptionFilter] = useState('')
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [realtimeStats, setRealtimeStats] = useState({
    currentTask: null as any,
    isScraping: false,
    progress: 0,
    currentPolicy: '',
    policiesProcessed: 0,
    totalPolicies: 0,
    errors: 0
  })
  const [isPaused, setIsPaused] = useState(false)
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [toast, setToast] = useState<{message: string, type: 'success' | 'error' | 'info'} | null>(null)

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 5000) // Auto-hide after 5 seconds
  }

  useEffect(() => {
    fetchPoliciesWithDetails()
    fetchPolicyOptions()
  }, [])

  // Separate effect for continuous refresh during scraping
  useEffect(() => {
    let refreshInterval: NodeJS.Timeout | null = null
    
    if (scraping) {
      refreshInterval = setInterval(() => {
        fetchPoliciesWithDetails(false) // Don't show loading screen during updates
      }, 5000) // Refresh every 5 seconds - much more reasonable
    }
    
    return () => {
      if (refreshInterval) {
        clearInterval(refreshInterval)
      }
    }
  }, [scraping])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (dropdownOpen && !target.closest('.monthly-dropdown-section')) {
        setDropdownOpen(false)
      }
    }

    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [dropdownOpen])

  const fetchPoliciesWithDetails = async (showLoading = true) => {
    try {
      if (showLoading) {
      setLoading(true)
      }
      setIsRefreshing(true)
      
      // Fetch policies
      const { data: policiesData, error: policiesError } = await supabase
        .from('policy_updates')
        .select('*')
        .order('published_date', { ascending: false })

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
      if (showLoading) {
      setLoading(false)
      }
      setIsRefreshing(false)
    }
  }

  const fetchPolicyOptions = async () => {
    try {
      setLoadingOptions(true)
      console.log('🔄 Fetching policy options...')
      const response = await fetch('http://localhost:8000/api/policy-options')
      const result = await response.json()
      
      if (result.success) {
        setPolicyOptions(result.data)
        console.log(`📋 Loaded ${result.data.length} policy options:`, result.data)
      } else {
        console.error('Failed to fetch policy options:', result.message)
      }
    } catch (error) {
      console.error('Error fetching policy options:', error)
    } finally {
      setLoadingOptions(false)
    }
  }

  const runScraper = async () => {
    try {
      setScraping(true)
      
      // Prepare request body with selected options
      const requestBody = {
        selected_options: selectedOptions
      }
      
      // Start the async scraping task via Flask backend
      const response = await fetch('http://localhost:8000/api/scrape-async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
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
      
      console.log('📡 Task Status:', status)

      // Update real-time stats
      setRealtimeStats(prev => ({
        ...prev,
        currentTask: status,
        isScraping: true,
        progress: status.current || 0,
        totalPolicies: status.total || 0,
        currentPolicy: status.status || 'Processing...',
        policiesProcessed: status.current || 0
      }))

      // Enhanced progress tracking
      if (status.state === 'SUCCESS') {
        // Show completion message
        const completedCount = status.current || 0
        const totalCount = status.total || 0
        showToast(`🎉 Scraping completed successfully! Processed ${completedCount}/${totalCount} policies.`, 'success')
        
        // Add to job history
        const jobEntry = {
          id: taskId,
          startTime: new Date(),
          endTime: new Date(),
          status: 'completed' as const,
          policiesProcessed: completedCount,
          totalPolicies: totalCount
        }
        setJobHistory(prev => [jobEntry, ...prev.slice(0, 9)]) // Keep last 10 jobs
        
        setScraping(false)
        setRealtimeStats(prev => ({ ...prev, isScraping: false, currentTask: null }))
        
        // Final refresh to show all results
        await fetchPoliciesWithDetails(true) // Show loading for final refresh
      } else if (status.state === 'FAILURE') {
        showToast(`❌ Scraper failed: ${status.error || status.status}`, 'error')
        
        // Add to job history
        const jobEntry = {
          id: taskId,
          startTime: new Date(),
          endTime: new Date(),
          status: 'failed' as const,
          policiesProcessed: status.current || 0,
          totalPolicies: status.total || 0
        }
        setJobHistory(prev => [jobEntry, ...prev.slice(0, 9)]) // Keep last 10 jobs
        
        setScraping(false)
        setRealtimeStats(prev => ({ ...prev, isScraping: false, currentTask: null, errors: prev.errors + 1 }))
      } else if (status.state === 'PROGRESS' || status.state === 'PENDING') {
        // Show enhanced progress information
        const current = status.current || 0
        const total = status.total || 0
        const currentItem = status.status || 'Processing...'
        
        console.log(`📊 Progress: ${current}/${total} - ${currentItem}`)
        
        // Refresh policies data occasionally during processing
        if (current % 5 === 0) { // Only refresh every 5th progress update
          fetchPoliciesWithDetails(false) // Don't show loading screen during updates
        }
        
        // Continue polling with reasonable interval
        setTimeout(() => pollTaskStatus(taskId), 2000) // Poll every 2 seconds - much more reasonable
      } else {
        // Still processing, continue polling with reasonable interval
        setTimeout(() => pollTaskStatus(taskId), 2000) // Poll every 2 seconds
      }
    } catch (error) {
      console.error('Error checking task status:', error)
      alert('Failed to check scraper status')
      setScraping(false)
    }
  }

  const clearScreen = () => {
    console.log('🧹 Clearing screen...', { currentPoliciesCount: policies.length })
    setPolicies([])
    setSelectedPolicy(null)
    console.log('✅ Screen cleared!')
    showToast('Screen cleared! Data remains in database.', 'info')
  }

  const clearAllData = async () => {
    if (!confirm('Are you sure you want to delete ALL data? This cannot be undone.')) {
      return
    }

    try {
      setClearing(true)
      
        // Use Flask API to clear data
        const response = await fetch('http://localhost:8000/api/clear-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const result = await response.json()

      if (result.success) {
        await fetchPoliciesWithDetails()
        showToast(`All data cleared successfully! ${result.message}`, 'success')
      } else {
        throw new Error(result.message || 'Failed to clear data')
      }
      
    } catch (error) {
      console.error('Error clearing data:', error)
      showToast(`Failed to clear data: ${error.message}`, 'error')
    } finally {
      setClearing(false)
    }
  }

  const pauseScraper = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/pause-scraper', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      const result = await response.json()
      
      if (result.success) {
        setIsPaused(true)
        alert('Scraper paused successfully!')
      } else {
        throw new Error(result.message || 'Failed to pause scraper')
      }
    } catch (error) {
      console.error('Error pausing scraper:', error)
      alert('Failed to pause scraper: ' + error)
    }
  }

  const resumeScraper = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/resume-scraper', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      const result = await response.json()
      
      if (result.success) {
        setIsPaused(false)
        alert('Scraper resumed successfully!')
      } else {
        throw new Error(result.message || 'Failed to resume scraper')
      }
    } catch (error) {
      console.error('Error resuming scraper:', error)
      alert('Failed to resume scraper: ' + error)
    }
  }

  const abortScraper = async () => {
    if (confirm('Are you sure you want to abort the current scraping job? This will stop all processing immediately.')) {
      try {
        const response = await fetch('http://localhost:8000/api/pause-scraper', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        })
        const result = await response.json()
        if (result.success) {
          // Add to job history
          const jobEntry = {
            id: `aborted_${Date.now()}`,
            startTime: new Date(),
            endTime: new Date(),
            status: 'aborted' as const,
            policiesProcessed: realtimeStats.policiesProcessed,
            totalPolicies: realtimeStats.totalPolicies
          }
          setJobHistory(prev => [jobEntry, ...prev.slice(0, 9)]) // Keep last 10 jobs
          
          setScraping(false)
          setIsPaused(false)
          setRealtimeStats(prev => ({ ...prev, isScraping: false, currentTask: null }))
          showToast('Scraping job aborted successfully!', 'info')
        } else {
          throw new Error(result.message || 'Failed to abort scraper')
        }
      } catch (error) {
        console.error('Error aborting scraper:', error)
        showToast('Failed to abort scraper: ' + error, 'error')
      }
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
          
          {/* Real-time Stats Section */}
          <div className="stats-section">
            <div className="stats-title">
              <i className="fas fa-chart-line"></i>
              Live Stats
              {isRefreshing && (
                <span className="refresh-indicator">
                  <i className="fas fa-sync-alt fa-spin"></i>
                  Updating...
                </span>
              )}
            </div>
            
            {realtimeStats.isScraping ? (
              <div className="scraping-stats">
                <div className="scraping-indicator">
                  <i className="fas fa-spinner fa-spin"></i>
                  <span>Scraping in Progress</span>
                </div>
                <div className="progress-bar">
                  <div 
                    className="progress-fill" 
                    style={{ width: `${(realtimeStats.progress / Math.max(realtimeStats.totalPolicies, 1)) * 100}%` }}
                  ></div>
                </div>
                <div className="progress-text">
                  {realtimeStats.policiesProcessed > 0 ? `${realtimeStats.policiesProcessed} / ${realtimeStats.totalPolicies} policies` : 'Processing policies...'}
                </div>
                <div className="current-policy">
              <i className="fas fa-file-alt"></i>
                  {realtimeStats.currentPolicy}
                </div>
              </div>
            ) : (
              <div className="static-stats">
                <div className="stat-item">
                  <div className="stat-number">{stats.totalPolicies}</div>
                  <div className="stat-label">Total Policies</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.totalCodes}</div>
                  <div className="stat-label">Medical Codes</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.totalDocuments}</div>
                  <div className="stat-label">References</div>
                </div>
                <div className="stat-item">
                  <div className="stat-number">{stats.totalChanges}</div>
                  <div className="stat-label">Changes</div>
                </div>
              </div>
            )}
          </div>

          {/* Job History Section */}
          <div className="stats-section">
            <div className="stats-title">
              <i className="fas fa-history"></i>
              Job History
            </div>
            
            <div className="job-history">
              {jobHistory.length === 0 ? (
                <div className="no-history">
              <i className="fas fa-clock"></i>
                  <span>No jobs completed yet</span>
                </div>
              ) : (
                <div className="history-list">
                  {jobHistory.slice(0, 5).map((job) => (
                    <div key={job.id} className="history-item">
                      <div className="history-status">
                        <i className={`fas ${job.status === 'completed' ? 'fa-check-circle' : job.status === 'failed' ? 'fa-times-circle' : 'fa-stop-circle'}`}></i>
                        <span className={`status-text ${job.status}`}>{job.status}</span>
                      </div>
                      <div className="history-details">
                        <div className="history-time">
                          {job.startTime.toLocaleTimeString()}
                        </div>
                        <div className="history-progress">
                          {job.policiesProcessed}/{job.totalPolicies} policies
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="main-content">
          <header className="main-header">
            <h1 className="page-title">
              All Policies
            </h1>
            
            {/* Monthly PDF Selection Dropdown */}
            <div className="monthly-dropdown-section">
              <div className="dropdown-trigger" onClick={() => {
                console.log('🖱️ Dropdown clicked, current state:', { dropdownOpen, policyOptionsLength: policyOptions.length })
                setDropdownOpen(!dropdownOpen)
              }}>
                <div className="trigger-content">
                  <span className="trigger-icon">📅</span>
                  <span className="trigger-text">
                    {selectedOptions.length === 0 
                      ? 'Select Policy Options to Scrape' 
                      : `${selectedOptions.length} option${selectedOptions.length === 1 ? '' : 's'} selected`
                    }
                  </span>
                  <span className="trigger-arrow">{dropdownOpen ? '▲' : '▼'}</span>
                </div>
              </div>
              
              {dropdownOpen && (
                <div className="dropdown-content">
                  <div className="dropdown-header">
                  <div className="header-info">
                    <span className="header-title">Policy Options ({policyOptions.length})</span>
                    <span className="header-subtitle">
                      {selectedOptions.length === 0 ? 'All options will be scraped' : `${selectedOptions.length} selected`}
                    </span>
                  </div>
                  <div className="header-actions">
                    <button
                      onClick={() => setSelectedOptions([])}
                      className="mini-btn"
                      disabled={scraping || clearing || selectedOptions.length === 0}
                    >
                      Clear
                    </button>
                    <button
                      onClick={() => setSelectedOptions(policyOptions.map(option => option.value))}
                      className="mini-btn"
                      disabled={scraping || clearing}
                    >
                      All
                    </button>
                  </div>
                  </div>
                  
                  <div className="search-section">
              <input 
                type="text" 
                      placeholder="🔍 Search policy options..."
                      value={optionFilter}
                      onChange={(e) => setOptionFilter(e.target.value)}
                className="search-input" 
                      disabled={scraping || clearing}
              />
            </div>
                  
                  <div className="options-container">
                    {loadingOptions ? (
                      <div className="loading-state">🔄 Loading...</div>
                    ) : policyOptions.length === 0 ? (
                      <div className="loading-state">❌ No policy options available</div>
                    ) : (
                      policyOptions
                        .filter(option => 
                          option.label.toLowerCase().includes(optionFilter.toLowerCase()) ||
                          option.category.toLowerCase().includes(optionFilter.toLowerCase())
                        )
                        .map((option) => (
                          <label key={option.value} className="option-item">
                            <input
                              type="checkbox"
                              value={option.value}
                              checked={selectedOptions.includes(option.value)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setSelectedOptions([...selectedOptions, option.value])
                                } else {
                                  setSelectedOptions(selectedOptions.filter(opt => opt !== option.value))
                                }
                              }}
                              disabled={scraping || clearing}
                              className="option-checkbox"
                            />
                            <span className="option-label">
                              <span className="option-title">{option.label}</span>
                              <span className="option-category">({option.category})</span>
                            </span>
                          </label>
                        ))
                    )}
                  </div>
                </div>
              )}
            </div>
            
            <div className="actions">
              <button 
                onClick={runScraper}
                disabled={scraping || clearing}
                className={`action-btn ${scraping ? 'loading' : 'success'}`}
              >
                {scraping ? '⏳ Scraping...' : '🚀 Run Scraper'}
              </button>
        {scraping && (
          <>
              <button 
              onClick={isPaused ? resumeScraper : pauseScraper}
              disabled={clearing}
              className={`action-btn ${isPaused ? 'success' : 'warning'}`}
              >
              {isPaused ? '▶️ Resume' : '⏸️ Pause'}
              </button>
              <button 
              onClick={abortScraper}
              disabled={clearing}
              className="action-btn danger"
              >
              🛑 Abort
              </button>
          </>
        )}
              <button 
                onClick={clearScreen}
                disabled={scraping || clearing}
                className="action-btn secondary"
              >
                🧹 Clear Screen
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
            {/* Policies List */}
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
                      {policies.map((policy) => (
                        <tr 
                          key={policy.id} 
                          className="policy-row"
                          onClick={() => showPolicyDetail(policy)}
                        >
                          <td>
                            <div className="policy-title">{policy.title}</div>
                          </td>
                          <td>
                            <span className={`category-badge ${getCategoryBadgeClass(policy.category)}`}>
                              {policy.category && policy.category !== 'N/A' ? policy.category : 'Policy Update'}
                            </span>
                            <div className="status-badge">
                              {policy.status && policy.status !== 'N/A' ? policy.status : 'Active'}
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
          </div>
        </main>

        {/* Detail Panel */}
        {selectedPolicy && (
          <aside className="detail-panel active">
            <div className="detail-header">
              <div className="detail-title-section">
              <div className="detail-title">{selectedPolicy.title}</div>
                <button 
                  className="close-button" 
                  onClick={() => setSelectedPolicy(null)}
                  aria-label="Close panel"
                >
                  <i className="fas fa-times"></i>
                </button>
              </div>
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

        .stats-section {
          padding: 20px;
          border-bottom: 1px solid #e1e4e8;
        }

        .stats-title {
          font-size: 14px;
          font-weight: 600;
          color: #586069;
          margin-bottom: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .refresh-indicator {
          margin-left: auto;
          color: #6c757d;
          font-size: 11px;
          font-weight: normal;
          opacity: 0.8;
        }

        .scraping-stats {
          background: #f6f8fa;
          border-radius: 8px;
          padding: 16px;
          border: 1px solid #e1e4e8;
        }

        .scraping-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 12px;
          color: #0066cc;
          font-weight: 500;
        }

        .progress-bar {
          width: 100%;
          height: 8px;
          background: #e1e4e8;
          border-radius: 4px;
          overflow: hidden;
          margin-bottom: 8px;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #0066cc, #4dabf7);
          transition: width 0.3s ease;
        }

        .progress-text {
          font-size: 12px;
          color: #586069;
          margin-bottom: 8px;
        }

        .current-policy {
          font-size: 12px;
          color: #24292e;
          display: flex;
          align-items: center;
          gap: 6px;
          background: #ffffff;
          padding: 8px;
          border-radius: 4px;
          border: 1px solid #e1e4e8;
        }

        .static-stats {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 12px;
        }

        /* Job History Styles */
        .job-history {
          margin-top: 8px;
        }

        .no-history {
          display: flex;
          align-items: center;
          gap: 8px;
          color: #9ca3af;
          font-size: 12px;
          padding: 12px;
          text-align: center;
          justify-content: center;
        }

        .history-list {
          max-height: 200px;
          overflow-y: auto;
        }

        .history-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 8px 12px;
          border-bottom: 1px solid #f3f4f6;
          font-size: 12px;
        }

        .history-item:last-child {
          border-bottom: none;
        }

        .history-status {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .history-status i {
          font-size: 14px;
        }

        .status-text {
          font-weight: 500;
          text-transform: capitalize;
        }

        .status-text.completed {
          color: #10b981;
        }

        .status-text.failed {
          color: #ef4444;
        }

        .status-text.aborted {
          color: #f59e0b;
        }

        .history-details {
          text-align: right;
          color: #6b7280;
        }

        .history-time {
          font-weight: 500;
        }

        .history-progress {
          font-size: 11px;
          margin-top: 2px;
        }

        .stat-item {
          text-align: center;
          padding: 12px;
          background: #f6f8fa;
          border-radius: 6px;
          border: 1px solid #e1e4e8;
        }

        .stat-item .stat-number {
          font-size: 18px;
          font-weight: 700;
          color: #0066cc;
          margin-bottom: 4px;
        }

        .stat-item .stat-label {
          font-size: 11px;
          color: #586069;
          text-transform: uppercase;
          letter-spacing: 0.5px;
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
          position: relative;
          overflow: visible;
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

        .monthly-dropdown-section {
          position: relative;
          margin: 16px 0;
        }

        .dropdown-trigger {
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          padding: 12px 16px;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .dropdown-trigger:hover {
          border-color: #3b82f6;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .trigger-content {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .trigger-icon {
          font-size: 18px;
        }

        .trigger-text {
          flex: 1;
          font-size: 14px;
          font-weight: 500;
          color: #374151;
        }

        .trigger-arrow {
          font-size: 12px;
          color: #6b7280;
          transition: transform 0.2s ease;
        }

        .dropdown-content {
          position: absolute;
          top: 100%;
          left: 0;
          right: 0;
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
          z-index: 1000;
          margin-top: 4px;
          max-height: 400px;
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }

        .dropdown-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          border-bottom: 1px solid #e5e7eb;
          background: #f9fafb;
        }

        .header-info {
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .header-title {
          font-size: 14px;
          font-weight: 600;
          color: #1f2937;
        }

        .header-subtitle {
          font-size: 12px;
          color: #6b7280;
        }

        .header-actions {
          display: flex;
          gap: 8px;
        }

        .mini-btn {
          padding: 4px 8px;
          font-size: 12px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          background: white;
          color: #374151;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .mini-btn:hover:not(:disabled) {
          background: #f3f4f6;
          border-color: #9ca3af;
        }

        .mini-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .search-section {
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
        }

        .search-input {
          width: 100%;
          padding: 8px 12px;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          font-size: 14px;
          background: white;
          color: #374151;
        }

        .search-input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        .search-input:disabled {
          background: #f3f4f6;
          color: #9ca3af;
          cursor: not-allowed;
        }

        .options-container {
          max-height: 250px;
          overflow-y: auto;
          padding: 8px;
        }

        .loading-state {
          text-align: center;
          padding: 20px;
          color: #6b7280;
          font-size: 14px;
        }

        .option-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px 12px;
          border-radius: 6px;
          cursor: pointer;
          transition: background-color 0.2s ease;
        }

        .option-item:hover {
          background: #f3f4f6;
        }

        .option-checkbox {
          width: 16px;
          height: 16px;
          accent-color: #3b82f6;
          cursor: pointer;
        }

        .option-checkbox:disabled {
          cursor: not-allowed;
          opacity: 0.5;
        }

        .option-label {
          font-size: 14px;
          color: #374151;
          cursor: pointer;
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .option-title {
          font-weight: 500;
          color: #1f2937;
        }

        .option-category {
          font-size: 12px;
          color: #6b7280;
          font-style: italic;
        }

        .option-item:has(.option-checkbox:disabled) .option-label {
          color: #9ca3af;
          cursor: not-allowed;
        }

        .option-item:has(.option-checkbox:disabled) .option-title {
          color: #9ca3af;
        }

        .option-item:has(.option-checkbox:disabled) .option-category {
          color: #9ca3af;
        }


        .action-btn.secondary {
          background: #f3f4f6;
          color: #374151;
          border-color: #d1d5db;
        }

        .action-btn.secondary:hover:not(:disabled) {
          background: #e5e7eb;
          border-color: #9ca3af;
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

        .action-btn.warning {
          background: #f59e0b;
          color: white;
          border-color: #f59e0b;
        }

        .action-btn.warning:hover:not(:disabled) {
          background: #d97706;
          border-color: #d97706;
        }

        .action-btn.danger {
          background: #dc2626;
          color: white;
          border-color: #dc2626;
        }
        .action-btn.danger:hover:not(:disabled) {
          background: #b91c1c;
          border-color: #b91c1c;
        }

        .action-btn.secondary {
          background: #6b7280;
          color: white;
          border-color: #6b7280;
        }
        .action-btn.secondary:hover:not(:disabled) {
          background: #4b5563;
          border-color: #4b5563;
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

        .detail-title-section {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 8px;
        }

        .detail-title {
          font-size: 18px;
          font-weight: 600;
          color: #1a1a1a;
          line-height: 1.4;
          flex: 1;
          margin-right: 12px;
        }

        .close-button {
          background: none;
          border: none;
          color: #6b7280;
          cursor: pointer;
          padding: 4px;
          border-radius: 4px;
          transition: all 0.2s ease;
          display: flex;
          align-items: center;
          justify-content: center;
          width: 28px;
          height: 28px;
          flex-shrink: 0;
        }

        .close-button:hover {
          background-color: #f3f4f6;
          color: #374151;
        }

        .close-button:active {
          background-color: #e5e7eb;
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
          
          .monthly-dropdown-section {
            margin: 12px 0;
          }

          .dropdown-trigger {
            padding: 10px 12px;
          }

          .trigger-text {
            font-size: 13px;
          }

          .dropdown-content {
            max-height: 350px;
          }

          .options-container {
            max-height: 200px;
          }

          .selection-actions {
            flex-direction: row;
            justify-content: center;
          }
          
          .actions {
            order: -1;
            width: 100%;
            justify-content: center;
            margin-bottom: 16px;
          }
        }

        /* Toast Notification Styles */
        .toast {
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 1000;
          min-width: 300px;
          max-width: 500px;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
          animation: slideIn 0.3s ease-out;
        }

        .toast-success {
          background: #10b981;
          color: white;
        }

        .toast-error {
          background: #ef4444;
          color: white;
        }

        .toast-info {
          background: #3b82f6;
          color: white;
        }

        .toast-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px 20px;
        }

        .toast-message {
          flex: 1;
          font-weight: 500;
        }

        .toast-close {
          background: none;
          border: none;
          color: inherit;
          font-size: 20px;
          cursor: pointer;
          margin-left: 12px;
          opacity: 0.8;
        }

        .toast-close:hover {
          opacity: 1;
        }

        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>

      {/* Toast Notification */}
      {toast && (
        <div className={`toast toast-${toast.type}`}>
          <div className="toast-content">
            <span className="toast-message">{toast.message}</span>
            <button className="toast-close" onClick={() => setToast(null)}>×</button>
          </div>
        </div>
      )}
    </>
  )
}
