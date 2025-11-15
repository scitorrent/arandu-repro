"use client";

import { useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export default function PDFViewer() {
  const params = useParams();
  const aid = params.aid as string;
  const version = params.v as string | undefined;
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  useEffect(() => {
    async function loadPDF() {
      if (!containerRef.current) return;
      
      try {
        // Dynamically import PDF.js
        const pdfjsLib = await import("pdfjs-dist");
        
        // Set worker
        pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
        
        // Build PDF URL
        const pdfUrl = version
          ? `${API_BASE}/api/v1/papers/${aid}/viewer?v=${version}`
          : `${API_BASE}/api/v1/papers/${aid}/viewer`;
        
        // Load PDF
        const loadingTask = pdfjsLib.getDocument({
          url: pdfUrl,
          withCredentials: false,
        });
        
        const pdf = await loadingTask.promise;
        
        // Render first page
        const page = await pdf.getPage(1);
        const viewport = page.getViewport({ scale: 1.5 });
        
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        if (!context) {
          throw new Error("Could not get canvas context");
        }
        
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        
        containerRef.current.innerHTML = "";
        containerRef.current.appendChild(canvas);
        
        await page.render({
          canvasContext: context,
          viewport: viewport,
        }).promise;
        
        setLoading(false);
      } catch (err) {
        console.error("Error loading PDF:", err);
        setError(err instanceof Error ? err.message : "Failed to load PDF");
        setLoading(false);
      }
    }
    
    if (aid) {
      loadPDF();
    }
  }, [aid, version]);
  
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="text-neutral-600">Loading PDF...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-neutral-50">
        <div className="card">
          <h2 className="text-xl font-semibold text-error-600 mb-2">Error</h2>
          <p className="text-neutral-600">{error}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-neutral-50 p-4">
      <div className="max-w-5xl mx-auto">
        <div ref={containerRef} className="bg-white shadow-lg rounded-lg overflow-hidden" />
      </div>
    </div>
  );
}

