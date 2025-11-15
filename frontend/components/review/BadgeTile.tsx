'use client'

import { useState } from 'react'

interface BadgeTileProps {
  reviewId: string
  badgeType: 'claim-mapped' | 'method-check' | 'citations-augmented'
}

export default function BadgeTile({ reviewId, badgeType }: BadgeTileProps) {
  const [copied, setCopied] = useState(false)

  const baseUrl = 'http://localhost:8000'
  const badgeUrl = `${baseUrl}/api/v1/badges/${reviewId}/${badgeType}.svg`
  const reviewUrl = `${baseUrl}/reviews/${reviewId}`
  const snippet = `[![Arandu: ${badgeType}](${badgeUrl})](${reviewUrl})`

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(snippet)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  return (
    <div className="border border-border rounded-md p-4">
      <div className="flex items-center gap-4 mb-3">
        <img src={badgeUrl} alt={badgeType} className="h-5" />
        <span className="text-sm font-medium text-text-primary">
          {badgeType.replace(/-/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
        </span>
      </div>
      <div className="bg-bg-tertiary rounded-md p-3 mb-3">
        <code className="text-xs text-text-secondary break-all">{snippet}</code>
      </div>
      <button
        onClick={handleCopy}
        className="px-4 py-2 bg-bg-tertiary text-text-primary rounded-md text-sm font-medium hover:bg-border transition-colors"
      >
        {copied ? '✓ Copied!' : 'Copy Snippet'}
      </button>
    </div>
  )
}

