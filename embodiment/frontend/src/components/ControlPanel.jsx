import React, { useState } from 'react';
import { Camera, Bot, BrainCircuit } from 'lucide-react';

const ControlPanel = () => {
    const [config, setConfig] = useState({
        camera: 'RealSense',
        robot: 'Dofbot',
        logic: 'Logic'
    });

    const handleConfigChange = async (type, value) => {
        const newConfig = { ...config, [type]: value };
        setConfig(newConfig);

        try {
            // UserRequestDTO 규격에 맞춘 payload 구성
            const payload = {
                request_type: 'config_change',
                config: {
                    target_robot: newConfig.robot.toLowerCase() === 'dofbot' ? 'dofbot' : 'pybullet',
                    active_camera: newConfig.camera.toLowerCase() === 'realsense' ? 'realsense' : 'pybullet',
                    op_mode: newConfig.logic.toLowerCase() === 'memory' ? 'memory_based' : 'rule_based',
                    is_emergency_stop: false
                }
            };

            await fetch(`http://localhost:8000/api/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
        } catch (e) { console.error("Config Error", e); }
    };

    const Section = ({ title, icon: Icon, options, current, type }) => (
        <div className="mb-4">
            <div className="flex items-center gap-2 mb-2 text-[11px] font-bold text-[#86868B] uppercase tracking-wider">
                <Icon size={12} /> {title}
            </div>
            <div className="flex bg-[#F2F2F7] p-1 rounded-[14px]">
                {options.map(opt => (
                    <button
                        key={opt}
                        onClick={() => handleConfigChange(type, opt)}
                        className={`flex-1 py-2 text-[12px] font-medium rounded-[10px] transition-all
              ${current === opt
                                ? 'bg-white text-[#007AFF] shadow-sm font-bold'
                                : 'text-[#86868B] hover:text-[#1D1D1F]'}`}
                    >
                        {opt}
                    </button>
                ))}
            </div>
        </div>
    );

    return (
        <div className="bg-white rounded-[22px] shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-5 flex-none mb-5">
            <Section
                title="Camera Source"
                icon={Camera}
                options={['RealSense', 'PyBullet']}
                current={config.camera}
                type="camera"
            />
            <Section
                title="Robot Target"
                icon={Bot}
                options={['Dofbot', 'PyBullet']}
                current={config.robot}
                type="robot"
            />
            <Section
                title="Logic Mode"
                icon={BrainCircuit}
                options={['Memory', 'Logic']}
                current={config.logic}
                type="logic"
            />
        </div>
    );
};

// Memoize to prevent re-renders unless functionality changes (though it uses local state)
export default React.memo(ControlPanel);
