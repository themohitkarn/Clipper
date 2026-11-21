import React from 'react';
import { Zap, Github, Sparkles, Video, CheckCircle2, ShieldCheck } from 'lucide-react';

export default function Navbar({ systemInfo }) {
  return (
    <header className="border-b border-slate-800 bg-[#0f1422] sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-sm">
            <Zap className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-xl tracking-tight text-white">
                Clipper AI
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                100% FREE
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Turn 10-Min to 24-Hr Long Videos into Viral Shorts
            </p>
          </div>
        </div>

        {/* Center Features Pill */}
        <div className="hidden md:flex items-center gap-6 text-xs text-slate-400 font-medium">
          <span className="flex items-center gap-1.5 hover:text-slate-200 transition-colors">
            <Video className="w-3.5 h-3.5 text-purple-400" />
            24-Hr Selective Download
          </span>
          <span className="flex items-center gap-1.5 hover:text-slate-200 transition-colors">
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            AI Hook Detection
          </span>
          <span className="flex items-center gap-1.5 hover:text-slate-200 transition-colors">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            No Watermark & Free
          </span>
        </div>

        {/* Right Info & GitHub */}
        <div className="flex items-center gap-3">
          {systemInfo && (
            <div className="hidden sm:flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
              <span className={`w-2 h-2 rounded-full ${systemInfo.ready ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`}></span>
              <span>{systemInfo.ready ? 'Engine Ready' : 'Setting up'}</span>
            </div>
          )}

          <a
            href="https://github.com/themohitkarn/Clipper"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 border border-slate-700 transition-all shadow-sm"
          >
            <Github className="w-4 h-4" />
            <span>GitHub</span>
          </a>
        </div>

      </div>
    </header>
  );
}
