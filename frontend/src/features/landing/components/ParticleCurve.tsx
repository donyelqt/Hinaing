"use client";

import { useEffect, useRef } from "react";

type ParticleCurveProps = {
  className?: string;
};

type Palette = {
  /** Thin lit line along the rim. */
  rim: [number, number, number];
  /** Saturated band just outside the rim. */
  mid: [number, number, number];
  /** Wide sparse dust that thins out with distance. */
  bulk: [number, number, number];
  /** Free-floating dust motes. */
  dust: [number, number, number];
};

// The reference runs pink to magenta. This swaps that for the indigo family
// so the accent matches the brand while keeping the reference's tonal roles:
// bright rim, saturated band, deep dust.
// Rim and motes sit above the band so the arc still reads a lit line with
// bright motes hanging off it. The reference motes are white, which vanishes
// on our slate-50 page, so they carry a saturated indigo instead.
const BASE_RIM: [number, number, number] = [165, 180, 252];
const BASE_MID: [number, number, number] = [99, 102, 241];
const BASE_BULK: [number, number, number] = [49, 46, 129];
const BASE_DUST: [number, number, number] = [129, 140, 248];

const TAU = Math.PI * 2;
const PARTICLE_BUDGET = 220_000;
/** The reference advances its clock at 60 units per second. */
const FRAME_MS = 1000 / 60;
/** Dither reseeds every 90 clock units, so 1.5 seconds. */
const DITHER_PERIOD = 90;

/** murmur3 finalizer, matching the reference shader's `hash_u32`. */
function hash(value: number): number {
  let mixed = value >>> 0;
  mixed = Math.imul(mixed ^ (mixed >>> 16), 0x7feb352d);
  mixed = Math.imul(mixed ^ (mixed >>> 15), 0x846ca68b);
  return (mixed ^ (mixed >>> 16)) >>> 0;
}

function noise01(value: number): number {
  return (hash(value) >>> 8) / 16777216;
}

function buildPalette(): Palette {
  return {
    rim: BASE_RIM,
    mid: BASE_MID,
    bulk: BASE_BULK,
    dust: BASE_DUST,
  };
}

type Arc = {
  scale: number;
  centerX: number;
  centerY: number;
  radius: number;
  thetaMin: number;
  thetaMax: number;
  /**
   * Half-plane the band may occupy: a point on the rim chord plus the normal
   * that points away from the circle's centre.
   */
  bandSide: { x: number; y: number; nx: number; ny: number } | null;
};

/**
 * Fits a circle whose arc runs across the viewport from the lower left to the
 * upper right, then reports the angular window that arc subtends.
 */
function fitArc(width: number, height: number): Arc {
  const scale = Math.min(2, Math.max(0.5, Math.sqrt((width * height) / (1920 * 1080))));
  const offsetX = -724 * scale + (width - 1920 * scale) * 0.4;
  const radiusY = 2000 * scale;
  const radiusX = 2500 * scale;

  const top = offsetX + Math.sqrt(radiusX * radiusX - radiusY * radiusY);
  const chord = width - offsetX;
  const chordY = radiusY > chord ? radiusY - Math.sqrt(radiusX * radiusX - chord * chord) : Infinity;

  const left = Math.min(top, width * 0.405);
  const bottom = Math.min(chordY, height * 0.585);
  const spanX = width - left;
  const spanY = bottom;
  const diagonal = Math.hypot(spanX, spanY);

  const sagitta = diagonal * 0.062;
  const radius = (diagonal * diagonal) / (8 * sagitta) + sagitta * 0.5;
  const centerX = (left + width) * 0.5 - (spanY / diagonal) * (radius - sagitta);
  const centerY = bottom * 0.5 + (spanX / diagonal) * (radius - sagitta);

  let thetaMin = Infinity;
  let thetaMax = -Infinity;
  for (let step = 0; step <= 32; step += 1) {
    const ratio = step / 32;
    const edgeSamples: Array<[number, number]> = [
      [width * ratio, 0],
      [width * ratio, height],
      [0, height * ratio],
      [width, height * ratio],
    ];
    for (const [x, y] of edgeSamples) {
      const theta = Math.atan2(y - centerY, x - centerX);
      if (theta < thetaMin) thetaMin = theta;
      if (theta > thetaMax) thetaMax = theta;
    }
  }

  // Keep the outer field on the outward side of the rim chord. Without this,
  // a frame tall enough to bring the far side of the circle into view wraps
  // the dust back around the rim and floods the copy above it. On wide frames
  // the far side is already outside the frame, so the clip changes nothing.
  let bandSide: Arc["bandSide"] = null;
  const edgeX = width - left;
  const edgeY = bottom;
  const length = Math.hypot(edgeX, edgeY);
  if (length > 0) {
    let nx = edgeY / length;
    let ny = -edgeX / length;
    const toCentreX = centerX - (left + width) / 2;
    const toCentreY = centerY - bottom / 2;
    if (toCentreX * nx + toCentreY * ny > 0) {
      nx = -nx;
      ny = -ny;
    }
    bandSide = { x: left, y: 0, nx, ny };
  }

  return {
    scale,
    centerX,
    centerY,
    radius,
    thetaMin: thetaMin - 0.04,
    thetaMax: thetaMax + 0.04,
    bandSide,
  };
}

function renderCurve(canvas: HTMLCanvasElement, width: number, height: number, clock: number): void {
  // Resizing the bitmap resets it and allocates a new buffer, so only touch
  // the dimensions when they actually change. This runs every frame.
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }

  const palette = buildPalette();
  const arc = fitArc(width, height);
  const scale = arc.scale;

  const context = canvas.getContext("2d");
  if (!context) return;

  const image = context.createImageData(width, height);
  const data = image.data;

  const midX = width / 2;
  const midY = height / 2;
  const vignetteRadius = 1600 * scale;

  /** Radial falloff toward the viewport edges, matching the reference. */
  const vignette = (x: number, y: number): number => {
    const normalized = Math.hypot(x - midX, y - midY) / vignetteRadius;
    const value = 1 - normalized * normalized * normalized;
    return value > 0.2 ? value : 0.2;
  };

  const halfWidth = Math.ceil(width / 2);
  const halfHeight = Math.ceil(height / 2);
  const columns = halfWidth;

  // The reference resolves the arc into 2px cells. Each cell keeps one ink
  // colour and a dithered share of the band profile.
  const inkR = new Float32Array(halfWidth * halfHeight);
  const inkG = new Float32Array(halfWidth * halfHeight);
  const inkB = new Float32Array(halfWidth * halfHeight);
  const occupied = new Uint8Array(halfWidth * halfHeight);

  const rimWidth = 5 * scale;
  const midWidth = 14 * scale;
  const bulkWidth = 120 * scale;
  const bulkReach = 10 * scale;
  const dustWidth = 600 * scale;
  const dustReach = 30 * scale;

  /** Phase of the rim shimmer, per the reference `glimmer`. */
  const glimmerPhase = clock * (TAU * 2.2 / 720);
  const glimmerFrequency = TAU * 2.2 / (arc.thetaMax - arc.thetaMin);

  const frame = Math.max(0, Math.floor(clock));

  for (let row = 0; row < halfHeight; row += 1) {
    const y = row * 2;
    const dy = y - arc.centerY;
    for (let col = 0; col < halfWidth; col += 1) {
      const x = col * 2;
      const dx = x - arc.centerX;
      const rimDistance = Math.hypot(dx, dy) - arc.radius;
      if (rimDistance < 0) continue;
      if (
        arc.bandSide &&
        (x - arc.bandSide.x) * arc.bandSide.nx + (y - arc.bandSide.y) * arc.bandSide.ny < 0
      ) {
        continue;
      }

      const shade = vignette(x + 1, y + 1);
      const theta = Math.atan2(dy, dx);
      const index = row * columns + col;
      let colour: [number, number, number] | null = null;
      let intensity = shade;

      if (rimDistance < rimWidth) {
        colour = palette.rim;
        intensity *= 1 + 0.16 * Math.sin(theta * glimmerFrequency - glimmerPhase);
      } else {
        const rimShare = Math.exp(-rimDistance / midWidth);
        const midShare = Math.exp(-rimDistance / bulkWidth) * Math.min(1, rimDistance / bulkReach) * 0.85;
        const dustShare = Math.exp(-rimDistance / dustWidth) * Math.min(1, rimDistance / dustReach) * 0.7;
        const total = Math.min(1, rimShare + midShare + dustShare);

        if (total > 0.003) {
          // Staggered reseed. Each cell picks a slot in a 90 frame cycle, so
          // the field repaints in waves instead of all at once.
          const bucket = hash(index ^ 0x85ebca6b) % DITHER_PERIOD;
          const generation = Math.floor((frame + DITHER_PERIOD - 1 - bucket) / DITHER_PERIOD);
          const roll = noise01(index ^ Math.imul(generation, 0xc2b2ae35) ^ 0x20260712);

          if (roll < rimShare) {
            colour = palette.rim;
            intensity *= 1 + 0.16 * Math.sin(theta * glimmerFrequency - glimmerPhase);
          } else if (roll < rimShare + midShare) {
            colour = palette.mid;
          } else if (roll < total) {
            colour = palette.bulk;
          }
        }
      }

      if (colour) {
        occupied[index] = 1;
        inkR[index] = colour[0] * intensity;
        inkG[index] = colour[1] * intensity;
        inkB[index] = colour[2] * intensity;
      }
    }
  }

  let offset = 0;
  for (let y = 0; y < height; y += 1) {
    const rowBase = (y >> 1) * columns;
    for (let x = 0; x < width; x += 1) {
      const sample = rowBase + (x >> 1);
      if (!occupied[sample]) {
        // Leave the page background alone. The reference paints black here
        // because its page is black; ours is slate-50.
        offset += 4;
        continue;
      }
      // The reference's `pixel_grain` hashes the full-resolution pixel index.
      const grain = (noise01(y * width + x ^ 0x9e3779b9) - 0.5) * 24;
      data[offset] = inkR[sample] + grain;
      data[offset + 1] = inkG[sample] + grain;
      data[offset + 2] = inkB[sample] + grain;
      data[offset + 3] = 255;
      offset += 4;
    }
  }

  // Free dust motes. They ride inward along the arc and wrap at the rim,
  // which is what makes the field crawl.
  const reach = 500 * scale;
  const particleCount = Math.min(
    30_000,
    Math.round(0.1 * 0.25 * (arc.thetaMax - arc.thetaMin) * (arc.radius - reach / 2) * reach * 0.25),
  );

  for (let i = 0; i < particleCount; i += 1) {
    const seed = hash(i ^ 0xa511e9b3);
    const thetaBase = arc.thetaMin + (arc.thetaMax - arc.thetaMin) * noise01(seed);
    const sampled = reach * (1 - Math.cbrt(noise01(seed ^ 0x63d83595)));
    const maxDepth = Math.max(sampled, 14 * scale);
    const speed = (0.14 + noise01(seed ^ 0x9e3779b9) * 0.22) * scale;
    const phase = noise01(seed ^ 0xc2b2ae35) * maxDepth;
    const travel = clock * speed + phase;
    const depth = travel - Math.floor(travel / maxDepth) * maxDepth;
    const radius = arc.radius - depth;

    const waveFrequency = 0.004 + noise01(seed ^ 0x27d4eb2f) * 0.011;
    const wavePhase = noise01(seed ^ 0x165667b1) * TAU;
    const wander = -(0.06 * scale / waveFrequency) * Math.cos(clock * waveFrequency + wavePhase) / Math.max(radius, 1);
    const theta = thetaBase + wander;

    const pointX = arc.centerX + radius * Math.cos(theta);
    const pointY = arc.centerY + radius * Math.sin(theta);

    const fadeIn = Math.min(1, depth / 3);
    const fadeOut = (maxDepth - depth) / (maxDepth * 0.25);
    const opacity = Math.max(0, Math.min(fadeIn, fadeOut));
    if (opacity <= 0) continue;

    const intensity = vignette(pointX, pointY);
    const px = Math.ceil(pointX - 1.5);
    const py = Math.ceil(pointY - 1.5);
    for (let row = py; row < py + 2; row += 1) {
      if (row < 0 || row >= height) continue;
      for (let col = px; col < px + 2; col += 1) {
        if (col < 0 || col >= width) continue;
        const index = (row * width + col) * 4;
        // Composite the mote over whatever is already there and write the
        // alpha. Unlike the reference we leave unoccupied pixels transparent,
        // so a mote landing on one has to supply its own cover or it would
        // be invisible.
        const cover = opacity;
        const dstAlpha = data[index + 3] / 255;
        const outAlpha = cover + dstAlpha * (1 - cover);
        const blend = (dst: number, src: number): number =>
          (src * cover + dst * dstAlpha * (1 - cover)) / outAlpha;
        data[index] = blend(data[index], palette.dust[0] * intensity);
        data[index + 1] = blend(data[index + 1], palette.dust[1] * intensity);
        data[index + 2] = blend(data[index + 2], palette.dust[2] * intensity);
        data[index + 3] = outAlpha * 255;
      }
    }
  }

  // Scanline grain, matching the reference's grade pass.
  offset = 0;
  for (let y = 0; y < height; y += 1) {
    const rowSeed = (y & 511) * 512;
    for (let x = 0; x < width; x += 1) {
      const value = noise01(rowSeed + (x & 511) ^ 3266489909);
      if (value < 0.045 && data[offset + 3] > 0) {
        const level = value < 0.023 ? 0 : 255;
        const blend = 10 / 255;
        data[offset] += (level - data[offset]) * blend;
        data[offset + 1] += (level - data[offset + 1]) * blend;
        data[offset + 2] += (level - data[offset + 2]) * blend;
      }
      offset += 4;
    }
  }

  context.putImageData(image, 0, 0);
}

export function ParticleCurve({ className = "" }: ParticleCurveProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");

    let frame = 0;
    let resizeFrame = 0;
    const startedAt = performance.now();

    const draw = (clock: number): void => {
      const rect = canvas.getBoundingClientRect();
      const cssWidth = Math.max(320, rect.width);
      const cssHeight = Math.max(240, rect.height);
      const ratio = Math.max(1, window.devicePixelRatio || 1);
      const budget = Math.sqrt(PARTICLE_BUDGET / (cssWidth * cssHeight));
      const scale = Math.max(0.55, Math.min(ratio, budget));
      const width = Math.round(cssWidth * scale);
      const height = Math.round(cssHeight * scale);
      renderCurve(canvas, width, height, clock);
    };

    if (reduced.matches) {
      draw(0);
    } else {
      const loop = (now: number): void => {
        // The reference advances its clock at 60 units per second.
        draw((now - startedAt) / FRAME_MS);
        frame = requestAnimationFrame(loop);
      };
      frame = requestAnimationFrame(loop);
    }

    const onResize = (): void => {
      // Re-render at the live clock. Resizing must not restart the motion.
      // Phones fire resize on every address-bar collapse, so fold a burst of
      // events into one redraw.
      if (resizeFrame) return;
      resizeFrame = requestAnimationFrame(() => {
        resizeFrame = 0;
        draw((performance.now() - startedAt) / FRAME_MS);
      });
    };

    window.addEventListener("resize", onResize, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      cancelAnimationFrame(resizeFrame);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className={className}
      style={{ position: "absolute", inset: 0, width: "100%", height: "100%", imageRendering: "pixelated" }}
    />
  );
}
