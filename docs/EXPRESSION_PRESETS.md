# 🎭 Expression Presets Definition (Frontend)

2026.02.04 기준, `interface/frontend/src/constants/expressions.js`에 정의된 10가지 표정 프리셋의 상세 명세입니다.

각 표정은 `base` (기본 정적 값)와 `motion` (동적 프레임 오프셋)으로 구성됩니다.

---

## 1. Neutral (평온)
기본값이자 대기 상태의 표정입니다.
- **Color**: Default
- **Motion**:
  - **입 오므리기 (Roundness)**: 0.0 ~ 0.4 (Base 0.2, Amp 0.2, Freq 0.5)
  - **기타**: GazeY, MouthCurve의 미세한 진동

## 2. Happy (기쁨)
- **Color**: `#f7e573`
- **Base**: Openness 0.9, Smile 0.25, Roundness 0.05
- **Motion**:
  - **입 오므리기**: 0.0 ~ 0.1 (Freq 1.5)
  - **눈 크기**: 0.8 ~ 1.0 (Freq 1)
  - **눈웃음**: 0.2 ~ 0.3 (Freq 1)

## 3. Joy (환희)
기쁨보다 더 격한 감정 표입니다.
- **Color**: `#ffd129`
- **Base**: Openness 0.9, Squeeze 0.3, Roundness 0.6, MouthOpenness 20.5
- **Motion**:
  - **입 벌림**: 10 ~ 31 (Base 20.5, Amp 10.5, Freq 1.5)
  - **기타**: 기쁨(Happy)과 동일한 눈/입 오므리기 패턴 적용

## 4. Sad (슬픔)
- **Color**: `#2990ff`
- **Base**: Openness 0.9, Squeeze 0.1, MouthCurve -70, Roundness 0.25
- **Motion**:
  - **입 오므리기**: 0.0 ~ 0.5 (Base 0.25, Amp 0.25, Freq 0.5)
  - **눈 찡그리기 (Squeeze)**: 0.0 ~ 0.2 (Freq 1)
  - **눈 크기**: 0.8 ~ 1.0 (Freq 0.5)

## 5. Angry (분노)
빠르고 격한 떨림이 특징입니다.
- **Color**: `#ff2929`
- **Base**: MouthCurve -100, MouthY 7.5, Openness -12.5, Rotation -25
- **Motion**:
  - **입 상하 (MouthY)**: 5 ~ 10 (Amp 2.5, Freq 3)
  - **입 벌림**: -15 ~ -10 (Amp 2.5, Freq 3)
  - **눈 회전**: -30 ~ -20 (Amp 5, Freq 4)
  - *Note*: 초기 설정보다 진동수를 낮춤 (Freq 8 -> 4/3)

## 6. Surprised (놀람)
- **Color**: `#fe8b20`
- **Base**: Openness 0.9, MouthOpenness 25.5, Roundness 1
- **Motion**:
  - **눈 크기**: 0.8 ~ 1.0 (Freq 2)
  - **입 벌림**: 20 ~ 31 (Freq 2)
  - *Note*: 진동수를 분노 대비 절반 수준으로 하향 (Freq 2)

## 7. Suspicious (의심)
시선과 입이 함께 눈치를 보며 움직입니다.
- **Color**: `#3f00d1`
- **Base**: GazeX 0, MouthX 10, Squeeze 1
- **Motion**:
  - **Gaze X**: -10 ~ 10 (Amp 10, Freq 0.5)
  - **Mouth X**: 5 ~ 15 (Amp 5, Freq 0.5) - *Gaze X와 동기화되어 움직임*

## 8. Thinking (고민)
눈알을 굴리며 입을 삐죽거리는 모션입니다.
- **Color**: `#00bfff`
- **Base**: GazeX 0, MouthX 5, GazeY -40
- **Motion**:
  - **Gaze X**: -30 ~ 30 (Amp 30, Freq 0.25)
  - **Mouth X**: -15 ~ 25 (Amp 20, Freq 0.25)
  - *Note*: 모션 속도를 매우 느리게 설정 (Freq 0.25)

## 9. Fear (공포)
겁에 질려 바들바들 떠는 모습입니다.
- **Color**: `#5000b3`
- **Base**: Squeeze 0.25, GazeY 10
- **Motion**:
  - **Squeeze**: 0.2 ~ 0.3 (Freq 6)
  - **Gaze X/Y**: ±5 떨림 (Freq 6)
  - **눈 크기**: ±0.1 떨림 (Freq 6)

## 10. Bored (지루함)
나른하게 시선을 위아래로 움직입니다.
- **Color**: `#7d8d97`
- **Base**: GazeY 0, Openness 0.3
- **Motion**:
  - **Gaze Y**: -20 ~ 20 (Amp 20, Freq 0.1)
  - *Note*: 매우 느린 호흡 (Freq 0.1)
