import React, { useState } from 'react';
import { X, Play, Pause, Download, Sliders, LayoutTemplate, Type, Scissors, Check, Sparkles } from 'lucide-react';

export default function ClipEditorModal({ clip, onClose }) {
  if (!clip) return null;

  const [aspectRatio, setAspectRatio] = useState(clip.aspect_ratio || '9:16');
  const [subtitleStyle, setSubtitleStyle] = useState(clip.subtitle_style || 'hormozi');
  const [startTime, setStartTime] = useState(clip.start_time);
  const [endTime, setEndTime] = useState(clip.end_time);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md animate-in fade-in duration-200">
      
      <div className="bg-[#121422] border border-slate-700/80 rounded-3xl w-full max-w-4xl max-h-[90vh] overflow-hidden shadow-2xl flex flex-col md:flex-row">
        
        {/* Left: Video Preview */}
        <div className="md:w-1/2 bg-black flex items-center justify-center relative p-4 border-b md:border-b-0 md:border-r border-slate-800">
          <div className="w-full max-w-[320px] aspect-[9/16] rounded-2xl overflow-hidden bg-slate-900 border border-slate-800 shadow-2xl flex items-center justify-center">
            <video
              src={clip.video_url}
              controls
              className="w-full h-full object-contain"
            >
              <track src={clip.vtt_url} kind="subtitles" srcLang="en" label="English" default />
            </video>
          </div>
        </div>

        {/* Right: Controls & Options */}
        <div className="md:w-1/2 p-6 flex flex-col justify-between overflow-y-auto">
          
          <div>
            {/* Modal Header */}
            <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-800">
              <div>
                <h3 className="font-extrabold text-white text-lg leading-tight line-clamp-1">
                  {clip.title}
                </h3>
                <span className="text-xs text-purple-400 font-semibold">
                  Viral Score: {clip.viral_score}/100 🔥
                </span>
              </div>
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-full bg-slate-800 hover:bg-slate-700 flex items-center justify-center text-slate-300 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Customization Options */}
            <div className="space-y-5 text-xs">
              
              {/* Aspect Ratio */}
              <div>
                <label className="flex items-center gap-1.5 font-bold text-slate-300 mb-2">
                  <LayoutTemplate className="w-4 h-4 text-purple-400" />
                  Target Aspect Ratio
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: '9:16', label: '9:16 Vertical', desc: 'Shorts/TikTok' },
                    { id: '1:1', label: '1:1 Square', desc: 'Feed Post' },
                    { id: '16:9', label: '16:9 Landscape', desc: 'Standard' }
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setAspectRatio(opt.id)}
                      className={`p-2.5 rounded-xl border text-center transition-all ${
                        aspectRatio === opt.id
                          ? 'bg-purple-900/30 border-purple-500 text-white shadow-sm'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <p className="font-bold">{opt.label}</p>
                      <p className="text-[10px] text-slate-500">{opt.desc}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Subtitle Style */}
              <div>
                <label className="flex items-center gap-1.5 font-bold text-slate-300 mb-2">
                  <Type className="w-4 h-4 text-yellow-400" />
                  Subtitle Preset
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {[
                    { id: 'hormozi', name: 'Alex Hormozi', badge: 'Yellow Highlight' },
                    { id: 'neon_green', name: 'Neon Cyber', badge: 'Lime Green' },
                    { id: 'clean_white', name: 'Clean Minimal', badge: 'White Shadow' },
                    { id: 'fire_red', name: 'Fire Punchy', badge: 'Bold Red' }
                  ].map((sub) => (
                    <button
                      key={sub.id}
                      type="button"
                      onClick={() => setSubtitleStyle(sub.id)}
                      className={`p-2.5 rounded-xl border text-left transition-all ${
                        subtitleStyle === sub.id
                          ? 'bg-purple-900/30 border-purple-500 text-white shadow-sm'
                          : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <p className="font-bold">{sub.name}</p>
                      <p className="text-[10px] text-purple-300/80">{sub.badge}</p>
                    </button>
                  ))}
                </div>
              </div>

              {/* Hook Text Display */}
              <div>
                <label className="font-bold text-slate-300 mb-1.5 block">Opening Hook</label>
                <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 text-slate-300 text-xs italic">
                  "{clip.hook_text}"
                </div>
              </div>

            </div>
          </div>

          {/* Modal Footer Actions */}
          <div className="pt-6 border-t border-slate-800/80 mt-6 flex flex-col gap-2">
            <a
              href={clip.video_url}
              download={`${clip.title}.mp4`}
              className="w-full py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-purple-600/30"
            >
              <Download className="w-4 h-4" />
              <span>Download MP4 Clip</span>
            </a>

            <div className="flex gap-2">
              <a
                href={clip.srt_url}
                download={`${clip.id}.srt`}
                className="flex-1 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs flex items-center justify-center gap-1.5 border border-slate-700 transition-colors"
              >
                <span>Download .SRT</span>
              </a>
              <button
                type="button"
                onClick={onClose}
                className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>

        </div>

      </div>

    </div>
  );
}
