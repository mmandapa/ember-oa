import { useState } from 'react'
import { FunnelIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface FilterPanelProps {
  categories: string[]
  months: string[]
  selectedCategory: string
  selectedMonth: string
  onCategoryFilter: (category: string) => void
  onMonthFilter: (month: string) => void
  onClearFilters: () => void
}

export function FilterPanel({
  categories,
  months,
  selectedCategory,
  selectedMonth,
  onCategoryFilter,
  onMonthFilter,
  onClearFilters
}: FilterPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const hasActiveFilters = selectedCategory || selectedMonth

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900 flex items-center">
          <FunnelIcon className="h-5 w-5 mr-2" />
          Filters
        </h3>
        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="text-sm text-primary-600 hover:text-primary-700 flex items-center"
          >
            <XMarkIcon className="h-4 w-4 mr-1" />
            Clear All
          </button>
        )}
      </div>

      <div className="space-y-4">
        {/* Category Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <select
            value={selectedCategory}
            onChange={(e) => onCategoryFilter(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
        </div>

        {/* Month Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Month
          </label>
          <select
            value={selectedMonth}
            onChange={(e) => onMonthFilter(e.target.value)}
            className="block w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
          >
            <option value="">All Months</option>
            {months.map((month) => (
              <option key={month} value={month}>
                {month}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Active Filters Summary */}
      {hasActiveFilters && (
        <div className="pt-4 border-t">
          <div className="text-sm text-gray-600">
            <span className="font-medium">Active filters:</span>
            <div className="mt-1 space-y-1">
              {selectedCategory && (
                <div className="flex items-center">
                  <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs mr-2">
                    Category: {selectedCategory}
                  </span>
                </div>
              )}
              {selectedMonth && (
                <div className="flex items-center">
                  <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs mr-2">
                    Month: {selectedMonth}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
