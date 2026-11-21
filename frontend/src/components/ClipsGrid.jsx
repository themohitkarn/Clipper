import React, { useState } from 'react';
import { DownloadCloud, Sparkles, Filter, ArrowUpDown } from 'lucide-react';
import ClipCard from './ClipCard';

export default function ClipsGrid({ clips, jobId, onOpenEditor }) {
  const [filterScore, setFilterScore] = useState(0);
  const [sortBy, setSortBy] = useState('score'); // 'score' or 'timeline'

  if (!clips || clips.length === 0) return null;

  const filteredClips = clips
    .filter(c => c.viral_score >= filterScore)
    .sort((a, b) => {
      if (sortBy === 'score') return b.viral_score - a.viral_score;
      return a.start_time - b.start_time;
    });

  return (
    <div className="w-full max-w-7xl mx-auto my-10 px-4">
      
      {/* Top Banner Toolbar */}
      <div className="bg-[#121420] border border-slate-800 rounded-2xl p-5 mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl">
        
        <div>
          <h2 className="text-xl sm:text-2xl font-black text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-purple-400 fill-purple-400" />
            <span>Generated Viral Clips ({clips.length})</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Ranked by AI virality scoring with animated Alex Hormozi captions & vertical reframe.
          </p>
        </div>

        {/* Filter and Batch Download */}
        <div className="flex flex-wrap items-center gap-3">
          
          {/* Virality Filter */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={filterScore}
              onChange={(e) => setFilterScore(Number(e.target.value))}
              className="bg-transparent border-none text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="0" className="bg-slate-900">All Clips</option>
              <option value="85" className="bg-slate-900">Score 85+ 🔥</option>
              <option value="90" className="bg-slate-900">Score 90+ 🚀</option>
            </select>
          </div>

          {/* Sort By */}
          <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300">
            <ArrowUpDown className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-transparent border-none text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="score" className="bg-slate-900">Sort: Viral Score</option>
              <option value="timeline" className="bg-slate-900">Sort: Timeline Order</option>
            </select>
          </div>

          {/* Batch ZIP Download */}
          {jobId && (
            <a
              href={`/api/jobs/${jobId}/download-zip`}
              download
              className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs flex items-center gap-2 shadow-sm transition-all"
            >
              <DownloadCloud className="w-4 h-4" />
              <span>Download All (ZIP)</span>
            </a>
          )}

        </div>

      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredClips.map((clip) => (
          <ClipCard
            key={clip.id}
            clip={clip}
            onOpenEditor={onOpenEditor}
          />
        ))}
      </div>

    </div>
  );
}
