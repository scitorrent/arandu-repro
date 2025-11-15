import Link from 'next/link'

export default function Home() {
  return (
    <div className="min-h-screen bg-bg-primary">
      <nav className="bg-bg-secondary border-b border-border">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Link href="/" className="text-xl font-semibold text-primary">
              Arandu CoReview Studio
            </Link>
            <div className="flex gap-6">
              <Link href="/reviews/submit" className="text-text-secondary hover:text-primary">
                Submit Review
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-semibold text-text-primary mb-4">
            Arandu CoReview Studio
          </h1>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            Review-first scientific paper analysis with claims extraction, citation suggestions,
            method checklist, and quality scoring.
          </p>
        </div>

        <div className="flex justify-center">
          <Link
            href="/reviews/submit"
            className="bg-primary text-text-inverse px-6 py-3 rounded-md font-medium hover:bg-primary-dark transition-colors"
          >
            Submit a Review
          </Link>
        </div>
      </main>
    </div>
  )
}

