/* Pure simulation: shared by the canvas game and deterministic Node tests. */
(function (root) {
  'use strict';
  const TAU = Math.PI * 2;
  const TRACK = { cx: 600, cy: 350, rx: 440, ry: 220, width: 112 };
  const clamp = (x, lo, hi) => Math.max(lo, Math.min(hi, x));

  function createRace() {
    return { x: 600, y: 570, heading: 0, speed: 0, boost: 100, elapsed: 0,
      lapTime: 0, laps: 0, bestLap: null, lastLap: null, checkpoint: 1,
      offroad: false, running: false, paused: false };
  }

  function trackPosition(x, y) {
    const angle = Math.atan2((y - TRACK.cy) / TRACK.ry, (x - TRACK.cx) / TRACK.rx);
    const nearestX = TRACK.cx + Math.cos(angle) * TRACK.rx;
    const nearestY = TRACK.cy + Math.sin(angle) * TRACK.ry;
    return { distance: Math.hypot(x - nearestX, y - nearestY),
      progress: ((Math.PI / 2 - angle) % TAU + TAU) % TAU };
  }

  function checkpoint(state) {
    const position = trackPosition(state.x, state.y);
    if (position.distance > TRACK.width / 2) return;
    const section = Math.floor(position.progress / (Math.PI / 2));
    // The car must visit right, top, left, then the finish; reversing over the
    // finish or resetting position cannot create a lap on its own.
    if (section !== state.checkpoint) return;
    state.checkpoint = (state.checkpoint + 1) % 4;
    if (section === 0) {
      state.laps += 1; state.lastLap = state.lapTime;
      state.bestLap = state.bestLap === null ? state.lapTime : Math.min(state.bestLap, state.lapTime);
      state.lapTime = 0;
    }
  }

  function step(state, controls, seconds) {
    if (!state.running || state.paused || !Number.isFinite(seconds) || seconds <= 0) return state;
    // Fixed-size substeps keep physics stable after a dropped rendering frame.
    let remaining = Math.min(seconds, 0.1);
    while (remaining > 1e-8) {
      const dt = Math.min(remaining, 1 / 120); remaining -= dt;
      state.elapsed += dt; state.lapTime += dt;
      state.offroad = trackPosition(state.x, state.y).distance > TRACK.width / 2 - 8;
      const brake = Boolean(controls.brake), handbrake = Boolean(controls.handbrake);
      const gas = Boolean(controls.gas) && !brake && !handbrake;
      const boosting = gas && Boolean(controls.nitro) && state.boost > 0 && !state.offroad;
      const acceleration = gas ? (boosting ? 290 : 190) : 0;
      const resistance = 24 + state.speed * 0.12 + (state.offroad ? 125 : 0);
      const deceleration = (brake ? 330 : 0) + (handbrake ? 430 : 0);
      const limit = state.offroad ? 105 : boosting ? 350 : 270;
      state.speed = clamp(state.speed + (acceleration - resistance - deceleration) * dt, 0, limit);
      state.boost = clamp(state.boost + (boosting ? -33 : 12) * dt, 0, 100);
      const steer = clamp(Number(controls.steering) || 0, -1, 1);
      state.heading += steer * 2.1 * clamp(state.speed / 125, 0, 1) * (handbrake ? 1.4 : 1) * dt;
      state.x = clamp(state.x + Math.cos(state.heading) * state.speed * dt, 15, 1185);
      state.y = clamp(state.y + Math.sin(state.heading) * state.speed * dt, 15, 685);
      checkpoint(state);
    }
    return state;
  }

  const api = { TRACK, createRace, trackPosition, checkpoint, step };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.NonaRace = api;
})(typeof globalThis === 'undefined' ? this : globalThis);
