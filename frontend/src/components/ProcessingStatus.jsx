import React from 'react';
import { Loader2, CheckCircle, Video, MessageSquareQuote, Flame, Scissors, Subtitles, Sparkles } from 'lucide-react';

export default function ProcessingStatus({ job }) {
  if (!job) return null;

  const steps = [
    { key: "fetching_info", label: "Metadata & Video Stream", icon: Video },
    { key: "transcribing", label: "Speech Transcription", icon: MessageSquareQuote },
    { key: "finding_hooks", label: "AI Hook & Virality Scoring", icon: Flame },
    { key: "cutting_clips", label: "Selective Cutting & Reframe", icon: Scissors },
    { key: "generating_subtitles", label: "Dynamic Captions Burn", icon: Subtitles },
    { key: "completed", label: "Clips Ready to Download", icon: CheckCircle },
  ];

  const getStepStatus = (stepKey) => {
    const order = ["queued", "fetching_info", "transcribing", "finding_hooks", "cutting_clips", "generating_subtitles", "completed"];
    const currentIdx = order.indexOf(job.status);
    const stepIdx = order.indexOf(stepKey);

    if (job.status === "completed") return "done";
    if (job.status === "failed") return "error";
    if (currentIdx === stepIdx) return "active";
    if (currentIdx > stepIdx) return "done";
    return "pending";
  };

  return (
    <div className="w-full max-w-4xl mx-auto my-6 px-4">
      <div className="bg-[#12141f] border border-purple-500/30 rounded-3xl p-6 sm:p-8 shadow-xl relative overflow-hidden">
        
        {/* Glow */}
        <div className="absolute top-0 right-0 w-60 h-60 bg-purple-500/10 rounded-full blur-2xl"></div>

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-purple-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
            <div>
              <h3 className="font-extrabold text-white text-base sm:text-lg flex items-center gap-2">
                <span>Clipping in Progress</span>
                <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300">
                  {job.progress}%
                </span>
              </h3>
              <p className="text-xs sm:text-sm text-slate-400 mt-0.5">
                {job.current_step || "Processing..."}
              </p>
            </div>
          </div>

          {job.source_title && (
            <div className="text-right hidden sm:block max-w-xs">
              <p className="text-xs font-semibold text-slate-300 truncate">{job.source_title}</p>
              <p className="text-[11px] text-slate-500">{job.source_channel || "YouTube"}</p>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        <div className="w-full h-3 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800 mb-6">
          <div
            className="h-full bg-gradient-to-r from-purple-500 via-indigo-500 to-pink-500 rounded-full transition-all duration-500 shadow-lg shadow-purple-500/50"
            style={{ width: `${Math.max(5, job.progress)}%` }}
          ></div>
        </div>

        {/* Step Checkpoints */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          {steps.map((st, i) => {
            const status = getStepStatus(st.key);
            const Icon = st.icon;
            return (
              <div
                key={i}
                className={`p-3 rounded-2xl border text-center transition-all ${
                  status === "active"
                    ? "bg-purple-900/20 border-purple-500/60 text-purple-200 shadow-md shadow-purple-500/10"
                    : status === "done"
                    ? "bg-emerald-950/20 border-emerald-500/40 text-emerald-300"
                    : "bg-slate-900/40 border-slate-800/80 text-slate-500"
                }`}
              >
                <div className="flex justify-center mb-1.5">
                  {status === "active" ? (
                    <Icon className="w-4 h-4 text-purple-400 animate-pulse" />
                  ) : status === "done" ? (
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Icon className="w-4 h-4 text-slate-600" />
                  )}
                </div>
                <p className="text-[11px] font-semibold leading-tight line-clamp-1">{st.label}</p>
              </div>
            );
          })}
        </div>

        {/* Friendly note for 24-hour videos */}
        <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
          <span className="flex items-center gap-1.5 text-purple-300">
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            24-hour video optimization active: selective range download enabled.
          </span>
          <span className="text-[11px] text-slate-500">Zero bandwidth wasted</span>
        </div>

      </div>
    </div>
  );
}
