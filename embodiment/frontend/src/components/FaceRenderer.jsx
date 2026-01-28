import React from 'react';
import useAppStore from '../store';

const FaceRenderer = ({ size = 140 }) => {
    const emotion = useAppStore((state) => state.emotion);

    // 백엔드에서 전송된 물리 표현 파라미터 (muscles) 추출
    const muscles = emotion?.muscles || {
        eye: { openness: 1.0, smile: 0.0 },
        mouth: { smile: 0.0, width: 0.5 },
        head: { roll: 0.0 }
    };

    const faceColor = "#1D1D1F";

    // 1. 눈 형태 계산 (openness 기반)
    const eyeRY = 15 * muscles.eye.openness;

    // 2. 입 형태 계산 (Quadratic Bezier)
    // M 70 120 Q 100 [ControlY] 130 120
    const controlY = 120 + (muscles.mouth.smile * 20);
    const mouthPath = `M 70 120 Q 100 ${controlY} 130 120`;

    // 3. 머리 각도 계산
    const headTransform = `rotate(${muscles.head.roll}, 100, 100)`;

    return (
        <div className="w-full h-full flex items-center justify-center">
            <svg
                width="100%"
                height="100%"
                viewBox="0 0 200 200"
                style={{ overflow: 'visible' }}
            >
                {/* Global Transform Group (Head Roll) */}
                <g transform={headTransform}>

                    {/* Left Eye */}
                    <g transform="translate(70, 80)">
                        <ellipse
                            cx="0" cy="0"
                            rx="12" ry={eyeRY}
                            fill={faceColor}
                        />
                        <circle cx="3" cy="-4" r="3" fill="white" opacity="0.2" />
                    </g>

                    {/* Right Eye */}
                    <g transform="translate(130, 80)">
                        <ellipse
                            cx="0" cy="0"
                            rx="12" ry={eyeRY}
                            fill={faceColor}
                        />
                        <circle cx="3" cy="-4" r="3" fill="white" opacity="0.2" />
                    </g>

                    {/* Mouth */}
                    <path
                        d={mouthPath}
                        stroke={faceColor}
                        strokeWidth="4"
                        fill="none"
                        strokeLinecap="round"
                    />

                </g>
            </svg>
        </div>
    );
};

export default React.memo(FaceRenderer);
