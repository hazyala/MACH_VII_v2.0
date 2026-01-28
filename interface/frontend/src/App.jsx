import React, { useEffect, useRef, useState } from 'react';
import useAppStore from './store';
import { wsManager } from './websocket_manager';
import FaceRenderer from './components/FaceRenderer';
import StatusPanel from './components/StatusPanel';
import ControlPanel from './components/ControlPanel';
import SensorPanel from './components/SensorPanel';
import ExpressionControlPanel from './components/ExpressionControlPanel'; // NEW
import { ExpressionEngine } from './logic/ExpressionEngine'; // NEW
import { Brain, Database } from 'lucide-react';
import { LineChart, Line, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

function App() {
  // 1. Selector Hooks
  const brain = useAppStore((state) => state.brain);
  const emotion = useAppStore((state) => state.emotion);
  const perception = useAppStore((state) => state.perception);
  const memory = useAppStore((state) => state.memory);
  const timestamp = useAppStore((state) => state.timestamp);

  // Derive memory connection from somewhere if available, else pass mock true/false or update store to include it
  // Currently store updateState receives full packet. Let's assume packet has memory.connected
  // But store.js doesn't have memory state yet explicitly defined in initial state, but updateState merges it.
  // Ideally update store to have memory section. For now access via direct prop if passed or use logic.
  // Actually the packet loop sends "memory": {"connected": ...}.
  // But store.js updates brain/emotion/perception. It might miss 'memory' if not in initial state logic?
  // store.js: updateState func:
  // updateState: (packet) => set((state) => ({ brain: ..., emotion: ..., perception: ..., timestamp: ... }))
  // It ignores 'memory'. I should fix store.js too to store memory state.
  // For now, I will assume it's missing and fix store.js in next step, or pass default false.

  // 2. Expression Engine Setup
  const engineRef = useRef(new ExpressionEngine());
  const [expression, setExpression] = useState(engineRef.current.current);
  const [isManual, setIsManual] = useState(false);
  const isManualRef = useRef(isManual);

  useEffect(() => {
    isManualRef.current = isManual;
  }, [isManual]);

  // 3. Animation Loop (60fps)
  useEffect(() => {
    let lastTime = performance.now();
    let frameId;

    const loop = (now) => {
      const dt = (now - lastTime) / 1000;
      lastTime = now;

      // Update Engine
      // Pass isManualRef.current to avoid closure staleness if using state directly in loop, 
      // but here we used state which might be stale in rAF loop without ref.
      // Better to use a Ref for isManual for the loop.
      const currExpr = engineRef.current.update(dt, isManualRef.current);

      // Force React Render (Optimization: Could use transient updates or canvas, but React state is fine for simple SVG)
      // Spread to trigger change detection
      setExpression(JSON.parse(JSON.stringify(currExpr)));

      frameId = requestAnimationFrame(loop);
    };

    frameId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frameId);
  }, []);

  // 4. Link Emotion -> Expression (When Auto Mode)
  useEffect(() => {
    if (!isManual) {
      engineRef.current.updateTargetFromEmotion(emotion);
    }
  }, [emotion, isManual]);

  // 5. WebSocket Init
  useEffect(() => {
    wsManager.connect();
    return () => wsManager.disconnect();
  }, []);

  // History for Chart
  const [history, setHistory] = React.useState([]);
  useEffect(() => {
    setHistory(prev => {
      const newHist = [...prev, { ...emotion, time: timestamp }];
      if (newHist.length > 50) newHist.shift();
      return newHist;
    });
  }, [timestamp, emotion]);

  // Handlers
  const sendCommand = async (type) => {
    try {
      const BASE_URL = 'http://localhost:8000';
      if (type === 'explore') {
        await fetch(`${BASE_URL}/api/context?allow_explore=true&risk_level=LOW`, { method: 'POST' });
      } else if (type === 'safe') {
        await fetch(`${BASE_URL}/api/context?allow_explore=false&risk_level=LOW`, { method: 'POST' });
      } else {
        await fetch(`${BASE_URL}/api/command?command=${type}`, { method: 'POST' });
      }
    } catch (e) { console.error("API Error", e); }
  };

  const handleManualControl = (path, value) => {
    // path: 'eye.openness', etc.
    if (!isManual) return;
    const keys = path.split('.');
    if (keys.length === 2) {
      engineRef.current.target[keys[0]][keys[1]] = value;
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white p-6 font-sans selection:bg-cyan-500/30">
      {/* Header */}
      <header className="flex justify-between items-center mb-6 pl-2 border-l-4 border-cyan-500">
        <div>
          <h1 className="text-4xl font-black italic tracking-tighter flex items-center gap-3 text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
            MACH VII <span className="text-gray-600 text-xl not-italic font-mono">v2.0</span>
          </h1>
          <p className="text-xs text-gray-500 font-mono mt-1 tracking-widest uppercase">Autonomous Agentic System</p>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-500 font-mono">SYSTEM TIME</div>
          <div className="text-xl font-mono text-cyan-500">{timestamp.toFixed(3)}</div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)]">

        {/* Left Column: Perception & Stats (3 cols) */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          <StatusPanel brain={brain} perception={perception} memory_connected={memory.connected} />
          <div className="flex-1">
            <SensorPanel perception={perception} />
          </div>
        </div>

        {/* Center Column: Face (6 cols) */}
        <div className="lg:col-span-6 flex flex-col items-center justify-center p-4">
          {/* Face uses 'expression' state now, NOT 'emotion' */}
          <div className="w-full h-full max-h-[600px] flex flex-col">
            <FaceRenderer expression={expression} />
          </div>
        </div>

        {/* Right Column: Controls & Analytics (3 cols) */}
        <div className="lg:col-span-3 flex flex-col gap-6 h-full overflow-y-auto pr-2">
          {/* Expression Debug Panel (Top Priority) */}
          <ExpressionControlPanel
            expression={expression}
            onInteract={handleManualControl}
            isManual={isManual}
            onToggleManual={() => setIsManual(!isManual)}
          />

          <ControlPanel
            onCommand={sendCommand}
            isManual={isManual}
            onToggleManual={() => setIsManual(!isManual)}
          />

          {/* Analytics Graph */}
          <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 shadow-lg min-h-[200px] flex flex-col">
            <h3 className="text-gray-400 text-sm font-bold mb-3 uppercase flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" /> Emotion Stream
            </h3>
            <div className="flex-1 w-full min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={history}>
                  <YAxis domain={[0, 1]} tick={{ fontSize: 10, fill: '#555' }} />
                  <Tooltip contentStyle={{ backgroundColor: '#111', border: '1px solid #333' }} />
                  <Line type="monotone" dataKey="focus" stroke="#22d3ee" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="frustration" stroke="#ef4444" strokeWidth={2} dot={false} isAnimationActive={false} />
                  <Line type="monotone" dataKey="confidence" stroke="#22c55e" strokeWidth={2} dot={false} isAnimationActive={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;
