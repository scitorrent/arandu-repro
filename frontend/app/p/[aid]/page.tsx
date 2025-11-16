"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

interface PaperMetadata {
  aid: string;
  title: string | null;
  visibility: string;
  latest_version: number | null;
  approved_public: boolean;
  approved_public_at: string | null;
  latest_score: number | null;
  counts: {
    claims: number;
    scores: number;
    versions: number;
  };
}

type Tab = "pdf" | "review" | "artifacts";

export default function PaperPage() {
  const params = useParams();
  const aid = params.aid as string;
  
  const [paper, setPaper] = useState<PaperMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("pdf");
  
  useEffect(() => {
    async function fetchPaper() {
      try {
        const response = await fetch(`${API_BASE}/api/v1/papers/${aid}`);
        if (!response.ok) {
          throw new Error("Paper not found");
        }
        const data = await response.json();
        setPaper(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load paper");
      } finally {
        setLoading(false);
      }
    }
    
    if (aid) {
      fetchPaper();
    }
  }, [aid]);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-neutral-600">Loading...</div>
      </div>
    );
  }
  
  if (error || !paper) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="card">
          <h2 className="text-xl font-semibold text-error-600 mb-2">Error</h2>
          <p className="text-neutral-600">{error || "Paper not found"}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-neutral-900">
                {paper.title || `Paper ${paper.aid}`}
              </h1>
              <p className="text-sm text-neutral-500 mt-1">AID: {paper.aid}</p>
            </div>
            {paper.latest_score !== null && (
              <div className="badge badge-success">
                Score: {paper.latest_score}
              </div>
            )}
          </div>
        </div>
      </header>
      
      {/* Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="border-b border-neutral-200">
          <nav className="flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab("pdf")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "pdf"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300"
              }`}
            >
              PDF
            </button>
            <button
              onClick={() => setActiveTab("review")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "review"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300"
              }`}
            >
              Review
            </button>
            <button
              onClick={() => setActiveTab("artifacts")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === "artifacts"
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300"
              }`}
            >
              Artifacts
            </button>
          </nav>
        </div>
        
        {/* Tab Content */}
        <div className="py-6">
          {activeTab === "pdf" && (
            <div className="card">
              <iframe
                src={`${API_BASE}/api/v1/papers/${aid}/viewer`}
                className="w-full h-[800px] border-0"
                title="PDF Viewer"
              />
            </div>
          )}
          
          {activeTab === "review" && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Review</h2>
              <p className="text-neutral-500">
                Review content will be displayed here when available.
              </p>
              <p className="text-sm text-neutral-400 mt-2">
                Claims: {paper.counts.claims} | Scores: {paper.counts.scores}
              </p>
            </div>
          )}
          
          {activeTab === "artifacts" && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Artifacts</h2>
              <p className="text-neutral-500">
                Artifacts will be displayed here when available.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

