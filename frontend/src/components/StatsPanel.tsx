import { ScrapingStats } from '../types/policy'
import { format } from 'date-fns'
import { DocumentTextIcon, CodeBracketIcon, ClockIcon } from '@heroicons/react/24/outline'

interface StatsPanelProps {
  stats: ScrapingStats
}

export function StatsPanel({ stats }: StatsPanelProps) {
  const formatLastScraped = (timestamp: string | null) => {
    if (!timestamp) return 'Never'
    try {
      return format(new Date(timestamp), 'MMM dd, yyyy HH:mm')
    } catch {
      return 'Invalid date'
    }
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
      {/* Total Policies */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <DocumentTextIcon className="h-8 w-8 text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Total Policies</p>
            <p className="text-2xl font-semibold text-gray-900">
              {stats.totalPolicies.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Total Medical Codes */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <CodeBracketIcon className="h-8 w-8 text-green-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Medical Codes</p>
            <p className="text-2xl font-semibold text-gray-900">
              {stats.totalMedicalCodes.toLocaleString()}
            </p>
          </div>
        </div>
      </div>

      {/* Last Scraped */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <ClockIcon className="h-8 w-8 text-purple-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Last Scraped</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatLastScraped(stats.lastScraped)}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
