import React, { useState } from 'react';
import { Download, Play, Pause, Flame, Subtitles, Share2, Edit3, Check, ExternalLink } from 'lucide-react';

export default function ClipCard({ clip, onOpenEditor }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [copied, setCopied] = useState(false);

  const formatDuration = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  const handleCopyCaption = () => {
    const textToCopy = `${clip.title}\n\n${clip.hook_text}\n\n#shorts #viral #reels #tiktok #clips`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-[#121420] border border-slate-800 hover:border-purple-500/50 rounded-3xl overflow-hidden shadow-xl transition-all duration-300 flex flex-col group">
      
      {/* Video Container */}
      <div className="relative bg-black flex items-center justify-center overflow-hidden aspect-[9/16] max-h-[480px]">
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
      <div className="p-5 flex-1 flex flex-col justify-between">
        <div>
          {/* Title */}
          <h4 className="font-extrabold text-white text-base leading-snug mb-2 group-hover:text-purple-300 transition-colors line-clamp-2">
            {clip.title}
          </h4>

          {/* Hook Preview */}
          <p className="text-xs text-slate-400 mb-3 line-clamp-2 bg-slate-900/60 p-2.5 rounded-xl border border-slate-800/80 italic">
            "{clip.hook_text}"
          </p>

          {/* Viral Strategy Reason */}
          <p className="text-[11px] text-purple-300/80 mb-4 flex items-start gap-1.5">
            <span className="text-amber-400 font-bold shrink-0">Why it works:</span>
            <span>{clip.viral_reason}</span>
          </p>
        </div>

        {/* Actions Grid */}
        <div className="pt-3 border-t border-slate-800/80 flex flex-col gap-2">
          
          {/* Main Download MP4 */}
          <a
            href={clip.video_url}
            download={`${clip.title}.mp4`}
            className="w-full py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-md shadow-purple-600/20"
          >
            <Download className="w-4 h-4" />
            <span>Download Clip (MP4)</span>
          </a>

          {/* Secondary Actions */}
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
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Share2 className="w-3.5 h-3.5 text-pink-400" />}
              <span>{copied ? "Copied" : "Copy"}</span>
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

    </div>
  );
}
