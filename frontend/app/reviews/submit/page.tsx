'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function SubmitReviewPage() {
  const router = useRouter()
  const [url, setUrl] = useState('')
  const [doi, setDoi] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validation
    if (!url && !doi && !pdfFile) {
      setError('At least one of URL, DOI, or PDF file must be provided')
      return
    }

    setIsSubmitting(true)

    try {
      const formData = new FormData()
      if (url) formData.append('url', url)
      if (doi) formData.append('doi', doi)
      if (repoUrl) formData.append('repo_url', repoUrl)
      if (pdfFile) formData.append('pdf_file', pdfFile)

      const response = await fetch('http://localhost:8000/api/v1/reviews', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to submit review')
      }

      const data = await response.json()
      router.push(`/reviews/${data.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to submit review')
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="bg-bg-secondary border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <a href="/" className="text-xl font-semibold text-primary">
              Arandu CoReview Studio
            </a>
            <a href="/reviews/submit" className="text-text-secondary hover:text-primary">
              Submit Review
            </a>
          </div>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="text-3xl font-semibold mb-8">Submit Review</h1>

        <form onSubmit={handleSubmit} className="bg-bg-secondary rounded-lg shadow-sm p-6 space-y-6">
          {error && (
            <div className="bg-error-light border border-error rounded-md p-4 text-error">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="url" className="block text-sm font-medium mb-2">
              Paper URL
            </label>
            <input
              type="url"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-lighter"
              placeholder="https://arxiv.org/abs/..."
            />
          </div>

          <div>
            <label htmlFor="doi" className="block text-sm font-medium mb-2">
              DOI
            </label>
            <input
              type="text"
              id="doi"
              value={doi}
              onChange={(e) => setDoi(e.target.value)}
              className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-lighter"
              placeholder="10.1234/example"
            />
          </div>

          <div>
            <label htmlFor="pdf" className="block text-sm font-medium mb-2">
              PDF File (optional if URL/DOI provided)
            </label>
            <input
              type="file"
              id="pdf"
              accept=".pdf"
              onChange={(e) => setPdfFile(e.target.files?.[0] || null)}
              className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-lighter"
            />
            <p className="text-sm text-text-secondary mt-1">Max 25MB</p>
          </div>

          <div>
            <label htmlFor="repo" className="block text-sm font-medium mb-2">
              GitHub Repository (optional)
            </label>
            <input
              type="url"
              id="repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full px-4 py-2 border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-primary-lighter"
              placeholder="https://github.com/user/repo"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-primary text-text-inverse px-6 py-3 rounded-md font-medium hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Review'}
          </button>
        </form>
      </main>
    </div>
  )
}

