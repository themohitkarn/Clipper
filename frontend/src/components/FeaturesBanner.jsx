import React from 'react';
import { Zap, Clock, ShieldCheck, Flame, Scissors, DownloadCloud } from 'lucide-react';

export default function FeaturesBanner() {
  const features = [
    {
      icon: Clock,
      title: "10 Min to 24+ Hr Videos",
      desc: "Selective time-slice streaming downloads only the 60s clips without downloading 40GB video files.",
      color: "text-purple-400"
    },
    {
      icon: Flame,
      title: "AI Hook & Virality Score",
      desc: "Ranks top moments by scroll-stopping hooks, curiosity gaps, and audience retention metrics.",
      color: "text-amber-400"
    },
    {
      icon: Scissors,
      title: "9:16 Vertical Reframe",
      desc: "Smart podcast-style blurred background + center crop for high production value on TikTok & Reels.",
      color: "text-pink-400"
    },
    {
      icon: Zap,
      title: "Alex Hormozi Subtitles",
      desc: "Bold animated yellow captions with auto-injected emojis (💰, 🔥, 🤯, 🛑) burned into video.",
      color: "text-yellow-400"
    },
    {
      icon: DownloadCloud,
      title: "One-Click Batch Export",
      desc: "Download individual MP4s, .SRT subtitle files, or export all generated clips as a ZIP archive.",
      color: "text-cyan-400"
    },
    {
      icon: ShieldCheck,
      title: "100% Free & No Watermark",
      desc: "No paid subscriptions, no monthly limits, no cloud fees. Built with open-source tools.",
      color: "text-emerald-400"
    }
  ];

  return (
    <div className="w-full max-w-7xl mx-auto my-16 px-4">
      <div className="text-center mb-10">
        <h3 className="text-2xl sm:text-3xl font-extrabold text-white">
          Everything Top Clipping Software Does — <span className="bg-gradient-to-r from-purple-400 to-emerald-400 bg-clip-text text-transparent">Free Forever</span>
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 mt-2 max-w-xl mx-auto">
          Built for creators, podcasters, streamers, and agencies who need limitless clipping.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {features.map((feat, i) => {
          const Icon = feat.icon;
          return (
            <div
              key={i}
              className="bg-[#121420]/80 border border-slate-800/80 hover:border-slate-700 rounded-3xl p-6 transition-all duration-300 hover:-translate-y-1"
            >
              <div className="w-12 h-12 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center mb-4 shadow-inner">
                <Icon className={`w-6 h-6 ${feat.color}`} />
              </div>
              <h4 className="font-extrabold text-white text-base mb-1.5">{feat.title}</h4>
              <p className="text-xs text-slate-400 leading-relaxed">{feat.desc}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
