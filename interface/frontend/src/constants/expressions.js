/**
 * EXPRESSIONS
 * 20가지 동적 표정 프리셋 정의
 * base: 기본 파라미터 값 (상태 업데이트용)
 * motion: 실시간 모션 오프셋 (진폭 amp, 주파수 freq)
 */
export const EXPRESSIONS = [
    {
        id: "neutral",
        label: "평온",
        base: {
            leftEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: 0, mouthOpenness: 0, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            gazeY: { amp: 1, freq: 0.2 },
            mouthCurve: { amp: 2, freq: 0.1 }
        }
    },
    {
        id: "happy",
        label: "기쁨",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.2, smile: 0.2, rotation: -5 },
            rightEye: { openness: 0.9, squeeze: 0.2, smile: 0.2, rotation: 5 },
            gazeX: 0, gazeY: 0, mouthCurve: 30, mouthOpenness: 5, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            leftEye: { smile: { amp: 0.05, freq: 1.2 } },
            rightEye: { smile: { amp: 0.05, freq: 1.2 } },
            mouthCurve: { amp: 5, freq: 0.5 }
        }
    },
    {
        id: "joy",
        label: "환희",
        base: {
            leftEye: { openness: 0.8, squeeze: 0.6, smile: 0.3, rotation: -10 },
            rightEye: { openness: 0.8, squeeze: 0.6, smile: 0.3, rotation: 10 },
            gazeX: 0, gazeY: -10, mouthCurve: 50, mouthOpenness: 30, mouthX: 0, mouthY: 5, mouthRoundness: 0
        },
        motion: {
            mouthCurve: { amp: 10, freq: 2 },
            mouthOpenness: { amp: 5, freq: 1.5 }
        }
    },
    {
        id: "sad",
        label: "슬픔",
        base: {
            leftEye: { openness: 0.7, squeeze: 0.0, smile: -0.5, rotation: 10 },
            rightEye: { openness: 0.7, squeeze: 0.0, smile: -0.5, rotation: -10 },
            gazeX: 0, gazeY: 15, mouthCurve: -40, mouthOpenness: 2, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            mouthCurve: { amp: 3, freq: 0.8 },
            gazeY: { amp: 2, freq: 0.3 }
        }
    },
    {
        id: "angry",
        label: "분노",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.8, smile: 0.1, rotation: 25 },
            rightEye: { openness: 0.9, squeeze: 0.8, smile: 0.1, rotation: -25 },
            gazeX: 0, gazeY: -5, mouthCurve: -20, mouthOpenness: -10, mouthX: 0, mouthY: -10, mouthRoundness: 0
        },
        motion: {
            leftEye: { rotation: { amp: 5, freq: 8 } },
            rightEye: { rotation: { amp: 5, freq: 8 } },
            mouthY: { amp: 4, freq: 5 }
        }
    },
    {
        id: "surprised",
        label: "놀람",
        base: {
            leftEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: -15, mouthCurve: -10, mouthOpenness: 31, mouthX: 0, mouthY: 10, mouthRoundness: 0.8
        },
        motion: {
            leftEye: { openness: { amp: 0.1, freq: 10 } },
            rightEye: { openness: { amp: 0.1, freq: 10 } }
        }
    },
    {
        id: "suspicious",
        label: "의심",
        base: {
            leftEye: { openness: 0.4, squeeze: 0.5, smile: 0, rotation: 10 },
            rightEye: { openness: 0.4, squeeze: 0.5, smile: 0, rotation: -10 },
            gazeX: 20, gazeY: 0, mouthCurve: -10, mouthOpenness: 0, mouthX: 10, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            gazeX: { amp: 10, freq: 0.5 }
        }
    },
    {
        id: "thinking",
        label: "고민",
        base: {
            leftEye: { openness: 0.8, squeeze: 0.2, smile: -0.2, rotation: -15 },
            rightEye: { openness: 0.9, squeeze: 0.2, smile: -0.2, rotation: -5 },
            gazeX: -20, gazeY: -30, mouthCurve: 0, mouthOpenness: -5, mouthX: -5, mouthY: 5, mouthRoundness: 0.2
        },
        motion: {
            gazeX: { amp: 5, freq: 0.2 },
            gazeY: { amp: 5, freq: 0.2 }
        }
    },
    {
        id: "fear",
        label: "공포",
        base: {
            leftEye: { openness: 1.0, squeeze: 0.3, smile: -0.8, rotation: 5 },
            rightEye: { openness: 1.0, squeeze: 0.3, smile: -0.8, rotation: -5 },
            gazeX: 0, gazeY: 10, mouthCurve: -50, mouthOpenness: 10, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            all: { amp: 2, freq: 15 } // 전체적으로 고주파 떨림
        }
    },
    {
        id: "bored",
        label: "지루함",
        base: {
            leftEye: { openness: 0.3, squeeze: 0, smile: -0.2, rotation: 0 },
            rightEye: { openness: 0.3, squeeze: 0, smile: -0.2, rotation: 0 },
            gazeX: 0, gazeY: 20, mouthCurve: -10, mouthOpenness: 5, mouthX: 0, mouthY: 10, mouthRoundness: 0.1
        },
        motion: {
            leftEye: { openness: { amp: 0.1, freq: 0.2 } },
            rightEye: { openness: { amp: 0.1, freq: 0.2 } }
        }
    },
    {
        id: "tired",
        label: "피곤함",
        base: {
            leftEye: { openness: 0.2, squeeze: 0, smile: -0.4, rotation: -5 },
            rightEye: { openness: 0.2, squeeze: 0, smile: -0.4, rotation: 5 },
            gazeX: 0, gazeY: 30, mouthCurve: -20, mouthOpenness: 10, mouthX: 0, mouthY: 20, mouthRoundness: 0.3
        },
        motion: {
            leftEye: { openness: { amp: 0.05, freq: 0.1 } },
            rightEye: { openness: { amp: 0.05, freq: 0.1 } }
        }
    },
    {
        id: "excited",
        label: "흥분",
        base: {
            leftEye: { openness: 1.0, squeeze: 0.1, smile: 0.2, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.1, smile: 0.2, rotation: 0 },
            gazeX: 0, gazeY: -5, mouthCurve: 40, mouthOpenness: 20, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            leftEye: { openness: { amp: 0.2, freq: 4 } },
            rightEye: { openness: { amp: 0.2, freq: 4 } },
            mouthOpenness: { amp: 10, freq: 3 }
        }
    },
    {
        id: "proud",
        label: "자부심",
        base: {
            leftEye: { openness: 0.8, squeeze: 0.4, smile: 0.1, rotation: -10 },
            rightEye: { openness: 0.8, squeeze: 0.4, smile: 0.1, rotation: 10 },
            gazeX: 0, gazeY: -20, mouthCurve: 20, mouthOpenness: -10, mouthX: 0, mouthY: -15, mouthRoundness: 0
        },
        motion: {
            mouthCurve: { amp: 5, freq: 0.3 }
        }
    },
    {
        id: "shy",
        label: "부끄러움",
        base: {
            leftEye: { openness: 0.7, squeeze: 0.5, smile: 0.3, rotation: 10 },
            rightEye: { openness: 0.7, squeeze: 0.5, smile: 0.3, rotation: -10 },
            gazeX: 15, gazeY: 40, mouthCurve: 15, mouthOpenness: -5, mouthX: 0, mouthY: 5, mouthRoundness: 0.4
        },
        motion: {
            gazeX: { amp: 5, freq: 1 }
        }
    },
    {
        id: "confused",
        label: "혼란",
        base: {
            leftEye: { openness: 0.9, squeeze: 0, smile: -0.2, rotation: 20 },
            rightEye: { openness: 0.6, squeeze: 0.4, smile: 0.1, rotation: -5 },
            gazeX: -10, gazeY: -10, mouthCurve: -30, mouthOpenness: 10, mouthX: -10, mouthY: 5, mouthRoundness: 0.1
        },
        motion: {
            leftEye: { rotation: { amp: 10, freq: 2 } },
            rightEye: { openness: { amp: 0.2, freq: 1.5 } }
        }
    },
    {
        id: "focused",
        label: "집중",
        base: {
            leftEye: { openness: 0.6, squeeze: 0.8, smile: 0.1, rotation: 15 },
            rightEye: { openness: 0.6, squeeze: 0.8, smile: 0.1, rotation: -15 },
            gazeX: 0, gazeY: 0, mouthCurve: -5, mouthOpenness: -20, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            gazeX: { amp: 1, freq: 2 }
        }
    },
    {
        id: "mischievous",
        label: "장난",
        base: {
            leftEye: { openness: 0.9, squeeze: 0.5, smile: 0.3, rotation: -20 },
            rightEye: { openness: 0.4, squeeze: 0.8, smile: 0.2, rotation: 20 },
            gazeX: 20, gazeY: -10, mouthCurve: 40, mouthOpenness: 0, mouthX: 15, mouthY: -5, mouthRoundness: 0
        },
        motion: {
            mouthCurve: { amp: 10, freq: 3 }
        }
    },
    {
        id: "sarcastic",
        label: "냉소",
        base: {
            leftEye: { openness: 0.5, squeeze: 0.2, smile: -0.1, rotation: 5 },
            rightEye: { openness: 0.9, squeeze: 0, smile: -0.3, rotation: -5 },
            gazeX: -30, gazeY: 0, mouthCurve: -40, mouthOpenness: 5, mouthX: -20, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            leftEye: { openness: { amp: 0.1, freq: 0.5 } }
        }
    },
    {
        id: "pain",
        label: "고통",
        base: {
            leftEye: { openness: 0.1, squeeze: 1.0, smile: 0, rotation: 0 },
            rightEye: { openness: 0.1, squeeze: 1.0, smile: 0, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: -60, mouthOpenness: 25, mouthX: 0, mouthY: 10, mouthRoundness: 0.5
        },
        motion: {
            all: { amp: 5, freq: 12 }
        }
    },
    {
        id: "wink",
        label: "윙크",
        base: {
            leftEye: { openness: 0.0, squeeze: 1.0, smile: 0.3, rotation: 0 },
            rightEye: { openness: 1.0, squeeze: 0.0, smile: 0.3, rotation: 0 },
            gazeX: 0, gazeY: 0, mouthCurve: 35, mouthOpenness: 5, mouthX: 0, mouthY: 0, mouthRoundness: 0
        },
        motion: {
            rightEye: { smile: { amp: 0.1, freq: 1 } }
        }
    }
];
