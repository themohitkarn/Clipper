import React, { useState } from 'react';
import { Youtube, Upload, Sparkles, Sliders, ChevronDown, ChevronUp, Clock, LayoutTemplate, Type, Key, Play } from 'lucide-react';

export default function VideoInputSection({ onSubmitUrl, onUploadFile, isProcessing }) {
  const [activeTab, setActiveTab] = useState('youtube');
  const [url, setUrl] = useState('');
  const [file, setFile] = useState(null);
  const [showSettings, setShowSettings] = useState(false);

  // Settings
  const [aspectRatio, setAspectRatio] = useState('9:16');
  const [subtitleStyle, setSubtitleStyle] = useState('hormozi');
  const [minDuration, setMinDuration] = useState(20);
  const [maxDuration, setMaxDuration] = useState(60);
  const [maxClips, setMaxClips] = useState(10);
  const [geminiApiKey, setGeminiApiKey] = useState('');

  const sampleVideos = [
    { label: "Alex Hormozi Podcast (1 hr)", url: "https://www.youtube.com/watch?v=7h2YqIu_XjQ" },
    { label: "Lex Fridman Interview (3 hrs)", url: "https://www.youtube.com/watch?v=jvqFAi7vkBc" },
    { label: "All-In Podcast (1.5 hrs)", url: "https://www.youtube.com/watch?v=W01L70IGBgE" }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (activeTab === 'youtube') {
      if (!url.trim()) return;
      onSubmitUrl({
        url: url.trim(),
        aspect_ratio: aspectRatio,
        subtitle_style: subtitleStyle,
        min_duration: parseInt(minDuration),
        max_duration: parseInt(maxDuration),
        max_clips: parseInt(maxClips),
        gemini_api_key: geminiApiKey.trim() || null
      });
    } else {
      if (!file) return;
      onUploadFile({
        file,
        aspect_ratio: aspectRatio,
        subtitle_style: subtitleStyle,
        min_duration: parseInt(minDuration),
        max_duration: parseInt(maxDuration),
        max_clips: parseInt(maxClips),
        gemini_api_key: geminiApiKey.trim() || null
      });
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto my-8 px-4">
      
      {/* Hero Headline */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs font-semibold mb-3">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span>The Free Alternative to Opus Clip, Munch & Klap</span>
        </div>
        <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white mb-3">
          Turn Any Video into <span className="text-blue-500">Viral Shorts</span> in Seconds
        </h1>
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto">
          Works with 10-minute clips or 24-hour long livestreams. High hook detection, auto 9:16 vertical reframe, and animated captions. 100% Free.
        </p>
      </div>

      {/* Main Card */}
      <div className="bg-[#0f1422] border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-xl relative overflow-hidden">

        {/* Tab Switcher */}
        <div className="flex p-1.5 bg-slate-900 border border-slate-800 rounded-xl max-w-md mx-auto mb-6">
          <button
            type="button"
            onClick={() => setActiveTab('youtube')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'youtube'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Youtube className="w-4 h-4 text-red-500" />
            YouTube Link
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('upload')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === 'upload'
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload File
          </button>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {activeTab === 'youtube' ? (
            <div>
              <div className="relative">
                <input
                  type="text"
                  placeholder="Paste YouTube video or livestream URL (e.g. https://www.youtube.com/watch?v=...)"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={isProcessing}
                  className="w-full bg-[#161824] border border-slate-700/80 rounded-2xl px-5 py-4 text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-purple-500 transition-colors shadow-inner"
                />
              </div>

              {/* Sample Links */}
              <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-400">
                <span className="text-slate-500">Try sample:</span>
                {sampleVideos.map((sample, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setUrl(sample.url)}
                    className="px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-purple-300 hover:text-white transition-colors border border-slate-700/60"
                  >
                    {sample.label}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="border-2 border-dashed border-slate-700 hover:border-purple-500/60 rounded-2xl p-8 text-center bg-[#141622]/50 transition-colors cursor-pointer">
              <input
                type="file"
                id="file-upload"
                accept="video/*"
                onChange={(e) => setFile(e.target.files[0])}
                className="hidden"
              />
              <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
                <div className="w-12 h-12 rounded-2xl bg-purple-500/10 flex items-center justify-center text-purple-400 mb-3">
                  <Upload className="w-6 h-6" />
                </div>
                <span className="text-sm font-semibold text-slate-200">
                  {file ? file.name : "Choose a video file or drag & drop here"}
                </span>
                <span className="text-xs text-slate-500 mt-1">MP4, MOV, MKV, WebM up to any length</span>
              </label>
            </div>
          )}

          {/* Collapsible Settings Button */}
          <div className="pt-2">
            <button
              type="button"
              onClick={() => setShowSettings(!showSettings)}
              className="flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-purple-300 transition-colors"
            >
              <Sliders className="w-3.5 h-3.5 text-purple-400" />
              <span>Customize Clip Settings (Aspect Ratio, Subtitles, Clip Count)</span>
              {showSettings ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          </div>

          {/* Settings Drawer */}
          {showSettings && (
            <div className="bg-[#141624] border border-slate-800 rounded-2xl p-5 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 animate-in fade-in duration-200 text-xs">
              
              {/* Aspect Ratio */}
              <div>
                <label className="flex items-center gap-1.5 font-bold text-slate-300 mb-2">
                  <LayoutTemplate className="w-3.5 h-3.5 text-indigo-400" />
                  Aspect Ratio
                </label>
                <select
                  value={aspectRatio}
                  onChange={(e) => setAspectRatio(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="9:16">9:16 (Shorts / Reels / TikTok)</option>
                  <option value="1:1">1:1 (Square Feed)</option>
                  <option value="16:9">16:9 (Landscape Highlights)</option>
                </select>
              </div>

              {/* Subtitle Style */}
              <div>
                <label className="flex items-center gap-1.5 font-bold text-slate-300 mb-2">
                  <Type className="w-3.5 h-3.5 text-yellow-400" />
                  Subtitle Style
                </label>
                <select
                  value={subtitleStyle}
                  onChange={(e) => setSubtitleStyle(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="hormozi">Alex Hormozi (Yellow & Bold)</option>
                  <option value="neon_green">Neon Cyber Green</option>
                  <option value="clean_white">Clean Modern White</option>
                  <option value="fire_red">Fire Red Punchy</option>
                  <option value="none">None (No Subtitles)</option>
                </select>
              </div>

              {/* Clip Count */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <label className="flex items-center gap-1.5 font-bold text-slate-300">
                    <Sparkles className="w-3.5 h-3.5 text-pink-400" />
                    Target Clips
                  </label>
                  <span className="text-[11px] text-blue-400 font-bold">{maxClips} Clips</span>
                </div>
                <div className="flex items-center gap-2">
                  <select
                    value={[3, 5, 10, 15, 20, 25, 30, 35, 36, 40, 50].includes(Number(maxClips)) ? String(maxClips) : 'custom'}
                    onChange={(e) => {
                      if (e.target.value !== 'custom') setMaxClips(Number(e.target.value));
                    }}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-blue-500"
                  >
                    <option value="3">Top 3 Clips</option>
                    <option value="5">Top 5 Viral Clips</option>
                    <option value="10">Top 10 Clips (Standard)</option>
                    <option value="15">Top 15 Clips (Long Video)</option>
                    <option value="20">Top 20 Clips (1-2 Hr Video)</option>
                    <option value="25">Top 25 Clips (2+ Hr Video)</option>
                    <option value="30">Top 30 Clips (Long Stream)</option>
                    <option value="35">Top 35 Clips (Full Highlights) 🔥</option>
                    <option value="36">Top 36 Clips (Max Coverage) 🔥</option>
                    <option value="40">Top 40 Clips (Marathon Video)</option>
                    <option value="50">Top 50 Clips (24-Hour Stream)</option>
                    <option value="custom">Custom Quantity...</option>
                  </select>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={maxClips}
                    onChange={(e) => setMaxClips(Math.max(1, Math.min(100, parseInt(e.target.value) || 1)))}
                    title="Type exact number of clips (e.g. 10, 35, 36)"
                    placeholder="Qty"
                    className="w-16 bg-slate-900 border border-slate-700 rounded-xl px-2 py-2 text-slate-200 text-center font-bold focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>

              {/* Clip Duration */}
              <div>
                <label className="flex items-center gap-1.5 font-bold text-slate-300 mb-2">
                  <Clock className="w-3.5 h-3.5 text-emerald-400" />
                  Duration
                </label>
                <select
                  value={`${minDuration}-${maxDuration}`}
                  onChange={(e) => {
                    const [min, max] = e.target.value.split('-').map(Number);
                    setMinDuration(min);
                    setMaxDuration(max);
                  }}
                  className="w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:border-purple-500"
                >
                  <option value="20-45">20s - 45s (Fast Viral)</option>
                  <option value="30-60">30s - 60s (Standard)</option>
                  <option value="45-90">45s - 90s (In-depth)</option>
                </select>
              </div>

              {/* Gemini API Key */}
              <div className="sm:col-span-2 md:col-span-4 mt-2 pt-3 border-t border-slate-800 flex flex-col sm:flex-row items-center gap-3">
                <div className="flex items-center gap-2 text-slate-400 whitespace-nowrap">
                  <Key className="w-3.5 h-3.5 text-amber-400" />
                  <span>Gemini API Key (Optional):</span>
                </div>
                <input
                  type="password"
                  placeholder="Leave empty for 100% Free Heuristic Mode, or paste free Google AI Studio key"
                  value={geminiApiKey}
                  onChange={(e) => setGeminiApiKey(e.target.value)}
                  className="flex-1 w-full bg-slate-900 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
                />
              </div>

            </div>
          )}

          {/* Submit Action Button */}
          <button
            type="submit"
            disabled={isProcessing || (activeTab === 'youtube' ? !url.trim() : !file)}
            className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-sm sm:text-base flex items-center justify-center gap-2 disabled:bg-slate-800 disabled:text-slate-500 disabled:cursor-not-allowed cursor-pointer transition-all shadow-md"
          >
            <Sparkles className="w-5 h-5 text-white" />
            <span>{isProcessing ? "Processing Video..." : "⚡ Generate Viral Clips Now (Free)"}</span>
          </button>

        </form>

      </div>
    </div>
  );
}
