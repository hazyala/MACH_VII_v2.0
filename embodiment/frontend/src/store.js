import { create } from 'zustand';

// 전역 상태 스토어 정의
// Brain, Emotion, Perception 데이터를 중앙에서 관리합니다.
const useAppStore = create((set) => ({
    // 1. Initial State (초기 상태)
    brain: {
        agent_state: "IDLE",
        robot_status: "unknown",
        timestamp: 0
    },
    emotion: {
        vector: {
            focus: 0.5,
            effort: 0.0,
            confidence: 0.5,
            frustration: 0.0,
            curiosity: 0.5
        },
        muscles: {
            eye: { openness: 1.0, smile: 0.0 },
            mouth: { smile: 0.0, width: 0.5 },
            head: { roll: 0.0 }
        }
    },
    perception: {
        obstacle_distance_cm: 0,
        depth_grid: [],
        human_detected: false,
        risk_level: "SAFE",
        sensor_mode: "UNKNOWN"
    },
    memory: {
        connected: false
    },
    timestamp: 0,

    // 2. Actions (상태 업데이트)
    updateState: (packet) => set((state) => ({
        brain: packet.brain || state.brain,
        emotion: packet.emotion || state.emotion,
        perception: packet.perception || state.perception,
        memory: packet.memory || state.memory,
        timestamp: packet.timestamp || Date.now() / 1000
    })),
}));

export default useAppStore;
