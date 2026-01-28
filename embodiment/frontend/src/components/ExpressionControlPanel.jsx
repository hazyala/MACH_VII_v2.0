import React from 'react';
import { Settings, Sliders } from 'lucide-react';

const ExpressionControlPanel = ({ expression, onInteract, isManual, onToggleManual }) => {
    // 🛡️ DEFENSIVE: Early return if expression is missing to prevent White Screen
    if (!expression || !expression.eye || !expression.mouth || !expression.head) {
        return (
            <div className="fixed top-20 right-4 bg-red-900 text-white p-4 z-[9999] border-2 border-red-500 rounded-lg">
                ⚠️ CRITICAL: Expression State Missing
            </div>
        );
    }

    // Helper for slider input
    const Slider = ({ label, value, min, max, step, path, disabled }) => (
        <div className={`flex flex-col gap-1 mb-2 ${disabled ? 'opacity-50 pointer-events-none' : ''}`}>
            <div className="flex justify-between text-xs text-gray-400 font-mono">
                <span>{label}</span>
                <span>{value.toFixed(2)}</span>
            </div>
            <input
                type="range"
                min={min} max={max} step={step}
                value={value}
                onChange={(e) => onInteract(path, parseFloat(e.target.value))}
                disabled={disabled}
                className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
            />
        </div>
    );

    return (
        <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 shadow-lg min-h-[300px] relative z-50">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-gray-400 text-sm font-bold uppercase flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-cyan-400" /> Expression Engine
                </h3>
                <span className="text-xs font-mono text-gray-500">
                    MANUAL = {(!!isManual).toString().toUpperCase()}
                </span>
            </div>

            <button
                onClick={onToggleManual}
                className={`w-full py-3 rounded-lg text-sm font-bold transition-all mb-4 flex items-center justify-center gap-2 border ${isManual
                    ? 'bg-cyan-600 hover:bg-cyan-500 text-white border-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.5)]'
                    : 'bg-gray-700 hover:bg-gray-600 text-gray-300 border-gray-600'
                    }`}
            >
                <Settings className={`w-4 h-4 ${isManual ? 'animate-spin-slow' : ''}`} />
                {isManual ? 'MANUAL OVERRIDE: ON' : 'ENABLE MANUAL CONTROL'}
            </button>

            <div className="grid grid-cols-2 gap-4">
                {/* Eye Controls */}
                <div className="bg-black/30 p-3 rounded-lg border border-gray-700/50">
                    <h4 className="text-cyan-600 text-xs font-bold mb-2 uppercase">Eye Muscles</h4>
                    <Slider label="Openness" value={expression.eye.openness} min={0} max={1.2} step={0.05} path="eye.openness" disabled={!isManual} />
                    <Slider label="Squint" value={expression.eye.squint} min={0} max={1} step={0.05} path="eye.squint" disabled={!isManual} />
                    <Slider label="Gaze X" value={expression.eye.gazeX} min={-1} max={1} step={0.1} path="eye.gazeX" disabled={!isManual} />
                    <Slider label="Gaze Y" value={expression.eye.gazeY} min={-1} max={1} step={0.1} path="eye.gazeY" disabled={!isManual} />
                    <Slider label="Blink Phase" value={expression.eye.blink} min={0} max={1} step={0.01} path="eye.blink" disabled={!isManual} />
                </div>

                {/* Mouth & Head Controls */}
                <div className="bg-black/30 p-3 rounded-lg border border-gray-700/50">
                    <h4 className="text-cyan-600 text-xs font-bold mb-2 uppercase">Mouth & Head</h4>
                    <Slider label="Mouth Open" value={expression.mouth.openness} min={0} max={1} step={0.05} path="mouth.openness" disabled={!isManual} />
                    <Slider label="Smile / Frown" value={expression.mouth.smile} min={-1} max={1} step={0.1} path="mouth.smile" disabled={!isManual} />
                    <Slider label="Mouth Width" value={expression.mouth.width} min={0} max={1.5} step={0.1} path="mouth.width" disabled={!isManual} />
                    <div className="h-2"></div>
                    <Slider label="Head Tilt" value={expression.head.tilt} min={-1} max={1} step={0.1} path="head.tilt" disabled={!isManual} />
                </div>
            </div>
        </div>
    );
};

export default ExpressionControlPanel;
