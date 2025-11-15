'use client'

interface ChecklistPanelProps {
  checklist: {
    items: Array<{
      key: string
      status: string
      evidence?: string
    }>
    summary: string
  } | null
}

export default function ChecklistPanel({ checklist }: ChecklistPanelProps) {
  if (!checklist || !checklist.items) {
    return (
      <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
        <p className="text-text-secondary">Checklist not available</p>
      </div>
    )
  }

  const statusColors: Record<string, { bg: string; text: string }> = {
    ok: { bg: 'bg-success-light', text: 'text-success' },
    partial: { bg: 'bg-warning-light', text: 'text-warning' },
    missing: { bg: 'bg-error-light', text: 'text-error' },
  }

  return (
    <div className="bg-bg-secondary rounded-lg shadow-sm p-6">
      <h2 className="text-xl font-semibold mb-4">Method Checklist</h2>
      <p className="text-sm text-text-secondary mb-6">{checklist.summary}</p>

      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            <th className="text-left py-3 text-sm font-semibold text-text-secondary uppercase">
              Item
            </th>
            <th className="text-left py-3 text-sm font-semibold text-text-secondary uppercase">
              Status
            </th>
            <th className="text-left py-3 text-sm font-semibold text-text-secondary uppercase">
              Evidence
            </th>
          </tr>
        </thead>
        <tbody>
          {checklist.items.map((item, i) => {
            const colors = statusColors[item.status] || { bg: 'bg-bg-tertiary', text: 'text-text-secondary' }
            return (
              <tr key={i} className="border-b border-border-light">
                <td className="py-3 text-text-primary">
                  {item.key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}
                </td>
                <td className="py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors.bg} ${colors.text}`}>
                    {item.status.toUpperCase()}
                  </span>
                </td>
                <td className="py-3 text-sm text-text-secondary">
                  {item.evidence || 'N/A'}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

