'use client'

import { useState } from 'react'
import NarrationDrawer from './NarrationDrawer'

interface ScorePanelProps {
  qualityScore: {
    value_0_100: number
    tier: string
    narrative?: {
      executive_justification: string[]
      technical_deepdive: string
    }
  } | null
  reviewId: string
}

export default function ScorePanel({ qualityScore, reviewId }: ScorePanelProps) {
  const [showNarration, setShowNarration] = useState(false)

  if (!qualityScore) {
    return (
      <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
        <p className="text-text-secondary">Quality score not available</p>
      </div>
    )
  }

  const tierColors: Record<string, string> = {
    A: 'text-success',
    B: 'text-secondary',
    C: 'text-warning',
    D: 'text-error',
  }

  const tierColor = tierColors[qualityScore.tier] || 'text-text-secondary'

  return (
    <>
      <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
        <h2 className="text-xl font-semibold mb-6">Quality Score</h2>

        <div className="flex items-center gap-8 mb-6">
          <div className={`text-6xl font-bold ${tierColor}`}>
            {qualityScore.value_0_100.toFixed(1)}
          </div>
          <div>
            <div className={`text-2xl font-semibold ${tierColor}`}>
              Tier {qualityScore.tier}
            </div>
            <div className="text-sm text-text-secondary">Out of 100</div>
          </div>
        </div>

        {qualityScore.narrative && (
          <button
            onClick={() => setShowNarration(true)}
            className="px-4 py-2 bg-primary text-text-inverse rounded-md font-medium hover:bg-primary-dark transition-colors"
          >
            View Explanation
          </button>
        )}
      </div>

      {showNarration && qualityScore.narrative && (
        <NarrationDrawer
          narrative={qualityScore.narrative}
          onClose={() => setShowNarration(false)}
        />
      )}
    </>
  )
}

