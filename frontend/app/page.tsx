export default function Home() {
  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-neutral-900 mb-4">
          Arandu Repro
        </h1>
        <p className="text-neutral-600 mb-8">
          Upload and view scientific papers
        </p>
        <div className="card">
          <p className="text-neutral-500">
            Navigate to <code className="bg-neutral-100 px-2 py-1 rounded">/p/[aid]</code> to view a paper
          </p>
        </div>
      </div>
    </main>
  );
}
