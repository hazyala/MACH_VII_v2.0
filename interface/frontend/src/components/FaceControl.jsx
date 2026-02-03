import React, { useState } from 'react';
import FaceRenderer from './Face/FaceRenderer';
import FaceController from './Controller/FaceController';
import { EXPRESSIONS } from '../constants/expressions';
import { Smile } from 'lucide-react';


//디버깅용 상위 컴포넌트입니다.

function FaceControl() {
    const [params, setParams] = useState(EXPRESSIONS[0].base);
    const [currentExprId, setCurrentExprId] = useState(EXPRESSIONS[0].id);
    const [motionOffsets, setMotionOffsets] = useState({});

    // 실시간 모션 루프 (RequestAnimationFrame)
    React.useEffect(() => {
        const expression = EXPRESSIONS.find(e => e.id === currentExprId);
        if (!expression || !expression.motion) {
            setMotionOffsets({});
            return;
        }

        let frameId;
        const startTime = Date.now();

        const update = () => {
            const elapsed = (Date.now() - startTime) / 1000;
            const newOffsets = {};

            const calc = (m) => Math.sin(elapsed * m.freq * Math.PI * 2) * m.amp;

            // 모션 계산 로직
            Object.entries(expression.motion).forEach(([key, value]) => {
                if (key === 'all') {
                    // 전체 지터 (고주파)
                    newOffsets.all = (Math.random() - 0.5) * value.amp;
                } else if (typeof value === 'object' && !value.amp) {
                    // 중첩 객체 (e.g., leftEye: { openness: {amp, freq} })
                    newOffsets[key] = {};
                    Object.entries(value).forEach(([subKey, subValue]) => {
                        newOffsets[key][subKey] = calc(subValue);
                    });
                } else {
                    // 일반 값
                    newOffsets[key] = calc(value);
                }
            });

            setMotionOffsets(newOffsets);
            frameId = requestAnimationFrame(update);
        };

        frameId = requestAnimationFrame(update);
        return () => cancelAnimationFrame(frameId);
    }, [currentExprId]);

    // 프리셋 적용 및 슬라이더 동기화
    const handlePresetChange = (id) => {
        const expr = EXPRESSIONS.find(e => e.id === id);
        if (expr) {
            setCurrentExprId(id);
            setParams(expr.base);
        }
    };

    // 최종 파라미터 계산 (Base + Motion + Jitter)
    const getFinalParams = () => {
        const final = JSON.parse(JSON.stringify(params)); // Deep clone

        const applyOffset = (target, offset) => {
            if (!offset) return;
            Object.entries(offset).forEach(([k, v]) => {
                if (k === 'all') return;
                if (typeof v === 'object') {
                    if (!target[k]) target[k] = {};
                    applyOffset(target[k], v);
                } else {
                    target[k] = (target[k] || 0) + v;
                }
            });
        };

        applyOffset(final, motionOffsets);

        // 'all' 모션 (전체 지터) 적용
        if (motionOffsets.all) {
            const jitter = motionOffsets.all;
            final.gazeX += jitter;
            final.gazeY += jitter;
            final.mouthX += jitter;
            final.mouthY += jitter;
        }

        return final;
    };

    // 글로우 강도는 0.6으로 고정
    const glowIntensity = 0.6;

    return (
        // 전체 컨테이너: 라이트 모드 배경
        <div className="flex w-full h-screen bg-[#f5f5f7] overflow-hidden font-sans relative">

            {/* 
                중앙 영역: 얼굴 렌더링 (Face Rendering)
                - 화면 중앙에 배치되어 얼굴 형상을 출력합니다.
            */}
            <div className="absolute inset-0 flex justify-center items-center h-full pointer-events-none">
                {/* 얼굴 컨테이너 (Face Container)
                    - 화면 가운데 정렬
                    - h-[80vh]: 화면 높이의 80%를 차지하도록 설정
                    - aspect-square: 정사각형 비율 유지
                */}
                <div className="relative aspect-square h-[80vh] max-w-full flex justify-center items-center pointer-events-auto">
                    <FaceRenderer {...getFinalParams()} glowIntensity={glowIntensity} />
                </div>

                {/* 표정 프리셋 선택기 (Radio Buttons) - 2열 그리드 및 디자인 동기화 */}
                <div
                    className="absolute left-8 top-1/2 -translate-y-1/2 w-80 max-h-[90vh] bg-black/50 backdrop-blur-xl p-6 rounded-2xl shadow-2xl border border-white/10 flex flex-col z-50 pointer-events-auto"
                >
                    <h2 className="text-xl font-bold mb-6 flex items-center tracking-tight text-white">
                        <Smile className="mr-2" size={20} />
                        Presets
                    </h2>
                    <div className="grid grid-cols-2 gap-2 overflow-y-visible">
                        {EXPRESSIONS.map((expr) => (
                            <label
                                key={expr.id}
                                className={`flex items-center justify-center px-2 py-2 rounded-xl cursor-pointer transition-all duration-200 border text-center ${currentExprId === expr.id ? 'bg-blue-600 border-blue-400 text-white shadow-[0_0_15px_rgba(37,99,235,0.4)]' : 'bg-white/5 border-transparent text-gray-300 hover:bg-white/10 hover:border-white/10'}`}
                            >
                                <input
                                    type="radio"
                                    name="expression"
                                    className="hidden"
                                    checked={currentExprId === expr.id}
                                    onChange={() => handlePresetChange(expr.id)}
                                />
                                <span className="text-[13px] font-medium tracking-tight">{expr.label}</span>
                            </label>
                        ))}
                    </div>
                </div>

                {/* 버전 표시 텍스트 */}
                <div className="absolute bottom-8 left-16 text-black/30 text-xs font-mono tracking-widest uppercase select-none">
                    MACH-VII v2.0 // Emotion Core
                </div>
            </div>

            {/* 
                플로팅 컨트롤러 레이어 (Floating Controller Layer)
                - 화면 오른쪽에 절대 좌표로 배치됩니다.
                - 얼굴 렌더링 레이어의 레이아웃에 영향을 주지 않습니다.
            */}
            <div className="absolute right-8 top-1/2 -translate-y-1/2 w-auto h-auto z-50">
                <FaceController params={params} setParams={setParams} />
            </div>

        </div>
    );
}

export default FaceControl;