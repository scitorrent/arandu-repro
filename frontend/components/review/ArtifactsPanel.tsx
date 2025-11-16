'use client'

import { useState } from 'react'
import BadgeTile from './BadgeTile'

interface ArtifactsPanelProps {
  reviewId: string
  htmlReportPath?: string
  jsonSummaryPath?: string
}

export default function ArtifactsPanel({
  reviewId,
  htmlReportPath,
  jsonSummaryPath,
}: ArtifactsPanelProps) {
  const [copied, setCopied] = useState(false)

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000'

  return (
    <div className="space-y-6">
      <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Downloads</h2>
        <div className="space-y-3">
          {htmlReportPath && (
            <a
              href={`${baseUrl}/api/v1/reviews/${reviewId}/artifacts/report.html`}
              download
              className="block w-full px-4 py-3 bg-primary text-text-inverse rounded-md font-medium hover:bg-primary-dark transition-colors text-center"
            >
              Download HTML Report
            </a>
          )}
          {jsonSummaryPath && (
            <a
              href={`${baseUrl}/api/v1/reviews/${reviewId}/artifacts/review.json`}
              download
              className="block w-full px-4 py-3 bg-bg-tertiary text-text-primary rounded-md font-medium hover:bg-border transition-colors text-center"
            >
              Download JSON Summary
            </a>
          )}
        </div>
      </div>

      <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-4">Badges</h2>
        <div className="space-y-4">
          <BadgeTile reviewId={reviewId} badgeType="claim-mapped" />
          <BadgeTile reviewId={reviewId} badgeType="method-check" />
          <BadgeTile reviewId={reviewId} badgeType="citations-augmented" />
        </div>
      </div>
    </div>
  )
}

