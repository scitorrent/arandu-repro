"use client";

import { useState } from "react";

export default function Home() {
  const [repoUrl, setRepoUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Repository URL:", repoUrl);
  };

  return (
    <div className="flex min-h-screen items-center justify-center p-8">
      <main className="w-full max-w-md">
        <h1 className="text-2xl font-bold mb-6">Arandu Repro</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="repoUrl" className="block text-sm font-medium mb-2">
              Repository URL
            </label>
            <input
              type="text"
              id="repoUrl"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="w-full px-4 py-2 border rounded-md"
            />
          </div>
          <button
            type="submit"
            className="w-full px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800"
          >
            Submit
          </button>
        </form>
      </main>
    </div>
  );
}
