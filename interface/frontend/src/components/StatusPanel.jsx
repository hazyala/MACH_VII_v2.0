import React from 'react';
import { Activity, Brain, Server } from 'lucide-react';

const StatusPanel = ({ brain, perception, memory_connected }) => {
    return (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 shadow-lg">
            <h3 className="text-gray-400 text-sm font-bold mb-3 uppercase flex items-center gap-2">
                <Activity className="w-4 h-4 text-cyan-400" /> System Status
            </h3>

            <div className="grid grid-cols-2 gap-4">
                {/* Agent State */}
                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
                    <div className="text-xs text-gray-500 mb-1">BRAIN STATE</div>
                    <div className={`text-lg font-bold ${brain.agent_state === 'RECOVERING' ? 'text-red-400' : 'text-white'}`}>
                        {brain.agent_state}
                    </div>
                </div>

                {/* Risk Level */}
                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
                    <div className="text-xs text-gray-500 mb-1">RISK LEVEL</div>
                    <div className={`text-lg font-bold ${perception.risk_level === 'DANGER' ? 'text-red-500' :
                            perception.risk_level === 'WARNING' ? 'text-yellow-400' : 'text-green-400'
                        }`}>
                        {perception.risk_level}
                    </div>
                </div>

                {/* Sensor Mode */}
                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
                    <div className="text-xs text-gray-500 mb-1">SENSOR MODE</div>
                    <div className="text-sm font-mono text-cyan-300">
                        {perception.sensor_mode}
                    </div>
                </div>

                {/* Memory Status */}
                <div className="bg-gray-900/50 p-3 rounded-lg border border-gray-700">
                    <div className="text-xs text-gray-500 mb-1">MEMORY LINK</div>
                    <div className={`text-sm font-mono flex items-center gap-2 ${memory_connected ? 'text-green-400' : 'text-gray-500'}`}>
                        <Server className="w-3 h-3" />
                        {memory_connected ? 'ONLINE' : 'OFFLINE'}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default StatusPanel;
