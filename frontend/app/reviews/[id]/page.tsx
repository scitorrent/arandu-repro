'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import ClaimCard from '@/components/review/ClaimCard'
import ChecklistPanel from '@/components/review/ChecklistPanel'
import ScorePanel from '@/components/review/ScorePanel'
import ArtifactsPanel from '@/components/review/ArtifactsPanel'

interface Review {
  id: string
  status: string
  paper_meta: {
    title?: string
    authors?: string[]
    venue?: string
  } | null
  claims: Array<{
    id: string
    text: string
    section?: string
  }> | null
  citations: Record<string, Array<{
    title: string
    authors: string[]
    score_final: number
  }>> | null
  checklist: {
    items: Array<{
      key: string
      status: string
      evidence?: string
    }>
    summary: string
  } | null
  quality_score: {
    value_0_100: number
    tier: string
    narrative?: {
      executive_justification: string[]
      technical_deepdive: string
    }
  } | null
  badges: {
    claim_mapped: boolean
    method_check: string
    citations_augmented: boolean
  } | null
  html_report_path?: string
  json_summary_path?: string
}

type Tab = 'overview' | 'claims' | 'checklist' | 'score' | 'artifacts'

export default function ReviewDetailPage() {
  const params = useParams()
  const reviewId = params.id as string
  const [review, setReview] = useState<Review | null>(null)
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchReview = async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/reviews/${reviewId}`)
        if (!response.ok) throw new Error('Failed to fetch review')
        const data = await response.json()
        setReview(data)
      } catch (err) {
        console.error('Error fetching review:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchReview()

    // Auto-refresh if processing
    const interval = setInterval(() => {
      if (review?.status === 'processing' || review?.status === 'pending') {
        fetchReview()
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [reviewId, review?.status])

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-text-secondary">Loading...</div>
      </div>
    )
  }

  if (!review) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-error">Review not found</div>
      </div>
    )
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'claims', label: 'Claims' },
    { id: 'checklist', label: 'Checklist' },
    { id: 'score', label: 'Score' },
    { id: 'artifacts', label: 'Artifacts' },
  ]

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="bg-bg-secondary border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="text-xl font-semibold text-primary">
              Arandu CoReview Studio
            </a>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-3xl font-semibold mb-2">
            {review.paper_meta?.title || 'Untitled Paper'}
          </h1>
          {review.paper_meta?.authors && (
            <div className="text-text-secondary">
              {review.paper_meta.authors.join(', ')}
            </div>
          )}
          <div className="mt-4 flex gap-2">
            {review.badges && (
              <>
                {review.badges.claim_mapped && (
                  <img
                    src={`http://localhost:8000/api/v1/badges/${reviewId}/claim-mapped.svg`}
                    alt="Claim-mapped"
                    className="h-5"
                  />
                )}
                <img
                  src={`http://localhost:8000/api/v1/badges/${reviewId}/method-check.svg`}
                  alt="Method-check"
                  className="h-5"
                />
                {review.badges.citations_augmented && (
                  <img
                    src={`http://localhost:8000/api/v1/badges/${reviewId}/citations-augmented.svg`}
                    alt="Citations-augmented"
                    className="h-5"
                  />
                )}
              </>
            )}
          </div>
        </header>

        {/* Tabs */}
        <div className="border-b border-border mb-6">
          <nav className="flex gap-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`pb-4 px-2 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary text-primary font-medium'
                    : 'border-transparent text-text-secondary hover:text-text-primary'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div>
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
                <h2 className="text-xl font-semibold mb-4">Summary</h2>
                <p className="text-text-secondary">
                  {review.claims?.length || 0} claims extracted.
                  {review.checklist?.summary && ` ${review.checklist.summary}`}
                </p>
              </div>
              {review.quality_score?.narrative?.executive_justification && (
                <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
                  <h2 className="text-xl font-semibold mb-4">Recommendations</h2>
                  <ul className="list-disc list-inside space-y-2 text-text-secondary">
                    {review.quality_score.narrative.executive_justification.map((bullet, i) => (
                      <li key={i}>{bullet}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {activeTab === 'claims' && (
            <div className="space-y-4">
              {review.claims?.map((claim) => (
                <ClaimCard
                  key={claim.id}
                  claim={claim}
                  citations={review.citations?.[claim.id] || []}
                  reviewId={reviewId}
                />
              ))}
            </div>
          )}

          {activeTab === 'checklist' && (
            <ChecklistPanel checklist={review.checklist} />
          )}

          {activeTab === 'score' && (
            <ScorePanel
              qualityScore={review.quality_score}
              reviewId={reviewId}
            />
          )}

          {activeTab === 'artifacts' && (
            <ArtifactsPanel
              reviewId={reviewId}
              htmlReportPath={review.html_report_path}
              jsonSummaryPath={review.json_summary_path}
            />
          )}
        </div>
      </main>
    </div>
  )
}

