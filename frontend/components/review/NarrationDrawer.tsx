'use client'

interface NarrationDrawerProps {
  narrative: {
    executive_justification: string[]
    technical_deepdive: string
  }
  onClose: () => void
}

export default function NarrationDrawer({ narrative, onClose }: NarrationDrawerProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-bg-secondary rounded-lg shadow-lg max-w-3xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-semibold">Score Explanation</h2>
            <button
              onClick={onClose}
              className="text-text-secondary hover:text-text-primary"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold mb-3">Executive Summary</h3>
              <ul className="list-disc list-inside space-y-2 text-text-secondary">
                {narrative.executive_justification.map((bullet, i) => (
                  <li key={i}>{bullet}</li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold mb-3">Technical Details</h3>
              <pre className="bg-bg-tertiary p-4 rounded-md text-sm whitespace-pre-wrap text-text-secondary">
                {narrative.technical_deepdive}
              </pre>
            </div>
          </div>

          <div className="mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-primary text-text-inverse rounded-md font-medium hover:bg-primary-dark transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

