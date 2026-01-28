export class ExpressionEngine {
    constructor() {
        // Physical Muscle Parameters (0.0 - 1.0 mostly)
        this.current = {
            eye: {
                openness: 1.0,
                squint: 0.0,
                gazeX: 0.0, // -1 (Left) to 1 (Right)
                gazeY: 0.0, // -1 (Up) to 1 (Down)
                blink: 0.0  // 0 (Open) to 1 (Closed)
            },
            mouth: {
                openness: 0.0,
                smile: 0.0, // -1 (Frown) to 1 (Smile)
                width: 0.5  // 0 (Narrow) to 1 (Wide)
            },
            head: {
                tilt: 0.0,
                bob: 0.0
            }
        };

        this.target = JSON.parse(JSON.stringify(this.current));

        // Internal State for Procedural Animation
        this.lastBlinkTime = 0;
        this.nextBlinkInterval = 3000;
        this.isBlinking = false;

        this.saccadeTime = 0;
        this.saccadeTarget = { x: 0, y: 0 };
    }

    // 1. Map Emotion to Muscle Targets (Semantic Layer)
    updateTargetFromEmotion(emotion) {
        // emotion: { focus, effort, confidence, frustration, curiosity }

        const e = emotion;

        // Base Expression
        this.target.eye.openness = 1.0 - (e.effort * 0.3); // Effort -> Eyes narrow slightly
        this.target.eye.squint = (e.confidence * 0.8) - (e.frustration * 0.5);
        this.target.mouth.smile = (e.confidence * 1.0) - (e.frustration * 1.0); // Simple linear map

        // Frustration Effects
        if (e.frustration > 0.5) {
            this.target.head.tilt = (Math.random() - 0.5) * 0.2; // Shake head slightly?
            this.target.mouth.width = 0.3; // Pursed lips
        } else {
            this.target.mouth.width = 0.5 + (e.confidence * 0.3);
            this.target.head.tilt = 0.0;
        }

        // Curiosity Effects (Head tilt)
        if (e.curiosity > 0.6) {
            this.target.head.tilt = 0.2; // Tilt head
            this.target.eye.openness = 1.0;
        }
    }

    // 2. Physics & Procedural Update (Physical Layer)
    update(dt, isManual = false) {
        if (isManual) {
            // Strict Manual Override: Bypass all physics/procedural
            // Just return target (which is set by sliders)
            // Copy target to current to ensure state sync
            this.current = JSON.parse(JSON.stringify(this.target));
            return this.current;
        }

        // A. Blinking Logic (Automatic)
        this._updateBlink(dt);

        // B. Saccades (Micro eye movements)
        this._updateSaccades(dt);

        // C. Head Bob
        this._updateHeadBob(dt);

        // D. Interpolation (Spring/Lerp)
        this._lerpStep(dt);

        return this.current;
    }

    _updateBlink(dt) {
        const now = Date.now();
        if (!this.isBlinking) {
            if (now - this.lastBlinkTime > this.nextBlinkInterval) {
                this.isBlinking = true;
                this.blinkPhase = 0;
            }
        } else {
            this.blinkPhase += dt * 10; // Slightly slower blink to be more visible (approx 0.3s)
            // Sine wave 0 -> 1 -> 0
            const val = Math.sin(this.blinkPhase);
            if (val < 0) this.current.eye.blink = 0;
            else this.current.eye.blink = val; // Full range 0 to 1

            if (this.blinkPhase >= Math.PI) {
                this.isBlinking = false;
                this.current.eye.blink = 0;
                this.lastBlinkTime = now;
                this.nextBlinkInterval = 1000 + Math.random() * 2000; // Frequent blinks (1-3s)
            }
        }
    }

    _updateSaccades(dt) {
        // Brownian Noise for Gaze (Visible Jitter)
        this.saccadeTime += dt;
        if (this.saccadeTime > 0.15) {
            const noise = 0.15; // +/- 0.15 * 5px scale = +/- 0.75px (Visible vibration)
            this.saccadeTarget.x = (Math.random() - 0.5) * noise;
            this.saccadeTarget.y = (Math.random() - 0.5) * noise;
            this.saccadeTime = 0;
        }
    }

    _updateHeadBob(dt) {
        // Breathing / Idle Bobbing (Visible)
        const time = Date.now() / 1000;
        this.current.head.bob = Math.sin(time * 3) * 3.0; // Faster and larger bob (+/- 3px)
    }

    _lerpStep(dt) {
        const speed = 10.0 * dt; // Very snappy

        // Recursive Lerp
        const process = (c, t, path = '') => {
            for (let key in c) {
                if (typeof c[key] === 'object') {
                    process(c[key], t[key], path + key + '.');
                } else {
                    if (key === 'blink') continue;
                    if (key === 'bob') continue;

                    let targetVal = t[key];

                    // Apply Saccades to Gaze Target
                    if (key === 'gazeX') targetVal += this.saccadeTarget.x;
                    if (key === 'gazeY') targetVal += this.saccadeTarget.y;

                    // Lerp
                    c[key] = c[key] + (targetVal - c[key]) * speed;
                }
            }
        };

        process(this.current, this.target);
    }
}
