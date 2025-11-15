'use client'

import { useState } from 'react'

interface ClaimCardProps {
  claim: {
    id: string
    text: string
    section?: string
  }
  citations: Array<{
    title: string
    authors: string[]
    score_final: number
  }>
  reviewId: string
}

export default function ClaimCard({ claim, citations, reviewId }: ClaimCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedText, setEditedText] = useState(claim.text)

  const handleAccept = () => {
    // TODO: PATCH /api/v1/reviews/{id} to persist changes
    setIsEditing(false)
  }

  const sectionColors: Record<string, string> = {
    introduction: 'bg-info-light text-info',
    method: 'bg-secondary-lighter text-secondary',
    results: 'bg-success-light text-success',
    discussion: 'bg-warning-light text-warning',
  }

  return (
    <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          {claim.section && (
            <span
              className={`px-2 py-1 rounded-full text-xs font-medium uppercase ${
                sectionColors[claim.section] || 'bg-bg-tertiary text-text-secondary'
              }`}
            >
              {claim.section}
            </span>
          )}
          <span className="text-xs text-text-tertiary">#{claim.id}</span>
        </div>
      </div>

      {isEditing ? (
        <div className="space-y-3">
          <textarea
            value={editedText}
            onChange={(e) => setEditedText(e.target.value)}
            className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-lighter"
            rows={3}
          />
          <div className="flex gap-2">
            <button
              onClick={handleAccept}
              className="px-4 py-2 bg-primary text-text-inverse rounded-md text-sm font-medium hover:bg-primary-dark"
            >
              Save
            </button>
            <button
              onClick={() => {
                setEditedText(claim.text)
                setIsEditing(false)
              }}
              className="px-4 py-2 bg-bg-tertiary text-text-primary rounded-md text-sm font-medium hover:bg-border"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          <p className="text-text-primary">{claim.text}</p>
          <div className="flex gap-2">
            <button
              onClick={() => setIsEditing(true)}
              className="text-sm text-secondary hover:text-secondary-light"
            >
              Edit
            </button>
          </div>
        </div>
      )}

      {citations.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border-light">
          <h4 className="text-sm font-semibold mb-2">Suggested Citations:</h4>
          <ul className="space-y-2">
            {citations.slice(0, 3).map((cit, i) => (
              <li key={i} className="text-sm">
                <a
                  href={cit.title}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-secondary hover:underline"
                >
                  {cit.title}
                </a>
                <span className="text-text-tertiary ml-2">
                  ({cit.authors.slice(0, 2).join(', ')})
                </span>
                <span className="text-text-tertiary ml-2">(score: {cit.score_final.toFixed(2)})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

