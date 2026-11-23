import React, { useState } from 'react';
import {
  Download, Play, Pause, Flame, Subtitles, Share2, Edit3, Check,
  ExternalLink, Youtube, Copy, Sparkles, Tag, ChevronDown, ChevronUp
} from 'lucide-react';

export default function ClipCard({ clip, onOpenEditor }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedTitle, setCopiedTitle] = useState(false);
  const [copiedDesc, setCopiedDesc] = useState(false);
  const [showSeoDetails, setShowSeoDetails] = useState(false);
  const [showYtModal, setShowYtModal] = useState(false);

  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const getFullCaption = () => {
    const tags = clip.hashtags && clip.hashtags.length > 0
      ? clip.hashtags.join(' ')
      : '#Shorts #Viral #Trending #Clips';
    const desc = clip.description || `Watch till the end! ${clip.hook_text}`;
    return `${clip.title}\n\n${desc}\n\n${tags}`;
  };

  const handleCopyCaption = () => {
    navigator.clipboard.writeText(getFullCaption());
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2500);
  };

  const handleCopyTitleOnly = () => {
    navigator.clipboard.writeText(clip.title);
    setCopiedTitle(true);
    setTimeout(() => setCopiedTitle(false), 2000);
  };

  const handleCopyDescOnly = () => {
    const tags = clip.hashtags ? clip.hashtags.join(' ') : '#Shorts #Viral';
    const desc = clip.description || clip.hook_text;
    navigator.clipboard.writeText(`${desc}\n\n${tags}`);
    setCopiedDesc(true);
    setTimeout(() => setCopiedDesc(false), 2000);
  };

  const handlePublishToYouTube = () => {
    // 1. Copy SEO content to clipboard automatically
    handleCopyCaption();
    setShowYtModal(true);

    // 2. Open YouTube Upload page in a new tab
    const uploadUrl = clip.youtube_upload_url || "https://studio.youtube.com/channel/UC/videos/upload?d=hd";
    window.open(uploadUrl, '_blank', 'noopener,noreferrer');
  };

  return (
    <div className="bg-[#121420] border border-slate-800 hover:border-purple-500/50 rounded-3xl overflow-hidden shadow-xl transition-all duration-300 flex flex-col group relative">
      
      {/* Video Container */}
      <div className="relative bg-black flex items-center justify-center overflow-hidden aspect-[9/16] max-h-[460px]">
        <video
          src={clip.video_url}
          poster={clip.thumbnail_url}
          className="w-full h-full object-contain"
          controls
          onPlay={() => setIsPlaying(true)}
          onPause={() => setIsPlaying(false)}
        >
          <track
            src={clip.vtt_url}
            kind="subtitles"
            srcLang="en"
            label="English"
            default
          />
        </video>

        {/* Virality Badge Overlay */}
        <div className="absolute top-3 left-3 z-10">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-black/75 backdrop-blur-md border border-purple-500/40 text-xs font-black text-white shadow-lg">
            <Flame className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span>{clip.viral_score}/100</span>
            <span className="text-[10px] text-purple-300 font-semibold uppercase ml-0.5">Viral</span>
          </div>
        </div>

        {/* Duration Badge Overlay */}
        <div className="absolute top-3 right-3 z-10">
          <span className="px-2.5 py-1 rounded-full bg-black/70 backdrop-blur-md text-[11px] font-bold text-slate-300 border border-white/10">
            {formatDuration(clip.duration)}
          </span>
        </div>
      </div>

      {/* Content Info */}
      <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between">
        <div>
          {/* Category Pill if available */}
          {clip.event_category_label && (
            <div className="mb-2">
              <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-950/60 text-purple-300 border border-purple-800/60">
                {clip.event_category_label}
              </span>
            </div>
          )}

          {/* Title */}
          <h4 className="font-extrabold text-white text-base leading-snug mb-2 group-hover:text-purple-300 transition-colors line-clamp-2">
            {clip.title}
          </h4>

          {/* Hook Preview */}
          <p className="text-xs text-slate-400 mb-2.5 line-clamp-2 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 italic">
            "{clip.hook_text}"
          </p>

          {/* Viral Strategy Reason */}
          <p className="text-[11px] text-purple-300/80 mb-3 flex items-start gap-1.5">
            <span className="text-amber-400 font-bold shrink-0">Why it works:</span>
            <span>{clip.viral_reason}</span>
          </p>

          {/* Hashtags display */}
          {clip.hashtags && clip.hashtags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {clip.hashtags.slice(0, 4).map((tag, i) => (
                <span key={i} className="text-[10px] px-2 py-0.5 rounded-md bg-blue-950/40 text-blue-400 font-medium border border-blue-900/40">
                  {tag}
                </span>
              ))}
              {clip.hashtags.length > 4 && (
                <span className="text-[10px] px-1.5 py-0.5 text-slate-500 font-medium">
                  +{clip.hashtags.length - 4} more
                </span>
              )}
            </div>
          )}
        </div>

        {/* Actions Grid */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-col gap-2">
          
          {/* YouTube 1-Click Publish Button */}
          <button
            onClick={handlePublishToYouTube}
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-red-600 via-rose-600 to-red-600 hover:from-red-500 hover:to-rose-500 text-white font-black text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-red-600/30 active:scale-98"
            title="Copies title and tags to clipboard and opens YouTube Studio"
          >
            <Youtube className="w-4 h-4 fill-white" />
            <span>🚀 1-Click Upload to YouTube</span>
          </button>

          {/* Download MP4 Button */}
          <a
            href={clip.video_url}
            download={`${clip.title.replace(/[^\w\s-]/g, '')}.mp4`}
            className="w-full py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download MP4</span>
          </a>

          {/* Secondary Actions Row */}
          <div className="grid grid-cols-3 gap-1.5 text-[11px]">
            {/* Subtitles SRT */}
            <a
              href={clip.srt_url}
              download={`${clip.id}.srt`}
              className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold flex items-center justify-center gap-1 border border-slate-700 transition-colors"
              title="Download SRT Subtitles"
            >
              <Subtitles className="w-3.5 h-3.5 text-yellow-400" />
              <span>.SRT</span>
            </a>

            {/* Copy Social Caption */}
            <button
              onClick={handleCopyCaption}
              className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold flex items-center justify-center gap-1 border border-slate-700 transition-colors"
              title="Copy caption and hashtags"
            >
              {copiedAll ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5 text-pink-400" />}
              <span>{copiedAll ? "Copied!" : "Copy SEO"}</span>
            </button>

            {/* Edit Clip */}
            <button
              onClick={() => onOpenEditor && onOpenEditor(clip)}
              className="py-1.5 px-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold flex items-center justify-center gap-1 border border-slate-700 transition-colors"
              title="Edit captions & aspect ratio"
            >
              <Edit3 className="w-3.5 h-3.5 text-indigo-400" />
              <span>Edit</span>
            </button>
          </div>

        </div>

      </div>

      {/* YouTube Upload Helper Modal Overlay */}
      {showYtModal && (
        <div className="absolute inset-0 bg-black/95 z-30 p-5 flex flex-col justify-between backdrop-blur-md animate-in fade-in duration-200">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <div className="flex items-center gap-2 text-red-500 font-black text-sm">
                <Youtube className="w-5 h-5 fill-red-500" />
                <span>Publishing to YouTube Shorts</span>
              </div>
              <button
                onClick={() => setShowYtModal(false)}
                className="text-slate-400 hover:text-white text-xs px-2 py-1 rounded-md bg-slate-800"
              >
                ✕ Close
              </button>
            </div>

            <div className="p-2.5 rounded-xl bg-emerald-950/40 border border-emerald-500/40 text-emerald-300 text-xs font-semibold mb-3 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>Title & Description automatically copied to your clipboard!</span>
            </div>

            <p className="text-[11px] text-slate-300 mb-2 leading-relaxed">
              <strong>Quick 2-Step Flow:</strong>
              <br />1. YouTube Studio upload page has opened in your browser.
              <br />2. Click <strong>Download MP4</strong> below, drag the file into YouTube, and press <strong>Ctrl+V</strong> to paste title & tags!
            </p>

            {/* Quick Copy Fields */}
            <div className="space-y-2 mt-3 text-xs">
              <div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                  <span>Viral Title:</span>
                  <button
                    onClick={handleCopyTitleOnly}
                    className="text-purple-400 hover:text-purple-300 font-bold flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copiedTitle ? "Copied!" : "Copy"}</span>
                  </button>
                </div>
                <div className="p-2 bg-slate-900 rounded-lg text-slate-200 text-[11px] truncate border border-slate-800">
                  {clip.title}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between text-[11px] text-slate-400 mb-1">
                  <span>Description & Tags:</span>
                  <button
                    onClick={handleCopyDescOnly}
                    className="text-purple-400 hover:text-purple-300 font-bold flex items-center gap-1"
                  >
                    <Copy className="w-3 h-3" />
                    <span>{copiedDesc ? "Copied!" : "Copy"}</span>
                  </button>
                </div>
                <div className="p-2 bg-slate-900 rounded-lg text-slate-200 text-[11px] line-clamp-2 border border-slate-800">
                  {clip.description || clip.hook_text} {clip.hashtags?.join(' ')}
                </div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800 flex flex-col gap-2">
            <a
              href={clip.video_url}
              download={`${clip.title.replace(/[^\w\s-]/g, '')}.mp4`}
              className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download MP4 File</span>
            </a>
            <button
              onClick={() => {
                const url = clip.youtube_upload_url || "https://studio.youtube.com/channel/UC/videos/upload?d=hd";
                window.open(url, '_blank', 'noopener,noreferrer');
              }}
              className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs flex items-center justify-center gap-1.5 border border-slate-700"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Re-open YouTube Studio</span>
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
