import { useState } from 'react'
import { PolicyUpdate } from '../types/policy'
import { format } from 'date-fns'
import { ChevronDownIcon, ChevronUpIcon, ExternalLinkIcon } from '@heroicons/react/24/outline'

interface PolicyCardProps {
  policy: PolicyUpdate
}

export function PolicyCard({ policy }: PolicyCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'No date available'
    try {
      return format(new Date(dateString), 'MMM dd, yyyy')
    } catch {
      return 'Invalid date'
    }
  }

  const truncateText = (text: string, maxLength: number = 200) => {
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {policy.title}
          </h3>
          <div className="flex flex-wrap gap-4 text-sm text-gray-500">
            <span className="flex items-center">
              <span className="font-medium">Published:</span>
              <span className="ml-1">{formatDate(policy.published_date)}</span>
            </span>
            {policy.category && (
              <span className="flex items-center">
                <span className="font-medium">Category:</span>
                <span className="ml-1 bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                  {policy.category}
                </span>
              </span>
            )}
            {policy.month_year && (
              <span className="flex items-center">
                <span className="font-medium">Month:</span>
                <span className="ml-1">{policy.month_year}</span>
              </span>
            )}
          </div>
        </div>
        <div className="flex space-x-2 ml-4">
          <a
            href={policy.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700"
            title="View original policy"
          >
            <ExternalLinkIcon className="h-5 w-5" />
          </a>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600"
            title={isExpanded ? 'Collapse' : 'Expand'}
          >
            {isExpanded ? (
              <ChevronUpIcon className="h-5 w-5" />
            ) : (
              <ChevronDownIcon className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>

      <div className="text-gray-700 mb-4">
        {isExpanded ? (
          <div className="whitespace-pre-wrap">{policy.body_content}</div>
        ) : (
          <p>{truncateText(policy.body_content)}</p>
        )}
      </div>

      {isExpanded && (
        <div className="border-t pt-4">
          <div className="text-sm text-gray-500">
            <span className="font-medium">Created:</span> {formatDate(policy.created_at)}
            {policy.updated_at !== policy.created_at && (
              <>
                <span className="mx-2">•</span>
                <span className="font-medium">Updated:</span> {formatDate(policy.updated_at)}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
