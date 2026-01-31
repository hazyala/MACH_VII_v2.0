import React from 'react';
import { Settings, Eye, MessageSquare, Sun, Move } from 'lucide-react';

const Slider = ({ label, value, onChange, min, max, step = 1, icon: Icon }) => (
    <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
            <div className="flex items-center text-gray-300 text-sm font-medium">
                {Icon && <Icon size={14} className="mr-2" />}
                {label}
            </div>
            <span className="text-xs text-gray-500 font-mono">{value}</span>
        </div>
        <input
            type="range"
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => onChange(parseFloat(e.target.value))}
            className="w-full h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-500 hover:accent-blue-400 transition-all"
        />
    </div>
);

const FaceController = ({ params, setParams }) => {
    const handleChange = (key, value) => {
        setParams(prev => ({ ...prev, [key]: value }));
    };

    return (
        <div className="w-80 h-full bg-[#1c1c1e] bg-opacity-90 backdrop-blur-md border-r border-[#2c2c2e] p-6 overflow-y-auto text-white shadow-2xl z-10">
            <h2 className="text-xl font-bold mb-6 flex items-center">
                <Settings className="mr-2" />
                Face Control
            </h2>

            {/* Group: Eyes */}
            <div className="mb-8">
                <h3 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4 border-b border-gray-700 pb-2">Eyes</h3>
                <Slider
                    label="Gaze X" value={params.gazeX} min={-50} max={50} icon={Move}
                    onChange={(v) => handleChange('gazeX', v)}
                />
                <Slider
                    label="Gaze Y" value={params.gazeY} min={-50} max={50} icon={Move}
                    onChange={(v) => handleChange('gazeY', v)}
                />
                <Slider
                    label="Openness" value={params.eyeOpenness} min={0} max={1} step={0.01} icon={Eye}
                    onChange={(v) => handleChange('eyeOpenness', v)}
                />
                <Slider
                    label="Squeeze (Happy/Wince)" value={params.eyeSqueeze} min={0} max={1} step={0.01} icon={Eye}
                    onChange={(v) => handleChange('eyeSqueeze', v)}
                />
            </div>

            {/* Group: Mouth */}
            <div className="mb-8">
                <h3 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4 border-b border-gray-700 pb-2">Mouth</h3>
                <Slider
                    label="Curve (Smile/Sad)" value={params.mouthCurve} min={-100} max={100} icon={MessageSquare}
                    onChange={(v) => handleChange('mouthCurve', v)}
                />
                <Slider
                    label="Openness" value={params.mouthOpenness} min={0} max={60} icon={MessageSquare}
                    onChange={(v) => handleChange('mouthOpenness', v)}
                />
            </div>

            {/* Group: Styling */}
            <div className="mb-8">
                <h3 className="text-xs uppercase tracking-wider text-gray-500 font-semibold mb-4 border-b border-gray-700 pb-2">Style</h3>
                <Slider
                    label="Glow Intensity" value={params.glowIntensity} min={0} max={1} step={0.01} icon={Sun}
                    onChange={(v) => handleChange('glowIntensity', v)}
                />

                <div className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-300">Color</span>
                    </div>
                    <input
                        type="color"
                        value={params.color}
                        onChange={(e) => handleChange('color', e.target.value)}
                        className="w-full h-8 rounded cursor-pointer bg-transparent"
                    />
                </div>
            </div>
        </div>
    );
};

export default FaceController;
