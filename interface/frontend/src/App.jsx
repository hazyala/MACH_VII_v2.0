import React, { useState } from 'react';
import FaceRenderer from './components/Face/FaceRenderer';
import FaceController from './components/Controller/FaceController';

function App() {
  // Default State (Initial "Neutral/Good" Face)
  const [params, setParams] = useState({
    eyeOpenness: 1.0,
    eyeSqueeze: 0.0,
    gazeX: 0,
    gazeY: 0,
    mouthCurve: 0,
    mouthOpenness: 0,
    glowIntensity: 0.6,
    color: '#00FFFF' // Cyan default
  });

  return (
    <div className="flex w-full h-screen bg-[#050505] overflow-hidden font-sans text-white">
      {/* 1. Left Control Panel */}
      <FaceController params={params} setParams={setParams} />

      {/* 2. Main Viewport (Face) */}
      <div className="flex-1 flex justify-center items-center relative">
        {/* Ambient Background Gradient (Subtle) */}
        <div
          className="absolute inset-0 opacity-20 pointer-events-none"
          style={{
            background: `radial-gradient(circle at 50% 50%, ${params.color}, transparent 70%)`
          }}
        />

        {/* Face Renderer */}
        <div className="scale-125 transform transition-transform duration-500 hover:scale-130">
          <FaceRenderer {...params} />
        </div>

        <div className="absolute bottom-8 text-white/30 text-xs font-mono tracking-widest uppercase">
          MACH-VII v2.0 // Emotion Core
        </div>
      </div>
    </div>
  );
}

export default App;
