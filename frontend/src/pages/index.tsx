import { useState, useEffect } from 'react'
import Head from 'next/head'
import { supabase } from '../utils/supabase'
import { PolicyUpdate } from '../types/policy'

export default function Home() {
  const [policies, setPolicies] = useState<PolicyUpdate[]>([])
  const [loading, setLoading] = useState(true)
  const [scraping, setScraping] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchPolicies()
  }, [])

  const fetchPolicies = async () => {
    try {
      setLoading(true)
      const { data, error } = await supabase
        .from('policy_updates')
        .select('*')
        .order('published_date', { ascending: false })
        .limit(50)

      if (error) throw error
      setPolicies(data || [])
    } catch (error) {
      console.error('Error fetching policies:', error)
    } finally {
      setLoading(false)
    }
  }

  const runScraper = async () => {
    try {
      setScraping(true)
      const response = await fetch('/api/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      const result = await response.json()
      
      if (result.success) {
        // Refresh policies after successful scraping
        await fetchPolicies()
        alert('Scraper completed successfully!')
      } else {
        alert(`Scraper failed: ${result.message}`)
      }
    } catch (error) {
      console.error('Error running scraper:', error)
      alert('Failed to run scraper')
    } finally {
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
        .neq('id', '00000000-0000-0000-0000-000000000000') // Delete all rows

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

      // Refresh the policies list
      await fetchPolicies()
      alert('All data cleared successfully!')
      
    } catch (error) {
      console.error('Error clearing data:', error)
      alert('Failed to clear data')
    } finally {
      setClearing(false)
    }
  }

  const filteredPolicies = policies.filter(policy =>
    policy.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    policy.body_content.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <>
      <Head>
        <title>Cigna Policy Scraper</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm">
          <div className="max-w-6xl mx-auto px-4 py-6">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-gray-900">
                Cigna Policy Updates
              </h1>
              <div className="flex space-x-3">
                <button
                  onClick={fetchPolicies}
                  className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                >
                  Refresh Data
                </button>
                <button
                  onClick={runScraper}
                  disabled={scraping || clearing}
                  className={`px-4 py-2 rounded text-white ${
                    scraping 
                      ? 'bg-orange-500 cursor-not-allowed' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {scraping ? 'Scraping...' : 'Run Scraper'}
                </button>
                <button
                  onClick={clearAllData}
                  disabled={scraping || clearing}
                  className={`px-4 py-2 rounded text-white ${
                    clearing 
                      ? 'bg-red-500 cursor-not-allowed' 
                      : 'bg-red-600 hover:bg-red-700'
                  }`}
                >
                  {clearing ? 'Clearing...' : 'Clear All Data'}
                </button>
              </div>
            </div>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-4 py-8">
          {/* Search */}
          <div className="mb-6">
            <input
              type="text"
              placeholder="Search policies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          {/* Stats */}
          <div className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Total Policies</div>
              <div className="text-2xl font-bold text-gray-900">{policies.length}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Filtered Results</div>
              <div className="text-2xl font-bold text-gray-900">{filteredPolicies.length}</div>
            </div>
            <div className="bg-white p-4 rounded-lg shadow">
              <div className="text-sm text-gray-500">Status</div>
              <div className={`text-2xl font-bold ${
                clearing ? 'text-red-600' :
                scraping ? 'text-orange-600' : 
                loading ? 'text-blue-600' : 'text-green-600'
              }`}>
                {clearing ? 'Clearing...' : scraping ? 'Scraping...' : loading ? 'Loading...' : 'Ready'}
              </div>
            </div>
          </div>

          {/* Policies List */}
          <div className="space-y-4">
            {loading ? (
              <div className="text-center py-12">
                <div className="text-gray-500">Loading policies...</div>
              </div>
            ) : filteredPolicies.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-gray-500">
                  {policies.length === 0 ? (
                    <p>No policies found. Run the scraper to populate data.</p>
                  ) : (
                    <p>No policies match your search.</p>
                  )}
                </div>
              </div>
            ) : (
              filteredPolicies.map((policy) => (
                <div key={policy.id} className="bg-white p-6 rounded-lg shadow">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {policy.title}
                    </h3>
                    <a
                      href={policy.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-700 text-sm"
                    >
                      View Original →
                    </a>
                  </div>
                  
                  <div className="text-sm text-gray-500 mb-3">
                    {policy.published_date && (
                      <span>Published: {new Date(policy.published_date).toLocaleDateString()}</span>
                    )}
                    {policy.category && (
                      <span className="ml-4">Category: {policy.category}</span>
                    )}
                    {policy.month_year && (
                      <span className="ml-4">Month: {policy.month_year}</span>
                    )}
                  </div>
                  
                  <div className="text-gray-700">
                    {policy.body_content.length > 300 
                      ? `${policy.body_content.substring(0, 300)}...`
                      : policy.body_content
                    }
                  </div>
                </div>
              ))
            )}
          </div>
        </main>
      </div>
    </>
  )
}
