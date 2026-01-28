import React, { useEffect } from 'react';
import useAppStore from './store';
import { wsManager } from './websocket_manager';

// New Component Imports (We will create/update these next)
import SensorPanel from './components/SensorPanel';
import CenterPanel from './components/CenterPanel'; // Combined Control + Face
import ChatPanel from './components/ChatPanel'; // Wide Chat

function App() {
  const timestamp = useAppStore((state) => state.timestamp);

  // WebSocket Connection
  useEffect(() => {
    wsManager.connect();
    return () => wsManager.disconnect();
  }, []);

  return (
    <div className="h-screen w-screen p-6 box-border font-sans selection:bg-blue-100">
      <div className="grid grid-cols-[28%_30%_42%] gap-6 h-full w-full">

        {/* Left Column: Perception */}
        <div className="flex flex-col h-full min-h-0">
          <SensorPanel />
        </div>

        {/* Center Column: Control & Expression */}
        <div className="flex flex-col h-full min-h-0">
          <CenterPanel />
        </div>

        {/* Right Column: Wide Chat */}
        <div className="flex flex-col h-full min-h-0">
          <ChatPanel />
        </div>

      </div>
    </div>
  );
}

export default App;
