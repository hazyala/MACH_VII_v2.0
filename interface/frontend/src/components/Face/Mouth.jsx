import { motion } from 'framer-motion';

const Mouth = ({
    x = 200, // 가로 중앙 좌표
    y = 280, // 세로 기준 좌표
    width = 80,
    curve = 0, // -100 (슬픔/찡그림)에서 100 (행복/웃음) 사이의 곡률
    openness = 0, // 0 (다묾)에서 100 (벌림/놀람) 사이의 개방 정도
    roundness = 0, // 0 (넓은 타원)에서 1 (동그란 O형) 사이의 정도
    color = "#FFFFFF",
    glowIntensity = 0.5
}) => {

    // 베지어 곡선 제어점 (Bezier Control Points)
    // roundness가 높을수록 너비를 좁힙니다.
    const effectiveWidth = width * (1 - roundness * 0.5);

    // 시작 및 끝점 계산
    const startX = x - effectiveWidth / 2;
    const endX = x + effectiveWidth / 2;

    // 제어점 (곡률 결정)
    // curve와 openness가 기본 베이스가 되며, roundness는 추가적인 수직 보정을 제공할 수 있습니다.
    const controlY = y + (curve * 1.5) + openness;

    // 입을 벌렸을 때 아랫입술도 아래로 이동합니다.
    const bottomY = y + (openness * 1.5);

    // 단순한 선 또는 곡선 (입을 다물었을 때)
    const dClosed = `M ${startX} ${y} Q ${x} ${controlY} ${endX} ${y}`;

    // 벌린 입 (타원형 형태)
    // 입을 벌리는 효과를 구현하기 위해 두 개의 곡선을 연결한 경로를 사용합니다.

    let d = dClosed;
    if (openness > 10) {
        // 입술의 윗부분(곡률 적용) + 아랫부분(반대 곡률 또는 아래로 처짐)
        // roundness가 높을수록 위아래 곡률을 더 강하게 주어 원형에 가깝게 만듭니다.

        const upperControlShift = (openness * 0.5) * roundness;
        const upperControlY = y + (curve * 0.5) - upperControlShift;

        const lowerControlY = y + openness + (curve * 0.5) + upperControlShift;

        d = `M ${startX} ${y} 
           Q ${x} ${upperControlY} ${endX} ${y}
           Q ${x} ${lowerControlY} ${startX} ${y}`;
    }

    return (
        <motion.path
            d={d}
            stroke={color}
            strokeWidth={openness > 10 ? 0 : 8}
            fill={openness > 10 ? color : "transparent"}
            strokeLinecap="round"
            strokeLinejoin="round"

            animate={{
                d: d,
                stroke: color,
                fill: openness > 10 ? color : "transparent",
                filter: `drop-shadow(0 0 ${glowIntensity * 20}px ${color})`
            }}
            transition={{
                type: "spring",
                stiffness: 300,
                damping: 30
            }}

            style={{
                strokeWidth: openness > 10 ? 0 : 8
            }}
        />
    );
};

export default Mouth;
