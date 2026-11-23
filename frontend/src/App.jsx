import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import VideoInputSection from './components/VideoInputSection';
import ProcessingStatus from './components/ProcessingStatus';
import ClipsGrid from './components/ClipsGrid';
import ClipEditorModal from './components/ClipEditorModal';
import FeaturesBanner from './components/FeaturesBanner';

export default function App() {
  const [systemInfo, setSystemInfo] = useState(null);
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [editingClip, setEditingClip] = useState(null);

  // Fetch system status on load
  useEffect(() => {
    fetch('/api/system')
      .then(res => res.json())
      .then(data => setSystemInfo(data))
      .catch(() => setSystemInfo({ ready: false }));
  }, []);

  // Poll or stream job progress
  useEffect(() => {
    if (!activeJobId || !isProcessing) return;

    let eventSource = null;
    let fallbackInterval = null;

    try {
      eventSource = new EventSource(`/api/jobs/${activeJobId}/stream`);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setJobData(data);
          if (data.status === 'completed' || data.status === 'failed') {
            setIsProcessing(false);
            eventSource.close();
          }
        } catch (e) {
          console.error("Error parsing SSE data", e);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        // Fallback polling if SSE is interrupted
        fallbackInterval = setInterval(async () => {
          try {
            const res = await fetch(`/api/jobs/${activeJobId}`);
            const data = await res.json();
            setJobData(data);
            if (data.status === 'completed' || data.status === 'failed') {
              setIsProcessing(false);
              clearInterval(fallbackInterval);
            }
          } catch (err) {
            console.error("Polling error", err);
          }
        }, 2000);
      };
    } catch (err) {
      console.error("SSE connection error", err);
    }

    return () => {
      if (eventSource) eventSource.close();
      if (fallbackInterval) clearInterval(fallbackInterval);
    };
  }, [activeJobId, isProcessing]);

  // Handle URL submission
  const handleSubmitUrl = async (payload) => {
    setIsProcessing(true);
    setJobData({ status: 'queued', progress: 5, current_step: 'Starting pipeline...' });

    try {
      const res = await fetch('/api/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.job_id) {
        setActiveJobId(data.job_id);
      } else {
        alert(data.detail || "Error starting video processing.");
        setIsProcessing(false);
      }
    } catch (err) {
      alert("Failed to connect to backend server. Make sure the API is running.");
      setIsProcessing(false);
    }
  };

  // Handle file upload
  const handleUploadFile = async (payload) => {
    setIsProcessing(true);
    setJobData({ status: 'queued', progress: 5, current_step: 'Uploading video file...' });

    const formData = new FormData();
    formData.append('file', payload.file);
    formData.append('aspect_ratio', payload.aspect_ratio);
    formData.append('subtitle_style', payload.subtitle_style);
    formData.append('min_duration', payload.min_duration);
    formData.append('max_duration', payload.max_duration);
    formData.append('max_clips', payload.max_clips);
    if (payload.gemini_api_key) {
      formData.append('gemini_api_key', payload.gemini_api_key);
    }
    if (payload.groq_api_key) {
      formData.append('groq_api_key', payload.groq_api_key);
    }
    if (payload.llm_provider) {
      formData.append('llm_provider', payload.llm_provider);
    }

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (data.job_id) {
        setActiveJobId(data.job_id);
      } else {
        alert(data.detail || "Upload failed.");
        setIsProcessing(false);
      }
    } catch (err) {
      alert("Failed to upload file to backend.");
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#08090e] text-slate-100 flex flex-col selection:bg-purple-600 selection:text-white">
      
      {/* Top Navigation */}
      <Navbar systemInfo={systemInfo} />

      {/* Main Container */}
      <main className="flex-1 pb-16">
        
        {/* Input Section */}
        <VideoInputSection
          onSubmitUrl={handleSubmitUrl}
          onUploadFile={handleUploadFile}
          isProcessing={isProcessing}
        />

        {/* Live Processing Indicator */}
        {isProcessing && jobData && (
          <ProcessingStatus job={jobData} />
        )}

        {/* Generated Clips Showcase */}
        {jobData && jobData.clips && jobData.clips.length > 0 && (
          <ClipsGrid
            clips={jobData.clips}
            jobId={activeJobId}
            onOpenEditor={(clip) => setEditingClip(clip)}
          />
        )}

        {/* Features & Capability Highlights */}
        <FeaturesBanner />

      </main>

      {/* Clip Editor Modal */}
      {editingClip && (
        <ClipEditorModal
          clip={editingClip}
          onClose={() => setEditingClip(null)}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0a0b12] py-8 text-center text-xs text-slate-500">
        <p className="max-w-md mx-auto mb-2">
          Clipper AI — Open Source 100% Free Video Highlights & Automated Clipping Platform
        </p>
        <p>
          Created for <a href="https://github.com/themohitkarn/Clipper" target="_blank" rel="noopener noreferrer" className="text-purple-400 hover:text-purple-300 font-semibold underline">themohitkarn/Clipper</a>
        </p>
      </footer>

    </div>
  );
}
