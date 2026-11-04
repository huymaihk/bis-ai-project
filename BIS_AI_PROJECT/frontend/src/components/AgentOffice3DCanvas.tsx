import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { AgentStationMeta, DepartmentId, ProductRecord } from '../types/bisTypes';
import { AGENT_STATIONS } from '../data/mockBisData';
import {
  AGENT_DIALOGUE_SCRIPT,
  Agent3DActorState,
  CONFERENCE_TABLE_SPEC,
  createInitialAgentActors,
  findNearestAgentToPosition,
  getConferenceTableSeats,
  getFloorElevationAt,
  PAIRWISE_DIALOGUES,
  rallyAllAgentsToTable,
  resolveActorToActorCollisions,
  resolvePositionAgainstObstacles,
  RobotEyeStyle,
  RobotFinishPreset,
  setCommanderWalkTarget,
  stepActorMovementWithCollision,
  stepActorPhysics,
  triggerActorJump,
} from '../utils/agentOfficeSim';
import {
  MessageSquare,
  Sparkles,
  Volume2,
  Compass,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  Gamepad2,
  Palette,
  Users,
  Footprints,
  FlaskConical,
  Megaphone,
  BookOpen,
  Image as ImageIcon,
  Settings,
} from 'lucide-react';

interface AgentOffice3DCanvasProps {
  activeProduct: Pick<ProductRecord, 'sku'>;
  reduceMotion: boolean;
  eyeStyle: RobotEyeStyle;
  finishPreset: RobotFinishPreset;
  onChangeEyeStyle: (style: RobotEyeStyle) => void;
  onChangeFinishPreset: (preset: RobotFinishPreset) => void;
  onSelectStation?: (station: AgentStationMeta) => void;
  onNavigateDepartment?: (dept: DepartmentId) => void;
  onSelectDepartment?: (dept: DepartmentId) => void;
}

interface ProjectedBubble {
  id: DepartmentId;
  agentCode: string;
  displayName: string;
  roleTitle: string;
  colorHex: string;
  text: string;
  screenX: number;
  screenY: number;
  visible: boolean;
  isTalking: boolean;
}

interface RobotMeshParts {
  root: THREE.Group;
  bodyGroup: THREE.Group;
  headGroup: THREE.Group;
  leftArm: THREE.Group;
  rightArm: THREE.Group;
  leftLeg: THREE.Group;
  rightLeg: THREE.Group;
  leftEye: THREE.Mesh;
  rightEye: THREE.Mesh;
  shellMaterials: THREE.MeshPhysicalMaterial[];
  hitbox: THREE.Mesh;
}

// Pre-allocated scratch vectors outside render loop (Zero GC inside tick)
const _projVec = new THREE.Vector3();
const _targetCamPos = new THREE.Vector3();
const _targetLookAt = new THREE.Vector3();

function createRoundedBoxExtrudeGeometry(
  width: number,
  height: number,
  depth: number,
  radius: number
): THREE.ExtrudeGeometry {
  const shape = new THREE.Shape();
  const w = width - radius * 2;
  const h = height - radius * 2;
  const x = -w / 2;
  const y = -h / 2;

  shape.moveTo(x, y + radius);
  shape.lineTo(x, y + h - radius);
  shape.quadraticCurveTo(x, y + h, x + radius, y + h);
  shape.lineTo(x + w - radius, y + h);
  shape.quadraticCurveTo(x + w, y + h, x + w, y + h - radius);
  shape.lineTo(x + w, y + radius);
  shape.quadraticCurveTo(x + w, y, x + w - radius, y);
  shape.lineTo(x + radius, y);
  shape.quadraticCurveTo(x, y, x, y + radius);

  const geo = new THREE.ExtrudeGeometry(shape, {
    depth: Math.max(0.02, depth - radius * 2),
    bevelEnabled: true,
    bevelSegments: 4,
    steps: 1,
    bevelSize: radius,
    bevelThickness: radius,
  });
  geo.center();
  return geo;
}

/**
 * Linear-Space Grayscale Brushed Metal Micro-Grain & Seam Bump/Roughness Map
 * Gives robot armor and floor tiles authentic CNC-machined anisotropic surface relief.
 */
function createBrushedMetalBumpTexture(repeatX = 2, repeatY = 2): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 256;
  const ctx = canvas.getContext('2d')!;

  ctx.fillStyle = '#808080';
  ctx.fillRect(0, 0, 256, 256);

  // Fine horizontal CNC brushed grain lines
  for (let y = 0; y < 256; y += 2) {
    const lum = 116 + ((y * 17) % 26);
    ctx.strokeStyle = `rgb(${lum}, ${lum}, ${lum})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(256, y);
    ctx.stroke();
  }

  // Subtle machined panel seam grooves
  ctx.strokeStyle = '#404040';
  ctx.lineWidth = 2;
  ctx.strokeRect(12, 12, 232, 232);
  ctx.strokeStyle = '#B8B8B8';
  ctx.lineWidth = 1;
  ctx.strokeRect(14, 14, 228, 228);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.NoColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(repeatX, repeatY);
  return tex;
}

/**
 * Procedural Brushed Bronze-Titanium Metallic Tile Floor Texture (Physical Industrial Floor)
 */
function createMetallicTileFloorTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d')!;

  const grad = ctx.createLinearGradient(0, 0, 512, 512);
  grad.addColorStop(0, '#726255');
  grad.addColorStop(0.5, '#847264');
  grad.addColorStop(1, '#645448');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 512, 512);

  // Fine brushed metal grain lines
  ctx.strokeStyle = 'rgba(255, 248, 238, 0.06)';
  ctx.lineWidth = 1;
  for (let y = 0; y < 512; y += 2) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(512, y);
    ctx.stroke();
  }

  // Secondary micro-grid lines (32px sub-tiles)
  const subStep = 32;
  ctx.strokeStyle = 'rgba(255, 244, 228, 0.06)';
  ctx.lineWidth = 1;
  for (let i = 0; i <= 512; i += subStep) {
    ctx.beginPath();
    ctx.moveTo(i, 0);
    ctx.lineTo(i, 512);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, i);
    ctx.lineTo(512, i);
    ctx.stroke();
  }

  // Primary physical floor plate expansion joints (128px spacing)
  const step = 128;
  ctx.strokeStyle = 'rgba(18, 12, 9, 0.72)';
  ctx.lineWidth = 3;
  for (let i = 0; i <= 512; i += step) {
    ctx.beginPath();
    ctx.moveTo(i, 0);
    ctx.lineTo(i, 512);
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0, i);
    ctx.lineTo(512, i);
    ctx.stroke();
  }

  // Machined metallic bevel highlight + corner hex rivets on each floor plate
  for (let x = 0; x < 512; x += step) {
    for (let y = 0; y < 512; y += step) {
      ctx.strokeStyle = 'rgba(248, 235, 212, 0.24)';
      ctx.lineWidth = 1.25;
      ctx.strokeRect(x + 2, y + 2, step - 4, step - 4);

      // 4 corner hex bolts per metallic tile
      ctx.fillStyle = 'rgba(30, 22, 18, 0.65)';
      [
        [x + 8, y + 8],
        [x + step - 8, y + 8],
        [x + 8, y + step - 8],
        [x + step - 8, y + step - 8],
      ].forEach(([bx, by]) => {
        ctx.beginPath();
        ctx.arc(bx, by, 2.2, 0, Math.PI * 2);
        ctx.fill();
      });
    }
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(9, 6);
  return tex;
}

/**
 * Soft Radial Contact Shadow Texture (Grounds Robots, Chairs & Desks flush to the floor)
 */
function createSoftShadowTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext('2d')!;

  const grad = ctx.createRadialGradient(64, 64, 6, 64, 64, 62);
  grad.addColorStop(0, 'rgba(10, 6, 4, 0.82)');
  grad.addColorStop(0.45, 'rgba(15, 9, 6, 0.48)');
  grad.addColorStop(0.8, 'rgba(20, 12, 8, 0.14)');
  grad.addColorStop(1, 'rgba(20, 12, 8, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 128, 128);

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/**
 * Woven Warm Beige-Bronze Rug Texture under the Central Oval Conference Table
 */
function createWovenRugTexture(): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 512;
  canvas.height = 512;
  const ctx = canvas.getContext('2d')!;

  const grad = ctx.createRadialGradient(256, 256, 30, 256, 256, 250);
  grad.addColorStop(0, '#B9A089');
  grad.addColorStop(0.75, '#A08770');
  grad.addColorStop(0.92, '#7D6551');
  grad.addColorStop(1, '#594637');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 512, 512);

  ctx.strokeStyle = 'rgba(255, 245, 232, 0.14)';
  ctx.lineWidth = 2;
  for (let r = 24; r < 246; r += 10) {
    ctx.beginPath();
    ctx.arc(256, 256, r, 0, Math.PI * 2);
    ctx.stroke();
  }

  ctx.strokeStyle = 'rgba(217, 160, 91, 0.55)';
  ctx.lineWidth = 6;
  ctx.beginPath();
  ctx.arc(256, 256, 244, 0, Math.PI * 2);
  ctx.stroke();

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

/**
 * High-Contrast Conference Table Top Texture ("Quy trình phiên 03026A")
 */
function createConferenceTableTexture(sku: string): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = 1024;
  canvas.height = 512;
  const ctx = canvas.getContext('2d')!;

  const bg = ctx.createRadialGradient(512, 256, 30, 512, 256, 480);
  bg.addColorStop(0, '#6B4F3F');
  bg.addColorStop(0.6, '#483429');
  bg.addColorStop(1, '#2D1F18');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, 1024, 512);

  ctx.strokeStyle = '#FDE68A';
  ctx.lineWidth = 7;
  ctx.beginPath();
  ctx.ellipse(512, 256, 456, 214, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.strokeStyle = 'rgba(252, 211, 77, 0.45)';
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.ellipse(512, 256, 430, 192, 0, 0, Math.PI * 2);
  ctx.stroke();

  ctx.fillStyle = '#FFFBEB';
  ctx.font = 'bold 36px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.fillText(`Quy trình phiên ${sku}`, 512, 162);

  const steps = [
    { icon: '📄', label: 'Nguồn PDF' },
    { icon: '📝', label: 'Nội dung' },
    { icon: '🖼️', label: 'Ảnh Studio' },
    { icon: '✓', label: 'Kiểm duyệt' },
  ];
  const startX = 206;
  const gap = 204;
  steps.forEach((step, idx) => {
    const cx = startX + idx * gap;
    const cy = 272;

    ctx.fillStyle = idx === 2 ? 'rgba(217, 56, 44, 0.92)' : 'rgba(36, 26, 21, 0.92)';
    ctx.strokeStyle = '#FDE68A';
    ctx.lineWidth = 3.5;
    ctx.beginPath();
    ctx.roundRect(cx - 76, cy - 46, 152, 92, 22);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#FFFBEB';
    ctx.font = 'bold 28px Inter, sans-serif';
    ctx.fillText(step.icon, cx, cy - 4);

    ctx.fillStyle = '#FAF6F0';
    ctx.font = 'bold 19px Inter, sans-serif';
    ctx.fillText(step.label, cx, cy + 28);

    if (idx < steps.length - 1) {
      ctx.fillStyle = '#FDE68A';
      ctx.font = 'bold 32px Inter, sans-serif';
      ctx.fillText('→', cx + 102, cy + 8);
    }
  });

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export type MonitorScreenKind =
  | 'technical'
  | 'marketing'
  | 'ops-check'
  | 'ops-store'
  | 'laptop-terminal'
  | 'wall-logo'
  | 'badge-bis';

/**
 * Redraws a dynamic computer monitor or laptop LCD canvas texture in real time (`t` in seconds)
 * so every screen in the 3D Command Room actively runs live waveforms, scanners, progress bars, and logs.
 */
function drawAnimatedMonitorScreen(
  tex: THREE.CanvasTexture,
  screenType: MonitorScreenKind,
  t: number,
  sku = '03026A'
): void {
  const canvas = tex.image as HTMLCanvasElement;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  if (screenType === 'laptop-terminal') {
    const w = canvas.width;
    const h = canvas.height;
    ctx.fillStyle = '#090D16';
    ctx.fillRect(0, 0, w, h);

    // Top status bar
    ctx.fillStyle = '#B91C1C';
    ctx.fillRect(0, 0, w, 24);
    ctx.fillStyle = '#FFFBEB';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`BIS AI · ${sku} · LIVE`, 10, 16);

    // Pulsing green indicator
    ctx.fillStyle = Math.sin(t * 7) > -0.2 ? '#34D399' : '#059669';
    ctx.beginPath();
    ctx.arc(w - 14, 12, 5, 0, Math.PI * 2);
    ctx.fill();

    // Live dual sine waveform
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.22)';
    ctx.lineWidth = 1;
    for (let gy = 40; gy < 105; gy += 16) {
      ctx.beginPath();
      ctx.moveTo(10, gy);
      ctx.lineTo(w - 10, gy);
      ctx.stroke();
    }

    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let x = 12; x <= w - 12; x += 6) {
      const y = 70 + Math.sin(x * 0.055 - t * 5.2) * 18 + Math.cos(x * 0.025 + t * 3.1) * 7;
      if (x === 12) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    // Animated telemetry bars at bottom
    [114, 132].forEach((by, idx) => {
      ctx.fillStyle = '#1E293B';
      ctx.fillRect(12, by, w - 24, 10);
      const ratio = 0.58 + 0.36 * (0.5 + 0.5 * Math.sin(t * (2.6 + idx) + idx * 1.7));
      ctx.fillStyle = idx === 0 ? '#10B981' : '#F59E0B';
      ctx.fillRect(12, by, (w - 24) * ratio, 10);
    });

    tex.needsUpdate = true;
    return;
  }

  // Standard 512x320 Desktop Studio Monitor Frame
  ctx.fillStyle = '#0F141C';
  ctx.fillRect(0, 0, 512, 320);
  ctx.fillStyle = '#1E2530';
  ctx.fillRect(0, 0, 512, 34);
  ['#EF4444', '#F59E0B', '#10B981'].forEach((c, i) => {
    ctx.fillStyle = c;
    ctx.beginPath();
    ctx.arc(20 + i * 18, 17, 5, 0, Math.PI * 2);
    ctx.fill();
  });

  // Live blinking status badge in window titlebar
  const blinkOn = Math.sin(t * 6.5) > -0.25;
  ctx.fillStyle = blinkOn ? '#10B981' : '#047857';
  ctx.beginPath();
  ctx.arc(426, 17, 5.5, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = '#E2E8F0';
  ctx.font = 'bold 12px monospace';
  ctx.textAlign = 'left';
  ctx.fillText('LIVE RUN', 437, 21);

  ctx.fillStyle = '#F8F5F0';
  ctx.fillRect(12, 42, 488, 266);

  if (screenType === 'technical') {
    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 13px monospace';
    ctx.fillText(`CAD / ISO 13934-1 ANALYZER · SKU ${sku}`, 78, 22);

    // Left pane: PDF Page 16 with animated vertical laser scanner beam
    ctx.fillStyle = '#FEE2E2';
    ctx.fillRect(24, 54, 188, 240);
    ctx.strokeStyle = '#FCA5A5';
    ctx.lineWidth = 2;
    ctx.strokeRect(24, 54, 188, 240);

    ctx.fillStyle = '#DC2626';
    ctx.beginPath();
    ctx.roundRect(68, 86, 100, 62, 10);
    ctx.fill();
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 28px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('PDF', 118, 127);

    ctx.fillStyle = '#7F1D1D';
    ctx.font = 'bold 14px monospace';
    ctx.fillText(`Trang 16 · ${sku}`, 118, 174);

    // Simulated spec text rows inside PDF
    for (let r = 0; r < 4; r++) {
      const ry = 192 + r * 18;
      ctx.fillStyle = '#B91C1C';
      ctx.fillRect(42, ry, 152 - (r % 2) * 28, 8);
    }

    // Moving horizontal laser scanner bar across PDF
    const scanY = 64 + ((Math.sin(t * 2.8) * 0.5 + 0.5) * 212);
    ctx.fillStyle = 'rgba(14, 165, 233, 0.28)';
    ctx.fillRect(26, scanY - 8, 184, 16);
    ctx.fillStyle = '#0284C7';
    ctx.fillRect(26, scanY, 184, 3);

    const activeLine = 1 + (Math.floor(t * 9) % 48);
    ctx.fillStyle = '#0F172A';
    ctx.fillRect(36, 266, 164, 20);
    ctx.fillStyle = '#38BDF8';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`OCR LINE ${String(activeLine).padStart(2, '0')}/48 PASS`, 118, 280);

    // Right Top Pane: Dark Oscilloscope with Moving Crosshead & Live Stress-Strain Curve
    ctx.fillStyle = '#0F172A';
    ctx.fillRect(226, 54, 262, 146);
    ctx.strokeStyle = '#1E293B';
    ctx.lineWidth = 1;
    for (let gx = 250; gx < 480; gx += 28) {
      ctx.beginPath();
      ctx.moveTo(gx, 54);
      ctx.lineTo(gx, 200);
      ctx.stroke();
    }

    // Twin cyan columns of tensile tester + moving red crosshead
    ctx.fillStyle = '#0EA5E9';
    ctx.fillRect(246, 68, 10, 118);
    ctx.fillRect(316, 68, 10, 118);
    const crossheadY = 108 + Math.sin(t * 2.5) * 26;
    ctx.fillStyle = '#EF4444';
    ctx.fillRect(238, crossheadY, 96, 11);

    // Live scrolling tensile curve (0.5 - 50 kN)
    ctx.strokeStyle = '#38BDF8';
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let x = 340; x <= 476; x += 5) {
      const wy =
        132 +
        Math.sin((x - 340) * 0.06 - t * 4.5) * 28 +
        Math.cos((x - 340) * 0.03 + t * 2.2) * 10;
      if (x === 340) ctx.moveTo(x, wy);
      else ctx.lineTo(x, wy);
    }
    ctx.stroke();

    const liveKn = (36.5 + Math.sin(t * 2.5) * 12.8).toFixed(1);
    ctx.fillStyle = '#FDE68A';
    ctx.font = 'bold 13px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`LOAD: ${liveKn} / 50.0 kN`, 338, 76);

    // Right Bottom Pane: 3 Animated Spec Progress Bars
    const bars = [
      { label: 'ISO 13934-1', color: '#0284C7', phase: 0 },
      { label: 'ASTM D5034', color: '#10B981', phase: 1.4 },
      { label: '1,200mm Stroke', color: '#D97706', phase: 2.8 },
    ];
    bars.forEach((b, idx) => {
      const y = 212 + idx * 28;
      ctx.fillStyle = '#E2E8F0';
      ctx.fillRect(226, y, 262, 18);
      const pct = 0.72 + 0.26 * (0.5 + 0.5 * Math.sin(t * 2.2 + b.phase));
      ctx.fillStyle = b.color;
      ctx.fillRect(226, y, 262 * pct, 18);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 11px monospace';
      ctx.textAlign = 'left';
      ctx.fillText(`${b.label} · ${Math.round(pct * 100)}%`, 234, y + 13);
    });
  } else if (screenType === 'marketing') {
    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 13px monospace';
    ctx.fillText(`CONTENT & SEO STUDIO · VI/EN · ${sku}`, 78, 22);

    // Left pane: Crimson fabric swatch with live diagonal light sweep
    ctx.fillStyle = '#7F1D1D';
    ctx.beginPath();
    ctx.roundRect(26, 54, 184, 186, 12);
    ctx.fill();

    ctx.fillStyle = '#DC2626';
    ctx.beginPath();
    ctx.roundRect(40, 68, 156, 140, 8);
    ctx.fill();

    // Animated specular highlight band across fabric swatch
    const sweepX = 44 + ((t * 55) % 140);
    ctx.fillStyle = 'rgba(254, 240, 138, 0.32)';
    ctx.fillRect(sweepX, 68, 22, 140);

    ctx.fillStyle = '#FFFBEB';
    ctx.font = 'bold 12px monospace';
    ctx.textAlign = 'center';
    ctx.fillText('ΔE 0.42 · 4:3 PASS', 118, 228);

    // Right pane: Live typing bilingual copy lines + SEO gauge
    ctx.fillStyle = '#0F172A';
    ctx.font = 'bold 16px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`Máy Đo Độ Bền Kéo ${sku}`, 228, 74);

    [96, 118, 140, 162].forEach((ly, idx) => {
      ctx.fillStyle = '#E2E8F0';
      ctx.fillRect(228, ly, 250, 12);
      const typeLen = 120 + Math.floor(130 * (0.5 + 0.5 * Math.sin(t * 2.4 - idx * 0.7)));
      ctx.fillStyle = idx === 0 ? '#0284C7' : '#475569';
      ctx.fillRect(228, ly, typeLen, 12);
    });

    // SEO Score Badge
    const seoChars = 144 + Math.floor(4 * Math.sin(t * 2.0));
    ctx.fillStyle = '#DCFCE7';
    ctx.strokeStyle = '#16A34A';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.roundRect(228, 188, 178, 48, 10);
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#15803D';
    ctx.font = 'bold 15px monospace';
    ctx.fillText(`SEO ${seoChars}/160 · 96%`, 240, 217);

    ctx.fillStyle = '#1E293B';
    ctx.font = 'bold 38px Inter, sans-serif';
    ctx.fillText('Aa', 422, 224);

    // Bottom pane: Live Storefront Conversion Sparkline
    ctx.fillStyle = '#0F172A';
    ctx.beginPath();
    ctx.roundRect(26, 250, 460, 46, 10);
    ctx.fill();

    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 3;
    ctx.beginPath();
    for (let x = 38; x <= 472; x += 8) {
      const sy = 273 + Math.sin(x * 0.045 - t * 4.2) * 12;
      if (x === 38) ctx.moveTo(x, sy);
      else ctx.lineTo(x, sy);
    }
    ctx.stroke();
  } else if (screenType === 'ops-check') {
    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 13px monospace';
    ctx.fillText(`QA CHECKLIST · 5/5 APPROVED · ${sku}`, 78, 22);

    const activeRow = Math.floor(t * 1.8) % 3;
    const labels = [
      'Thông số Kỹ thuật & PDF Trang 16',
      'Nội dung VI/EN & Chuẩn SEO 148 ký tự',
      'Bộ ảnh Studio 4:3 & Kiểm tra Trùng lặp',
    ];
    [56, 122, 188].forEach((y, idx) => {
      const isFocused = idx === activeRow;
      if (isFocused) {
        ctx.fillStyle = '#ECFDF5';
        ctx.fillRect(22, y - 4, 468, 56);
      }

      ctx.fillStyle = '#DCFCE7';
      ctx.strokeStyle = '#16A34A';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.roundRect(30, y, 46, 46, 10);
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = '#15803D';
      ctx.font = 'bold 30px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('✓', 53, y + 34);

      ctx.fillStyle = '#0F172A';
      ctx.font = 'bold 15px Inter, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText(labels[idx], 92, y + 18);

      // Animated verification progress bar
      ctx.fillStyle = '#CBD5E1';
      ctx.fillRect(92, y + 28, 290, 12);
      const fillW = isFocused ? 220 + Math.sin(t * 5) * 65 : 290;
      ctx.fillStyle = '#10B981';
      ctx.fillRect(92, y + 28, fillW, 12);

      ctx.fillStyle = '#15803D';
      ctx.font = 'bold 13px monospace';
      ctx.fillText('PASS', 402, y + 38);
    });

    // Bottom live terminal log bar
    ctx.fillStyle = '#0F172A';
    ctx.fillRect(24, 258, 464, 38);
    ctx.fillStyle = '#34D399';
    ctx.font = 'bold 13px monospace';
    ctx.textAlign = 'left';
    const pct = 88 + (Math.floor(t * 14) % 13);
    ctx.fillText(`> [QA-GATE] Verify SKU ${sku} (50kN vs 30kN) ... ${pct}% OK`, 34, 282);
  } else if (screenType === 'ops-store') {
    ctx.fillStyle = '#94A3B8';
    ctx.font = 'bold 13px monospace';
    ctx.fillText(`HARAVAN STOREFRONT SYNC · ${sku}`, 78, 22);

    ctx.fillStyle = '#B91C1C';
    ctx.font = 'italic 900 24px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(`BIS STORE · ${sku}`, 28, 74);

    // Product visual card with animated scanner frame
    ctx.fillStyle = '#991B1B';
    ctx.beginPath();
    ctx.roundRect(28, 86, 194, 156, 10);
    ctx.fill();

    const pulsePad = 6 + Math.sin(t * 3.5) * 4;
    ctx.strokeStyle = '#FDE68A';
    ctx.lineWidth = 2.5;
    ctx.strokeRect(28 + pulsePad, 86 + pulsePad, 194 - pulsePad * 2, 156 - pulsePad * 2);

    ctx.fillStyle = '#FFFBEB';
    ctx.font = 'bold 15px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`SKU ${sku} · 50kN`, 125, 170);

    // Right pane: Live 92% Similarity Comparison (`03026A` vs `03026`)
    ctx.fillStyle = '#0F172A';
    ctx.font = 'bold 14px monospace';
    ctx.textAlign = 'left';
    ctx.fillText('SIMILARITY: 92% vs 03026', 242, 102);

    [116, 146, 176].forEach((by, idx) => {
      ctx.fillStyle = '#E2E8F0';
      ctx.fillRect(242, by, 240, 16);
      const w = 165 + Math.sin(t * 3 + idx) * 55;
      ctx.fillStyle = idx === 0 ? '#0EA5E9' : idx === 1 ? '#F59E0B' : '#10B981';
      ctx.fillRect(242, by, w, 16);
    });

    // Glowing Animated Publish CTA Button
    ctx.fillStyle = '#D9382C';
    ctx.beginPath();
    ctx.roundRect(242, 214, 240, 56, 12);
    ctx.fill();

    const shimmerX = 248 + ((t * 140) % 210);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.26)';
    ctx.fillRect(shimmerX, 216, 24, 52);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 19px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('🛒 ĐỒNG BỘ HARAVAN', 362, 249);
  }

  tex.needsUpdate = true;
}

/**
 * Realistic Computer Monitor UI Screen Textures for Each Department Station
 */
function createMonitorScreenTexture(
  screenType: MonitorScreenKind,
  sku = '03026A'
): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = screenType === 'laptop-terminal' ? 256 : 512;
  canvas.height = screenType === 'laptop-terminal' ? 160 : 320;

  if (screenType === 'wall-logo') {
    canvas.width = 1024;
    canvas.height = 320;
    const wCtx = canvas.getContext('2d')!;
    const g = wCtx.createLinearGradient(0, 0, 1024, 320);
    g.addColorStop(0, '#D8C8B6');
    g.addColorStop(0.5, '#EFE5D8');
    g.addColorStop(1, '#CBB8A3');
    wCtx.fillStyle = g;
    wCtx.fillRect(0, 0, 1024, 320);

    wCtx.fillStyle = '#B91C1C';
    wCtx.font = 'italic 900 142px Inter, sans-serif';
    wCtx.textAlign = 'center';
    wCtx.fillText('BIS', 512, 175);

    wCtx.fillStyle = '#2A1F1A';
    wCtx.font = 'bold 46px Inter, sans-serif';
    wCtx.fillText('T E X T I L E   A I', 512, 248);

    const wTex = new THREE.CanvasTexture(canvas);
    wTex.colorSpace = THREE.SRGBColorSpace;
    return wTex;
  }

  if (screenType === 'badge-bis') {
    canvas.width = 256;
    canvas.height = 128;
    const bCtx = canvas.getContext('2d')!;
    const bg = bCtx.createLinearGradient(0, 0, 256, 128);
    bg.addColorStop(0, '#E2DDD5');
    bg.addColorStop(0.5, '#F8F5F0');
    bg.addColorStop(1, '#B8AEA2');
    bCtx.fillStyle = bg;
    bCtx.fillRect(0, 0, 256, 128);
    bCtx.strokeStyle = '#475569';
    bCtx.lineWidth = 6;
    bCtx.strokeRect(3, 3, 250, 122);
    bCtx.fillStyle = '#B91C1C';
    bCtx.font = 'italic 900 74px Inter, sans-serif';
    bCtx.textAlign = 'center';
    bCtx.fillText('BIS', 128, 90);
    const bTex = new THREE.CanvasTexture(canvas);
    bTex.colorSpace = THREE.SRGBColorSpace;
    return bTex;
  }

  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  drawAnimatedMonitorScreen(tex, screenType, 0, sku);
  return tex;
}

const STATION_WALK_TARGETS: Record<
  DepartmentId,
  { x: number; z: number; title: string; subtitle: string; Icon: React.FC<{ className?: string }> }
> = {
  overview: {
    x: 0,
    z: -3.85,
    title: 'Chỉ huy BIS',
    subtitle: 'Điều phối Quy trình 03026A',
    Icon: Users,
  },
  technical: {
    x: -7.4,
    z: -3.25,
    title: 'Technical',
    subtitle: 'Hồ sơ kỹ thuật · Spec · PDF',
    Icon: FlaskConical,
  },
  marketing: {
    x: 7.4,
    z: -3.25,
    title: 'Marketing',
    subtitle: 'Nội dung sản phẩm · Truyền thông',
    Icon: Megaphone,
  },
  knowledge: {
    x: -6.8,
    z: 0.85,
    title: 'Knowledge',
    subtitle: 'Thư viện · Tri thức · Lưu trữ',
    Icon: BookOpen,
  },
  imagestudio: {
    x: 6.8,
    z: 0.85,
    title: 'Image Studio',
    subtitle: 'Chụp · Xử lý · Ảnh sản phẩm',
    Icon: ImageIcon,
  },
  operations: {
    x: -2.4,
    z: 3.85,
    title: 'Operations',
    subtitle: 'Quản lý tác vụ · Kiểm duyệt · Xuất bản',
    Icon: Settings,
  },
  memory: {
    x: 2.4,
    z: 3.85,
    title: 'Memory',
    subtitle: 'Lịch sử · Ghi chú · Đồng bộ',
    Icon: Compass,
  },
};

export const AgentOffice3DCanvas: React.FC<AgentOffice3DCanvasProps> = ({
  activeProduct,
  reduceMotion,
  eyeStyle,
  finishPreset,
  onChangeEyeStyle,
  onChangeFinishPreset,
  onSelectStation,
  onNavigateDepartment,
  onSelectDepartment,
}) => {
  const canvasMountRef = useRef<HTMLDivElement | null>(null);
  const actorsRef = useRef<Agent3DActorState[]>(createInitialAgentActors());
  const keysRef = useRef<Record<string, boolean>>({});
  const cameraModeRef = useRef<'overview' | 'cinematic_8d' | 'follow_commander' | 'meeting_closeup'>('overview');
  const focusedDeptRef = useRef<DepartmentId>('imagestudio');
  const finishPresetRef = useRef<RobotFinishPreset>(finishPreset);
  const reduceMotionRef = useRef<boolean>(reduceMotion);
  const walkRingTimerRef = useRef<number>(0);
  const walkRingPosRef = useRef<{ x: number; z: number }>({ x: 0, z: -3.55 });
  const dialogueIndexRef = useRef<number>(0);

  const [cameraMode, setCameraMode] = useState<
    'overview' | 'cinematic_8d' | 'follow_commander' | 'meeting_closeup'
  >('overview');
  const [focusedDept, setFocusedDept] = useState<DepartmentId>('imagestudio');
  const [dockCollapsed, setDockCollapsed] = useState<boolean>(false);
  const [bubbles, setBubbles] = useState<ProjectedBubble[]>([]);
  const [liveConversationLog, setLiveConversationLog] = useState<string>(
    `Chỉ huy BIS ↔ Image Studio Robot: Đang chụp & xử lý bộ ảnh ${activeProduct.sku} theo chuẩn Benchmark!`
  );

  const handleOpenDepartment = (dept: DepartmentId) => {
    const station = AGENT_STATIONS.find((s) => s.id === dept);
    if (station && onSelectStation) {
      onSelectStation(station);
    }
    if (onNavigateDepartment) {
      onNavigateDepartment(dept);
    } else if (onSelectDepartment) {
      onSelectDepartment(dept);
    }
  };

  useEffect(() => {
    finishPresetRef.current = finishPreset;
  }, [finishPreset]);

  useEffect(() => {
    reduceMotionRef.current = reduceMotion;
  }, [reduceMotion]);

  const handleTriggerAllJump = () => {
    actorsRef.current = actorsRef.current.map((a, idx) =>
      triggerActorJump(a, 7.4 + (idx % 3) * 0.65)
    );
    setLiveConversationLog(
      `Tất cả 7 Robot Hợp Kim Titan & Chrome CNC vừa bật nhảy hưởng ứng tiến độ phiên ${activeProduct.sku}!`
    );
  };

  const handleRallyToConferenceTable = () => {
    actorsRef.current = rallyAllAgentsToTable(actorsRef.current, activeProduct.sku);
    walkRingPosRef.current = { x: 0, z: -3.55 };
    walkRingTimerRef.current = 3.2;
    setLiveConversationLog(
      `Chỉ huy BIS triệu tập toàn bộ 7 Robot chạy vòng quanh bàn họp trung tâm phiên ${activeProduct.sku} (Không đi xuyên bàn hay bục)!`
    );
  };

  const handleWalkCommanderToStation = (targetDept: DepartmentId) => {
    focusedDeptRef.current = targetDept;
    setFocusedDept(targetDept);
    const stationTarget = STATION_WALK_TARGETS[targetDept];
    const safeSpot = resolvePositionAgainstObstacles(stationTarget.x, stationTarget.z, 0.65);

    walkRingPosRef.current = { x: safeSpot.x, z: safeSpot.z };
    walkRingTimerRef.current = 3.2;

    const lines = AGENT_DIALOGUE_SCRIPT[targetDept] || AGENT_DIALOGUE_SCRIPT.overview;
    const pickedLine = lines[Math.floor(Math.random() * lines.length)];

    actorsRef.current = actorsRef.current.map((a) => {
      if (a.id === 'overview') {
        const jumped = triggerActorJump(a, 6.4);
        return {
          ...jumped,
          customTargetPos: { x: safeSpot.x, z: safeSpot.z },
          isRunning: true,
          isMoving: true,
          isTalking: true,
          talkingWithId: targetDept,
          currentSpeech: `Chỉ huy BIS → ${STATION_WALK_TARGETS[targetDept].title}: Kiểm tra tiến độ mã ${activeProduct.sku}!`,
          speechTimer: 7.0,
        };
      }
      if (a.id === targetDept) {
        const jumped = triggerActorJump(a, 6.6);
        return {
          ...jumped,
          isTalking: true,
          talkingWithId: 'overview',
          currentSpeech: pickedLine,
          speechTimer: 7.5,
        };
      }
      return a;
    });

    setLiveConversationLog(pickedLine);
  };

  const handleTriggerPairwiseChat = (preferredDept?: DepartmentId) => {
    const pair = preferredDept
      ? PAIRWISE_DIALOGUES.find(
          (p) => p.speakerA === preferredDept || p.speakerB === preferredDept
        ) || PAIRWISE_DIALOGUES[dialogueIndexRef.current % PAIRWISE_DIALOGUES.length]
      : PAIRWISE_DIALOGUES[dialogueIndexRef.current % PAIRWISE_DIALOGUES.length];

    dialogueIndexRef.current += 1;
    focusedDeptRef.current = pair.speakerA === 'overview' ? pair.speakerB : pair.speakerA;
    setFocusedDept(focusedDeptRef.current);

    actorsRef.current = actorsRef.current.map((a) => {
      if (a.id === pair.speakerA) {
        const jumped = triggerActorJump(a, 6.4);
        return {
          ...jumped,
          isTalking: true,
          talkingWithId: pair.speakerB,
          currentSpeech: pair.lineA,
          speechTimer: 7.0,
        };
      }
      if (a.id === pair.speakerB) {
        const jumped = triggerActorJump(a, 6.0);
        return {
          ...jumped,
          isTalking: true,
          talkingWithId: pair.speakerA,
          currentSpeech: pair.lineB,
          speechTimer: 7.5,
        };
      }
      return a;
    });

    setLiveConversationLog(`${pair.lineA} | ${pair.lineB}`);
  };

  useEffect(() => {
    const container = canvasMountRef.current;
    if (!container) return;

    // 1. Software WebGL detection per Three.js skill
    const isSoftwareGl = (() => {
      const gl = document.createElement('canvas').getContext('webgl2');
      if (!gl) return true;
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      const param = ext ? ext.UNMASKED_RENDERER_WEBGL : gl.RENDERER;
      const gpu = String(gl.getParameter(param));
      gl.getExtension('WEBGL_lose_context')?.loseContext();
      return /SwiftShader|llvmpipe|softpipe|Software|Basic Render/i.test(gpu);
    })();

    const width = container.clientWidth || 1000;
    const height = container.clientHeight || 520;

    // Rich Metallic Espresso-Bronze 8D Industrial Studio Atmosphere
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1E1612);
    scene.fog = new THREE.FogExp2(0x1E1612, 0.011);

    const camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 140);
    camera.position.set(0, 13.6, 21.8);
    camera.lookAt(0, 1.15, 0.35);

    const renderer = new THREE.WebGLRenderer({
      antialias: !isSoftwareGl,
      powerPreference: 'default',
      preserveDrawingBuffer: false,
    });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.04;
    renderer.setPixelRatio(isSoftwareGl ? 1 : Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = !isSoftwareGl;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 2. Mandatory High-Contrast Studio Environment Reflection (`RoomEnvironment`) for Real PBR Metals
    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.035).texture;
    pmremGenerator.dispose();

    // 3. Balanced 3-Point Warm/Cool Studio Lighting Rig for High-Contrast Metallic Speculars
    const hemiLight = new THREE.HemisphereLight(0xfff2df, 0x1c1512, 0.85);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xfff4e0, 1.85);
    keyLight.position.set(12, 24, 16);
    if (!isSoftwareGl) {
      keyLight.castShadow = true;
      keyLight.shadow.mapSize.width = 1024;
      keyLight.shadow.mapSize.height = 1024;
      keyLight.shadow.camera.left = -18;
      keyLight.shadow.camera.right = 18;
      keyLight.shadow.camera.top = 15;
      keyLight.shadow.camera.bottom = -15;
      keyLight.shadow.bias = -0.0005;
      keyLight.shadow.normalBias = 0.02;
    }
    scene.add(keyLight);

    const coolSteelRimLight = new THREE.DirectionalLight(0x93c5fd, 1.15);
    coolSteelRimLight.position.set(-15, 16, -12);
    scene.add(coolSteelRimLight);

    const warmCopperBackLight = new THREE.DirectionalLight(0xf59e0b, 0.9);
    warmCopperBackLight.position.set(14, 12, -10);
    scene.add(warmCopperBackLight);

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    // Let the surrounding page own wheel/touch scrolling over the office.
    controls.enableZoom = false;
    renderer.domElement.style.touchAction = 'pan-y';
    controls.enableDamping = !isSoftwareGl;
    controls.dampingFactor = 0.06;
    controls.maxPolarAngle = Math.PI / 2 - 0.06;
    controls.minDistance = 7;
    controls.maxDistance = 36;
    controls.target.set(0, 1.15, 0.35);

    // 5. Shared PBR Metallic Materials + Procedural CanvasTextures with Anisotropy
    const maxAniso = renderer.capabilities.getMaxAnisotropy();
    const floorTileTex = createMetallicTileFloorTexture();
    floorTileTex.anisotropy = maxAniso;
    const floorBumpTex = createBrushedMetalBumpTexture(9, 6);
    const robotMetalBumpTex = createBrushedMetalBumpTexture(3, 3);

    const softShadowTex = createSoftShadowTexture();
    const wovenRugTex = createWovenRugTexture();
    wovenRugTex.anisotropy = maxAniso;
    const conferenceTableTex = createConferenceTableTexture(activeProduct.sku);
    conferenceTableTex.anisotropy = maxAniso;
    const techScreenTex = createMonitorScreenTexture('technical', activeProduct.sku);
    const mktScreenTex = createMonitorScreenTexture('marketing', activeProduct.sku);
    const opsCheckTex = createMonitorScreenTexture('ops-check', activeProduct.sku);
    const opsStoreTex = createMonitorScreenTexture('ops-store', activeProduct.sku);
    const laptopScreenTex = createMonitorScreenTexture('laptop-terminal', activeProduct.sku);
    const wallLogoTex = createMonitorScreenTexture('wall-logo', activeProduct.sku);
    const bisBadgeTex = createMonitorScreenTexture('badge-bis', activeProduct.sku);

    const softShadowMat = new THREE.MeshBasicMaterial({
      map: softShadowTex,
      transparent: true,
      depthWrite: false,
      opacity: 0.88,
      polygonOffset: true,
      polygonOffsetFactor: -1,
      polygonOffsetUnits: -1,
    });

    const brushedTitaniumMat = new THREE.MeshPhysicalMaterial({
      color: 0xa69b8f,
      metalness: 0.92,
      roughness: 0.24,
      bumpMap: robotMetalBumpTex,
      bumpScale: 0.015,
      clearcoat: 0.55,
      clearcoatRoughness: 0.12,
      envMapIntensity: 1.4,
    });
    const darkGunmetalMat = new THREE.MeshStandardMaterial({
      color: 0x1e2229,
      metalness: 0.9,
      roughness: 0.38,
      envMapIntensity: 1.45,
    });
    const polishedChromeMat = new THREE.MeshPhysicalMaterial({
      color: 0xe2e8f0,
      metalness: 0.98,
      roughness: 0.07,
      clearcoat: 0.8,
      envMapIntensity: 1.85,
    });
    const anodizedGoldMat = new THREE.MeshStandardMaterial({
      color: 0xfbbf24,
      metalness: 0.92,
      roughness: 0.2,
      envMapIntensity: 2.0,
    });
    const crimsonAnodizedAlloyMat = new THREE.MeshPhysicalMaterial({
      color: 0xc82820,
      metalness: 0.84,
      roughness: 0.24,
      clearcoat: 0.55,
      clearcoatRoughness: 0.14,
      envMapIntensity: 1.85,
    });
    const warmBronzeAlloyMat = new THREE.MeshStandardMaterial({
      color: 0x755948,
      metalness: 0.72,
      roughness: 0.28,
      bumpMap: robotMetalBumpTex,
      bumpScale: 0.008,
    });
    const partitionWallMat = new THREE.MeshStandardMaterial({
      color: 0x5c473b,
      metalness: 0.64,
      roughness: 0.34,
    });
    const foliageLushMat = new THREE.MeshStandardMaterial({
      color: 0x3f6212,
      roughness: 0.58,
      metalness: 0.06,
    });
    const foliageBrightMat = new THREE.MeshStandardMaterial({
      color: 0x65a30d,
      roughness: 0.5,
      metalness: 0.06,
    });

    const officeGroup = new THREE.Group();
    scene.add(officeGroup);

    // Helper: Add a soft contact shadow disc at exact surface elevation + 0.004
    const addContactShadow = (
      parent: THREE.Object3D,
      x: number,
      y: number,
      z: number,
      rx: number,
      rz: number
    ) => {
      const sd = new THREE.Mesh(new THREE.PlaneGeometry(rx * 2, rz * 2), softShadowMat);
      sd.rotation.x = -Math.PI / 2;
      sd.position.set(x, y, z);
      parent.add(sd);
    };

    // Helper: Build Sculpted Lush Indoor Potted Plant (Bottom strictly at local y = 0)
    const buildPottedPlant = (scale = 1.0): THREE.Group => {
      const pg = new THREE.Group();
      pg.scale.setScalar(scale);

      addContactShadow(pg, 0, 0.005, 0, 0.42, 0.42);

      const pot = new THREE.Mesh(
        new THREE.CylinderGeometry(0.26, 0.2, 0.42, 16),
        warmBronzeAlloyMat
      );
      pot.position.y = 0.21;
      pg.add(pot);

      const potRim = new THREE.Mesh(
        new THREE.TorusGeometry(0.26, 0.025, 8, 20),
        anodizedGoldMat
      );
      potRim.rotation.x = Math.PI / 2;
      potRim.position.y = 0.42;
      pg.add(potRim);

      [
        { x: 0, y: 0.68, z: 0, r: 0.28, mat: foliageLushMat },
        { x: -0.18, y: 0.58, z: 0.12, r: 0.22, mat: foliageBrightMat },
        { x: 0.18, y: 0.62, z: -0.1, r: 0.23, mat: foliageBrightMat },
        { x: 0.08, y: 0.84, z: 0.08, r: 0.2, mat: foliageLushMat },
        { x: -0.12, y: 0.8, z: -0.12, r: 0.21, mat: foliageBrightMat },
      ].forEach((lf) => {
        const leaf = new THREE.Mesh(new THREE.SphereGeometry(lf.r, 12, 10), lf.mat);
        leaf.scale.set(1.15, 0.85, 1.15);
        leaf.position.set(lf.x, lf.y, lf.z);
        pg.add(leaf);
      });

      return pg;
    };

    // Helper: Build Realistic Executive Swivel Chair (Casters flush at local y = 0, seat top at y = 0.48)
    const chairSeatGeo = createRoundedBoxExtrudeGeometry(0.68, 0.64, 0.11, 0.045);
    const chairBackGeo = createRoundedBoxExtrudeGeometry(0.64, 0.72, 0.11, 0.055);
    const buildExecutiveSwivelChair = (scale = 1.0): THREE.Group => {
      const cg = new THREE.Group();
      cg.scale.setScalar(scale);

      addContactShadow(cg, 0, 0.005, 0, 0.46, 0.46);

      for (let i = 0; i < 5; i++) {
        const angle = (i * Math.PI * 2) / 5;
        const leg = new THREE.Mesh(
          new THREE.CylinderGeometry(0.022, 0.022, 0.36, 8),
          polishedChromeMat
        );
        leg.rotation.z = Math.PI / 2;
        leg.rotation.y = angle;
        leg.position.set(Math.cos(angle) * 0.18, 0.06, Math.sin(angle) * 0.18);
        cg.add(leg);

        const caster = new THREE.Mesh(
          new THREE.CylinderGeometry(0.032, 0.032, 0.03, 10),
          darkGunmetalMat
        );
        caster.rotation.z = Math.PI / 2;
        caster.position.set(Math.cos(angle) * 0.34, 0.032, Math.sin(angle) * 0.34);
        cg.add(caster);
      }

      const piston = new THREE.Mesh(
        new THREE.CylinderGeometry(0.042, 0.052, 0.38, 12),
        polishedChromeMat
      );
      piston.position.y = 0.23;
      cg.add(piston);

      const seat = new THREE.Mesh(chairSeatGeo, crimsonAnodizedAlloyMat);
      seat.rotation.x = Math.PI / 2;
      seat.position.y = 0.43;
      cg.add(seat);

      const backrest = new THREE.Mesh(chairBackGeo, crimsonAnodizedAlloyMat);
      backrest.position.set(0, 0.82, -0.27);
      backrest.rotation.x = -0.08;
      cg.add(backrest);

      const spine = new THREE.Mesh(
        new THREE.BoxGeometry(0.11, 0.52, 0.045),
        polishedChromeMat
      );
      spine.position.set(0, 0.66, -0.34);
      cg.add(spine);

      [-0.35, 0.35].forEach((ax) => {
        const post = new THREE.Mesh(
          new THREE.CylinderGeometry(0.024, 0.024, 0.22, 8),
          polishedChromeMat
        );
        post.position.set(ax, 0.55, -0.05);
        cg.add(post);

        const pad = new THREE.Mesh(
          new THREE.BoxGeometry(0.08, 0.038, 0.34),
          darkGunmetalMat
        );
        pad.position.set(ax, 0.67, -0.04);
        cg.add(pad);
      });

      return cg;
    };

    // Helper: Build Industrial Metallic Workstation Desk with 4 Chrome Legs (Bottom at local y = 0, Top at local y = 0.72)
    const buildWorkstationDesk = (w: number, d: number): THREE.Group => {
      const dg = new THREE.Group();
      addContactShadow(dg, 0, 0.005, 0, w * 0.54, d * 0.54);

      const topThickness = 0.09;
      const topGeo = createRoundedBoxExtrudeGeometry(w, d, topThickness, 0.04);
      const topMesh = new THREE.Mesh(topGeo, warmBronzeAlloyMat);
      topMesh.rotation.x = Math.PI / 2;
      topMesh.position.y = 0.72 - topThickness / 2;
      dg.add(topMesh);

      // Brushed chrome edge trim band
      const trimGeo = createRoundedBoxExtrudeGeometry(w + 0.03, d + 0.03, 0.028, 0.04);
      const trimMesh = new THREE.Mesh(trimGeo, polishedChromeMat);
      trimMesh.rotation.x = Math.PI / 2;
      trimMesh.position.y = 0.72 - topThickness / 2;
      dg.add(trimMesh);

      // 4 tubular steel legs with gunmetal leveling feet grounded at local y = 0
      const legH = 0.64;
      const insetX = w / 2 - 0.22;
      const insetZ = d / 2 - 0.18;
      [
        [-insetX, -insetZ],
        [insetX, -insetZ],
        [-insetX, insetZ],
        [insetX, insetZ],
      ].forEach(([lx, lz]) => {
        const leg = new THREE.Mesh(
          new THREE.CylinderGeometry(0.045, 0.04, legH, 12),
          brushedTitaniumMat
        );
        leg.position.set(lx, legH / 2 + 0.03, lz);
        dg.add(leg);

        const footPad = new THREE.Mesh(
          new THREE.CylinderGeometry(0.065, 0.07, 0.03, 12),
          darkGunmetalMat
        );
        footPad.position.set(lx, 0.015, lz);
        dg.add(footPad);
      });

      // Modesty front dark gunmetal baffle panel
      const baffle = new THREE.Mesh(
        new THREE.BoxGeometry(w - 0.55, 0.36, 0.03),
        darkGunmetalMat
      );
      baffle.position.set(0, 0.44, -insetZ + 0.05);
      dg.add(baffle);

      return dg;
    };

    // Helper: Build Realistic Studio Display Monitor (Base grounded at local y = 0)
    const buildStudioMonitor = (
      screenTex: THREE.CanvasTexture,
      w = 2.0,
      h = 1.25
    ): THREE.Group => {
      const mg = new THREE.Group();

      const foot = new THREE.Mesh(
        new THREE.BoxGeometry(0.55, 0.03, 0.4),
        polishedChromeMat
      );
      foot.position.y = 0.015;
      mg.add(foot);

      const neck = new THREE.Mesh(
        new THREE.BoxGeometry(0.18, 0.44, 0.045),
        polishedChromeMat
      );
      neck.position.set(0, 0.22, -0.08);
      neck.rotation.x = -0.12;
      mg.add(neck);

      const chassis = new THREE.Mesh(
        new THREE.BoxGeometry(w + 0.14, h + 0.14, 0.07),
        brushedTitaniumMat
      );
      chassis.position.set(0, 0.35 + h / 2, 0);
      mg.add(chassis);

      const bezel = new THREE.Mesh(
        new THREE.BoxGeometry(w + 0.05, h + 0.05, 0.025),
        darkGunmetalMat
      );
      bezel.position.set(0, 0.35 + h / 2, 0.036);
      mg.add(bezel);

      const screenMat = new THREE.MeshBasicMaterial({ map: screenTex });
      const screen = new THREE.Mesh(new THREE.PlaneGeometry(w, h), screenMat);
      screen.position.set(0, 0.35 + h / 2, 0.052);
      mg.add(screen);

      const kb = new THREE.Mesh(
        new THREE.BoxGeometry(0.66, 0.024, 0.24),
        polishedChromeMat
      );
      kb.position.set(-0.08, 0.012, 0.38);
      mg.add(kb);

      const mouse = new THREE.Mesh(
        new THREE.SphereGeometry(0.06, 12, 8),
        polishedChromeMat
      );
      mouse.scale.set(0.8, 0.4, 1.3);
      mouse.position.set(0.4, 0.015, 0.38);
      mg.add(mouse);

      return mg;
    };

    // Helper: Build Metallic BIS Laptop with Live Glowing Inner LCD Screen & Keyboard (Bottom grounded at local y = 0)
    const laptopLcdMat = new THREE.MeshBasicMaterial({ map: laptopScreenTex });
    const buildMetallicLaptop = (): THREE.Group => {
      const lg = new THREE.Group();
      const base = new THREE.Mesh(
        new THREE.BoxGeometry(0.62, 0.028, 0.42),
        brushedTitaniumMat
      );
      base.position.y = 0.014;
      lg.add(base);

      const kbDeck = new THREE.Mesh(
        new THREE.BoxGeometry(0.54, 0.008, 0.22),
        darkGunmetalMat
      );
      kbDeck.position.set(0, 0.03, -0.02);
      lg.add(kbDeck);

      const trackpad = new THREE.Mesh(
        new THREE.BoxGeometry(0.18, 0.006, 0.09),
        polishedChromeMat
      );
      trackpad.position.set(0, 0.03, 0.14);
      lg.add(trackpad);

      const lid = new THREE.Mesh(
        new THREE.BoxGeometry(0.62, 0.4, 0.024),
        darkGunmetalMat
      );
      lid.position.set(0, 0.21, -0.19);
      lid.rotation.x = -0.22;
      lg.add(lid);

      // Glowing live inner LCD screen facing +Z (toward operator)
      const innerScreen = new THREE.Mesh(
        new THREE.PlaneGeometry(0.56, 0.34),
        laptopLcdMat
      );
      innerScreen.position.set(0, 0, 0.014);
      lid.add(innerScreen);

      // Outer BIS badge facing -Z (away from operator)
      const logo = new THREE.Mesh(
        new THREE.PlaneGeometry(0.28, 0.14),
        new THREE.MeshBasicMaterial({ map: bisBadgeTex })
      );
      logo.position.set(0, 0, -0.014);
      logo.rotation.y = Math.PI;
      lid.add(logo);

      return lg;
    };

    // 5A. Spacious CNC-Machined Brushed Bronze-Titanium Floor (34m x 24m, top surface at exact y = 0.00)
    const baseFloorGeo = new THREE.BoxGeometry(34, 0.45, 24);
    const baseFloorMat = new THREE.MeshStandardMaterial({
      map: floorTileTex,
      color: 0xffffff,
      bumpMap: floorBumpTex,
      bumpScale: 0.014,
      roughnessMap: floorBumpTex,
      metalness: 0.74,
      roughness: 0.28,
      envMapIntensity: 1.45,
    });
    const baseFloor = new THREE.Mesh(baseFloorGeo, baseFloorMat);
    baseFloor.position.y = -0.225;
    baseFloor.receiveShadow = !isSoftwareGl;
    baseFloor.userData = { isWalkableFloor: true };
    officeGroup.add(baseFloor);

    // 5B. Back Architectural Wall with Crimson Anodized Slats + BIS TEXTILE AI Sign + Lush Greenery
    const backWallGroup = new THREE.Group();
    backWallGroup.position.set(0, 2.9, -10.2);
    officeGroup.add(backWallGroup);

    const centerWall = new THREE.Mesh(
      new THREE.BoxGeometry(10.5, 6.0, 0.4),
      new THREE.MeshStandardMaterial({
        color: 0xd8c8b8,
        metalness: 0.48,
        roughness: 0.34,
      })
    );
    backWallGroup.add(centerWall);

    const signBoard = new THREE.Mesh(
      new THREE.PlaneGeometry(6.6, 2.0),
      new THREE.MeshBasicMaterial({ map: wallLogoTex })
    );
    signBoard.position.set(0, 0.35, 0.22);
    backWallGroup.add(signBoard);

    const crimsonSlatMat = new THREE.MeshStandardMaterial({
      color: 0xb91c1c,
      metalness: 0.76,
      roughness: 0.24,
    });
    [-8.6, 8.6].forEach((sideX) => {
      const backing = new THREE.Mesh(
        new THREE.BoxGeometry(6.4, 6.0, 0.32),
        darkGunmetalMat
      );
      backing.position.set(sideX, 0, 0);
      backWallGroup.add(backing);

      for (let s = -6; s <= 6; s++) {
        const slat = new THREE.Mesh(
          new THREE.BoxGeometry(0.24, 5.9, 0.42),
          crimsonSlatMat
        );
        slat.position.set(sideX + s * 0.46, 0, 0.06);
        backWallGroup.add(slat);
      }
    });

    [
      { x: -3.8, z: -8.9, s: 1.35 },
      { x: 3.8, z: -8.9, s: 1.35 },
      { x: -12.2, z: -6.2, s: 1.45 },
      { x: 12.2, z: -6.2, s: 1.45 },
    ].forEach((pl) => {
      const plant = buildPottedPlant(pl.s);
      plant.position.set(pl.x, 0, pl.z);
      officeGroup.add(plant);
    });

    // 5C. Grounded Machined Brass-Titanium Floor Inlay Ring Around Central Conference Area
    const holoCeilingGroup = new THREE.Group();
    holoCeilingGroup.position.set(0, 0.012, -0.2);
    officeGroup.add(holoCeilingGroup);

    const outerHoloRing = new THREE.Mesh(
      new THREE.TorusGeometry(4.65, 0.032, 10, 64),
      anodizedGoldMat
    );
    outerHoloRing.rotation.x = Math.PI / 2;
    outerHoloRing.scale.set(1.16, 0.82, 1);
    holoCeilingGroup.add(outerHoloRing);

    const innerHoloRing = new THREE.Mesh(
      new THREE.TorusGeometry(4.35, 0.024, 10, 48),
      polishedChromeMat
    );
    innerHoloRing.rotation.x = Math.PI / 2;
    innerHoloRing.scale.set(1.16, 0.82, 1);
    holoCeilingGroup.add(innerHoloRing);

    // 5D. CENTRAL OVAL CONFERENCE TABLE ("Quy trình phiên 03026A") at (0, -0.2)
    // Uses CONFERENCE_TABLE_SPEC & getConferenceTableSeats() so chairs and seated robots are strictly outside the table rim!
    const { centerX: confCx, centerZ: confCz, baseRadius: confR, scaleX: confSx, scaleZ: confSz } =
      CONFERENCE_TABLE_SPEC;
    addContactShadow(officeGroup, confCx, 0.005, confCz, 5.4, 3.9);

    // Central Rug: height 0.024 centered at y = 0.012 so top is at exact y = 0.024
    const centralRug = new THREE.Mesh(
      new THREE.CylinderGeometry(4.35, 4.4, 0.024, 64),
      new THREE.MeshStandardMaterial({
        map: wovenRugTex,
        color: 0xffffff,
        roughness: 0.78,
        metalness: 0.1,
      })
    );
    centralRug.scale.set(1.2, 1, 0.84);
    centralRug.position.set(confCx, 0.012, confCz);
    officeGroup.add(centralRug);

    [-1.22, 1.22].forEach((px) => {
      addContactShadow(officeGroup, px, 0.028, confCz, 0.92, 0.78);
      const ped = new THREE.Mesh(
        new THREE.CylinderGeometry(0.48, 0.68, 0.72, 24),
        brushedTitaniumMat
      );
      ped.position.set(px, 0.024 + 0.36, confCz);
      officeGroup.add(ped);

      const pedGoldRing = new THREE.Mesh(
        new THREE.TorusGeometry(0.67, 0.026, 10, 28),
        anodizedGoldMat
      );
      pedGoldRing.rotation.x = Math.PI / 2;
      pedGoldRing.position.set(px, 0.024 + 0.026, confCz);
      officeGroup.add(pedGoldRing);
    });

    const tableTopRim = new THREE.Mesh(
      new THREE.CylinderGeometry(confR - 0.04, confR, 0.14, 64),
      warmBronzeAlloyMat
    );
    tableTopRim.scale.set(confSx, 1, confSz);
    tableTopRim.position.set(confCx, 0.78, confCz);
    officeGroup.add(tableTopRim);

    const tableGoldLip = new THREE.Mesh(
      new THREE.TorusGeometry(confR - 0.01, 0.028, 12, 64),
      anodizedGoldMat
    );
    tableGoldLip.rotation.x = Math.PI / 2;
    tableGoldLip.scale.set(confSx, confSz, 1);
    tableGoldLip.position.set(confCx, 0.83, confCz);
    officeGroup.add(tableGoldLip);

    const tableGraphicPlane = new THREE.Mesh(
      new THREE.CircleGeometry(confR - 0.14, 64),
      new THREE.MeshBasicMaterial({
        map: conferenceTableTex,
        polygonOffset: true,
        polygonOffsetFactor: -1,
        polygonOffsetUnits: -1,
      })
    );
    tableGraphicPlane.rotation.x = -Math.PI / 2;
    tableGraphicPlane.scale.set(confSx, confSz, 1);
    tableGraphicPlane.position.set(confCx, 0.855, confCz);
    officeGroup.add(tableGraphicPlane);

    // 5 Executive Swivel Chairs & Table Laptops computed from true ellipse outward normals (0.58m outside rim)
    const conferenceSeats = getConferenceTableSeats(CONFERENCE_TABLE_SPEC, 0.58);
    conferenceSeats.forEach((seat) => {
      const chair = buildExecutiveSwivelChair(seat.chairScale);
      chair.position.set(seat.chairX, 0.024, seat.chairZ);
      chair.rotation.y = seat.chairRotY;
      officeGroup.add(chair);

      if (seat.id === 'head-commander' || seat.id === 'seat-nw' || seat.id === 'seat-ne') {
        const seatLaptop = buildMetallicLaptop();
        seatLaptop.scale.setScalar(seat.id === 'head-commander' ? 0.96 : 0.82);
        seatLaptop.position.set(seat.laptopX, 0.855, seat.laptopZ);
        seatLaptop.rotation.y = seat.laptopRotY;
        officeGroup.add(seatLaptop);
      }
    });

    const coffeeCup = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.065, 0.16, 14),
      darkGunmetalMat
    );
    coffeeCup.position.set(0.62, 0.855 + 0.08, -1.48);
    officeGroup.add(coffeeCup);

    [
      { y: 0.88, color: 0xe7dfd5 },
      { y: 0.925, color: 0xb91c1c },
      { y: 0.97, color: 0xd9382c },
    ].forEach((sw) => {
      const layer = new THREE.Mesh(
        new THREE.BoxGeometry(0.7, 0.042, 0.46),
        new THREE.MeshStandardMaterial({ color: sw.color, roughness: 0.5 })
      );
      layer.position.set(0, sw.y, 1.08);
      officeGroup.add(layer);
    });

    // 5E. 5 SURROUNDING ARCHITECTURAL METALLIC DEPARTMENT PLATFORMS (Top surface strictly at y = 0.16)
    const PLATFORM_TOP_Y = 0.16;
    const platformBaseMat = new THREE.MeshStandardMaterial({
      color: 0x8f7968,
      metalness: 0.68,
      roughness: 0.28,
      bumpMap: robotMetalBumpTex,
      bumpScale: 0.008,
    });

    const buildPlatformSlab = (
      x: number,
      z: number,
      w: number,
      d: number,
      withBackPartition: 'left' | 'right' | 'none' = 'none'
    ) => {
      const pg = new THREE.Group();
      pg.position.set(x, 0, z);

      addContactShadow(pg, 0, 0.005, 0, w * 0.58, d * 0.58);

      // Solid gunmetal plinth base resting flush at y = 0.00..0.04
      const plinthGeo = createRoundedBoxExtrudeGeometry(w + 0.12, d + 0.12, 0.04, 0.32);
      const plinth = new THREE.Mesh(plinthGeo, darkGunmetalMat);
      plinth.rotation.x = Math.PI / 2;
      plinth.position.y = 0.02;
      pg.add(plinth);

      // Anodized gold chamfer rim at y = 0.04..0.06
      const goldTrimGeo = createRoundedBoxExtrudeGeometry(w + 0.06, d + 0.06, 0.024, 0.3);
      const goldTrim = new THREE.Mesh(goldTrimGeo, anodizedGoldMat);
      goldTrim.rotation.x = Math.PI / 2;
      goldTrim.position.y = 0.045;
      pg.add(goldTrim);

      // Main brushed metallic platform slab from y = 0.04 to exact top y = 0.16 (thickness 0.12, centered at 0.10)
      const slabGeo = createRoundedBoxExtrudeGeometry(w, d, 0.12, 0.28);
      const slab = new THREE.Mesh(slabGeo, platformBaseMat);
      slab.rotation.x = Math.PI / 2;
      slab.position.y = 0.1;
      slab.receiveShadow = !isSoftwareGl;
      pg.add(slab);

      if (withBackPartition !== 'none') {
        const backWall = new THREE.Mesh(
          createRoundedBoxExtrudeGeometry(w - 0.28, 1.75, 0.16, 0.1),
          partitionWallMat
        );
        backWall.position.set(0, PLATFORM_TOP_Y + 0.875, -d / 2 + 0.16);
        pg.add(backWall);

        const sideWing = new THREE.Mesh(
          createRoundedBoxExtrudeGeometry(0.16, 1.55, d * 0.56, 0.08),
          partitionWallMat
        );
        sideWing.position.set(
          withBackPartition === 'left' ? -w / 2 + 0.16 : w / 2 - 0.16,
          PLATFORM_TOP_Y + 0.775,
          -d * 0.18
        );
        pg.add(sideWing);
      }

      officeGroup.add(pg);
      return pg;
    };

    // 1. TECHNICAL PLATFORM (Top-Left: x = -8.8, z = -5.55, w = 5.2, d = 2.6)
    // Desk placed at z = 0.22; monitor on center-right (x = 0.48) and seated operator robot on left (x = -1.28) so neither blocks the other!
    const techPlatform = buildPlatformSlab(-8.8, -5.55, 5.2, 2.6, 'left');
    const techDesk = buildWorkstationDesk(3.8, 0.96);
    techDesk.position.set(0.1, PLATFORM_TOP_Y, 0.22);
    techPlatform.add(techDesk);

    const techDESK_TOP_Y = PLATFORM_TOP_Y + 0.72;
    const techMonitor = buildStudioMonitor(techScreenTex, 2.05, 1.24);
    techMonitor.position.set(0.48, techDESK_TOP_Y, 0.22);
    techMonitor.rotation.y = 0.12;
    techPlatform.add(techMonitor);

    const techChair = buildExecutiveSwivelChair(0.9);
    techChair.position.set(-1.18, PLATFORM_TOP_Y, -0.56);
    techChair.rotation.y = 0.12;
    techPlatform.add(techChair);

    const techSideChair = buildExecutiveSwivelChair(0.86);
    techSideChair.position.set(1.75, PLATFORM_TOP_Y, -0.54);
    techSideChair.rotation.y = -0.18;
    techPlatform.add(techSideChair);

    [-1.72, -1.52, -1.32].forEach((bx, idx) => {
      const binder = new THREE.Mesh(
        new THREE.BoxGeometry(0.16, 0.48, 0.34),
        idx === 1 ? darkGunmetalMat : crimsonAnodizedAlloyMat
      );
      binder.position.set(bx, techDESK_TOP_Y + 0.24, 0.16);
      techPlatform.add(binder);
    });

    const specStack = new THREE.Mesh(
      new THREE.BoxGeometry(0.58, 0.14, 0.42),
      new THREE.MeshStandardMaterial({ color: 0xf5efe6, roughness: 0.4 })
    );
    specStack.position.set(-0.75, techDESK_TOP_Y + 0.07, 0.28);
    techPlatform.add(specStack);

    // 2. MARKETING PLATFORM (Top-Right: x = 8.8, z = -5.55, w = 5.2, d = 2.6)
    // Desk placed at z = 0.22; monitor on center-right (x = 0.42) and seated operator robot behind laptop on left (x = -1.22)!
    const mktPlatform = buildPlatformSlab(8.8, -5.55, 5.2, 2.6, 'right');
    const mktDesk = buildWorkstationDesk(3.8, 0.96);
    mktDesk.position.set(-0.15, PLATFORM_TOP_Y, 0.22);
    mktPlatform.add(mktDesk);

    const mktDESK_TOP_Y = PLATFORM_TOP_Y + 0.72;
    const mktMonitor = buildStudioMonitor(mktScreenTex, 2.05, 1.24);
    mktMonitor.position.set(0.42, mktDESK_TOP_Y, 0.22);
    mktMonitor.rotation.y = -0.12;
    mktPlatform.add(mktMonitor);

    const mktLaptop = buildMetallicLaptop();
    mktLaptop.position.set(-1.22, mktDESK_TOP_Y, 0.24);
    mktLaptop.rotation.y = -0.08;
    mktPlatform.add(mktLaptop);

    const mktChair = buildExecutiveSwivelChair(0.9);
    mktChair.position.set(-1.22, PLATFORM_TOP_Y, -0.56);
    mktChair.rotation.y = 0;
    mktPlatform.add(mktChair);

    const mktSideChair = buildExecutiveSwivelChair(0.86);
    mktSideChair.position.set(1.45, PLATFORM_TOP_Y, -0.54);
    mktSideChair.rotation.y = -0.18;
    mktPlatform.add(mktSideChair);

    const mannequinStand = new THREE.Mesh(
      new THREE.CylinderGeometry(0.04, 0.24, 1.35, 14),
      anodizedGoldMat
    );
    mannequinStand.position.set(2.15, PLATFORM_TOP_Y + 0.675, -0.55);
    mktPlatform.add(mannequinStand);

    const mannequinTorso = new THREE.Mesh(
      new THREE.CylinderGeometry(0.26, 0.2, 1.05, 18),
      crimsonAnodizedAlloyMat
    );
    mannequinTorso.position.set(2.15, PLATFORM_TOP_Y + 1.48, -0.55);
    mktPlatform.add(mannequinTorso);

    const mannequinNeck = new THREE.Mesh(
      new THREE.CylinderGeometry(0.085, 0.1, 0.2, 12),
      brushedTitaniumMat
    );
    mannequinNeck.position.set(2.15, PLATFORM_TOP_Y + 2.08, -0.55);
    mktPlatform.add(mannequinNeck);

    // 3. KNOWLEDGE PLATFORM (Mid-Left: x = -10.35, z = 0.8, w = 3.4, d = 3.7)
    // Bookcase at x = -1.08, Desk at x = +0.62, Operator Chair in between at x = -0.26 facing +X!
    const knowPlatform = buildPlatformSlab(-10.35, 0.8, 3.4, 3.7, 'left');
    const bookcase = new THREE.Mesh(
      new THREE.BoxGeometry(0.84, 2.4, 3.1),
      warmBronzeAlloyMat
    );
    bookcase.position.set(-1.08, PLATFORM_TOP_Y + 1.2, 0);
    knowPlatform.add(bookcase);

    [-1.05, -0.35, 0.35, 1.05].forEach((bz, idx) => {
      const bookRow = new THREE.Mesh(
        new THREE.BoxGeometry(0.42, 0.38, 0.52),
        idx % 2 === 0 ? crimsonAnodizedAlloyMat : anodizedGoldMat
      );
      bookRow.position.set(-0.78, PLATFORM_TOP_Y + 1.55, bz);
      knowPlatform.add(bookRow);

      const lowerRow = new THREE.Mesh(
        new THREE.BoxGeometry(0.42, 0.36, 0.5),
        idx % 2 === 1 ? crimsonAnodizedAlloyMat : brushedTitaniumMat
      );
      lowerRow.position.set(-0.78, PLATFORM_TOP_Y + 0.92, bz);
      knowPlatform.add(lowerRow);
    });

    const knowDesk = buildWorkstationDesk(1.12, 2.05);
    knowDesk.position.set(0.62, PLATFORM_TOP_Y, 0.12);
    knowPlatform.add(knowDesk);

    const knowChair = buildExecutiveSwivelChair(0.88);
    knowChair.position.set(-0.26, PLATFORM_TOP_Y, 0.12);
    knowChair.rotation.y = Math.PI / 2;
    knowPlatform.add(knowChair);

    const knowDESK_TOP_Y = PLATFORM_TOP_Y + 0.72;
    const openBook = new THREE.Mesh(
      new THREE.BoxGeometry(0.46, 0.12, 0.58),
      crimsonAnodizedAlloyMat
    );
    openBook.position.set(0.58, knowDESK_TOP_Y + 0.06, -0.22);
    openBook.rotation.z = -0.12;
    knowPlatform.add(openBook);

    const knowLaptop = buildMetallicLaptop();
    knowLaptop.scale.setScalar(0.82);
    knowLaptop.position.set(0.62, knowDESK_TOP_Y, 0.52);
    knowLaptop.rotation.y = 0.45;
    knowPlatform.add(knowLaptop);

    // 4. IMAGE STUDIO PLATFORM (Mid-Right: x = 10.35, z = 0.8, w = 3.4, d = 3.7)
    const studioPlatform = buildPlatformSlab(10.35, 0.8, 3.4, 3.7, 'right');

    const cycloramaBooth = new THREE.Mesh(
      new THREE.BoxGeometry(1.35, 2.35, 2.05),
      new THREE.MeshStandardMaterial({
        color: 0xfafaf9,
        emissive: 0xfffbeb,
        emissiveIntensity: 0.18,
        metalness: 0.15,
        roughness: 0.2,
      })
    );
    cycloramaBooth.position.set(0.78, PLATFORM_TOP_Y + 1.175, -0.18);
    studioPlatform.add(cycloramaBooth);

    const specimenPedestal = new THREE.Mesh(
      new THREE.CylinderGeometry(0.46, 0.5, 0.22, 24),
      polishedChromeMat
    );
    specimenPedestal.position.set(0.68, PLATFORM_TOP_Y + 0.11, -0.18);
    studioPlatform.add(specimenPedestal);

    const fabricSwatch = new THREE.Mesh(
      new THREE.CylinderGeometry(0.25, 0.42, 0.98, 24),
      crimsonAnodizedAlloyMat
    );
    fabricSwatch.position.set(0.68, PLATFORM_TOP_Y + 0.22 + 0.49, -0.18);
    studioPlatform.add(fabricSwatch);

    const softboxStand = new THREE.Mesh(
      new THREE.CylinderGeometry(0.035, 0.045, 1.75, 10),
      darkGunmetalMat
    );
    softboxStand.position.set(-0.22, PLATFORM_TOP_Y + 0.875, -1.05);
    studioPlatform.add(softboxStand);

    const softboxHead = new THREE.Mesh(
      new THREE.BoxGeometry(0.44, 0.76, 0.76),
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        emissive: 0xfffbeb,
        emissiveIntensity: 1.35,
      })
    );
    softboxHead.position.set(-0.16, PLATFORM_TOP_Y + 1.78, -1.02);
    softboxHead.rotation.y = -0.5;
    softboxHead.rotation.z = -0.18;
    studioPlatform.add(softboxHead);

    const tripodPole = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.05, 1.0, 10),
      darkGunmetalMat
    );
    tripodPole.position.set(-0.35, PLATFORM_TOP_Y + 0.5, 0.55);
    studioPlatform.add(tripodPole);

    const cameraBody = new THREE.Mesh(
      new THREE.BoxGeometry(0.34, 0.26, 0.26),
      darkGunmetalMat
    );
    cameraBody.position.set(-0.35, PLATFORM_TOP_Y + 1.08, 0.55);
    studioPlatform.add(cameraBody);

    const cameraLens = new THREE.Mesh(
      new THREE.CylinderGeometry(0.085, 0.085, 0.26, 16),
      polishedChromeMat
    );
    cameraLens.rotation.z = Math.PI / 2;
    cameraLens.position.set(-0.14, PLATFORM_TOP_Y + 1.08, 0.55);
    studioPlatform.add(cameraLens);

    // Tethered Studio Preview Laptop on a compact stand
    const studioTetherStand = new THREE.Mesh(
      new THREE.CylinderGeometry(0.28, 0.32, 0.62, 16),
      brushedTitaniumMat
    );
    studioTetherStand.position.set(-0.95, PLATFORM_TOP_Y + 0.31, 0.98);
    studioPlatform.add(studioTetherStand);

    const studioLaptop = buildMetallicLaptop();
    studioLaptop.scale.setScalar(0.78);
    studioLaptop.position.set(-0.95, PLATFORM_TOP_Y + 0.62, 0.98);
    studioLaptop.rotation.y = -0.35;
    studioPlatform.add(studioLaptop);

    // 5. OPERATIONS PLATFORM (Bottom-Center: x = 0, z = 6.18, w = 7.8, d = 2.2)
    // Desk at z = 0.24 (spans -0.23..+0.71) with 2 operator chairs cleanly behind the flanks at z = -0.56!
    const opsPlatform = buildPlatformSlab(0, 6.18, 7.8, 2.2, 'none');
    const opsDesk = buildWorkstationDesk(5.8, 0.94);
    opsDesk.position.set(0, PLATFORM_TOP_Y, 0.24);
    opsPlatform.add(opsDesk);

    const opsLeftChair = buildExecutiveSwivelChair(0.88);
    opsLeftChair.position.set(-2.25, PLATFORM_TOP_Y, -0.56);
    opsLeftChair.rotation.y = 0.16;
    opsPlatform.add(opsLeftChair);

    const opsRightChair = buildExecutiveSwivelChair(0.88);
    opsRightChair.position.set(2.25, PLATFORM_TOP_Y, -0.56);
    opsRightChair.rotation.y = -0.16;
    opsPlatform.add(opsRightChair);

    const opsDESK_TOP_Y = PLATFORM_TOP_Y + 0.72;
    const opsLeftMonitor = buildStudioMonitor(opsCheckTex, 2.04, 1.22);
    opsLeftMonitor.position.set(-1.3, opsDESK_TOP_Y, 0.26);
    opsPlatform.add(opsLeftMonitor);

    const opsRightMonitor = buildStudioMonitor(opsStoreTex, 2.04, 1.22);
    opsRightMonitor.position.set(1.3, opsDESK_TOP_Y, 0.26);
    opsPlatform.add(opsRightMonitor);

    const opsClipboard = new THREE.Mesh(
      new THREE.BoxGeometry(0.44, 0.04, 0.54),
      new THREE.MeshStandardMaterial({ color: 0xf7f3ee, roughness: 0.3 })
    );
    opsClipboard.position.set(-2.45, opsDESK_TOP_Y + 0.02, 0.2);
    opsPlatform.add(opsClipboard);

    const opsRightLaptop = buildMetallicLaptop();
    opsRightLaptop.scale.setScalar(0.86);
    opsRightLaptop.position.set(2.45, opsDESK_TOP_Y, 0.2);
    opsRightLaptop.rotation.y = -0.22;
    opsPlatform.add(opsRightLaptop);

    const opsLeftPlant = buildPottedPlant(0.88);
    opsLeftPlant.position.set(-3.45, PLATFORM_TOP_Y, 0.15);
    opsPlatform.add(opsLeftPlant);

    const opsRightPlant = buildPottedPlant(0.88);
    opsRightPlant.position.set(3.45, PLATFORM_TOP_Y, 0.15);
    opsPlatform.add(opsRightPlant);

    // 5F. Inset Brass Guide Rails on the Floor & Foreground Textile Rolls
    const pathwayMat = anodizedGoldMat;
    const arrowGeo = new THREE.ConeGeometry(0.16, 0.32, 3);
    arrowGeo.rotateX(Math.PI / 2);
    [
      { x: -5.6, z: -2.6, w: 2.8, rot: -0.52 },
      { x: 5.6, z: -2.6, w: 2.8, rot: 0.52 },
      { x: -5.8, z: 0.6, w: 2.4, rot: 0.05 },
      { x: 5.8, z: 0.6, w: 2.4, rot: -0.05 },
      { x: -2.2, z: 3.45, w: 1.9, rot: 1.18 },
      { x: 2.2, z: 3.45, w: 1.9, rot: -1.18 },
    ].forEach((pw) => {
      const stripGroup = new THREE.Group();
      stripGroup.position.set(pw.x, 0.012, pw.z);
      stripGroup.rotation.y = pw.rot;

      const strip = new THREE.Mesh(
        new THREE.BoxGeometry(pw.w, 0.018, 0.075),
        pathwayMat
      );
      stripGroup.add(strip);

      const arrowTip = new THREE.Mesh(arrowGeo, pathwayMat);
      arrowTip.position.set(pw.x < 0 ? -pw.w * 0.45 : pw.w * 0.45, 0.008, 0);
      arrowTip.rotation.y = pw.x < 0 ? -Math.PI / 2 : Math.PI / 2;
      stripGroup.add(arrowTip);

      officeGroup.add(stripGroup);
    });

    // Foreground Textile Fabric Rolls grounded on a metallic pallet at y = 0
    const rollGeo = new THREE.CylinderGeometry(0.42, 0.42, 1.32, 24);
    [
      { x: -11.2, z: 5.7, color: 0xb91c1c },
      { x: -11.9, z: 6.3, color: 0xe7dfd5 },
      { x: -10.5, z: 6.4, color: 0x475569 },
      { x: 11.2, z: 5.7, color: 0xb91c1c },
      { x: 11.9, z: 6.3, color: 0xd97706 },
      { x: 10.5, z: 6.4, color: 0xe7dfd5 },
    ].forEach((r) => {
      addContactShadow(officeGroup, r.x, 0.005, r.z, 0.72, 0.55);
      const roll = new THREE.Mesh(
        rollGeo,
        new THREE.MeshStandardMaterial({
          color: r.color,
          roughness: 0.62,
          metalness: 0.1,
        })
      );
      roll.rotation.z = Math.PI / 2;
      roll.rotation.y = 0.35;
      roll.position.set(r.x, 0.42, r.z);
      officeGroup.add(roll);
    });

    // Walk Target Indicator Ring on the Floor
    const walkTargetRing = new THREE.Mesh(
      new THREE.RingGeometry(0.45, 0.68, 32),
      new THREE.MeshBasicMaterial({
        color: 0xfde68a,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0,
        polygonOffset: true,
        polygonOffsetFactor: -2,
        polygonOffsetUnits: -2,
      })
    );
    walkTargetRing.rotation.x = -Math.PI / 2;
    walkTargetRing.position.set(0, 0.03, -3.55);
    scene.add(walkTargetRing);

    // 6. Build Authentic CNC-Machined Metallic BIS Robots (With Articulated Joints & Strict Grounding!)
    const robotHeadGeo = createRoundedBoxExtrudeGeometry(1.04, 0.76, 0.78, 0.16);
    const robotVisorBezelGeo = createRoundedBoxExtrudeGeometry(0.88, 0.52, 0.08, 0.05);
    const robotVisorGeo = createRoundedBoxExtrudeGeometry(0.8, 0.44, 0.07, 0.04);
    const robotTorsoGeo = createRoundedBoxExtrudeGeometry(0.76, 0.64, 0.52, 0.12);
    const shoulderPauldronGeo = createRoundedBoxExtrudeGeometry(0.24, 0.24, 0.28, 0.05);
    const upperLimbGeo = new THREE.CylinderGeometry(0.095, 0.085, 0.22, 16);
    const lowerLimbGeo = new THREE.CylinderGeometry(0.09, 0.08, 0.2, 16);
    const jointSphereGeo = new THREE.SphereGeometry(0.095, 14, 12);
    const earCupGeo = new THREE.CylinderGeometry(0.2, 0.2, 0.15, 24);
    const eyeLensBarrelGeo = new THREE.CylinderGeometry(0.135, 0.135, 0.06, 20);
    const eyeOuterGeo = new THREE.SphereGeometry(0.105, 18, 14);
    const eyePupilGeo = new THREE.SphereGeometry(0.048, 12, 10);
    const hitboxGeo = new THREE.BoxGeometry(1.6, 2.5, 1.6);
    const hitboxMat = new THREE.MeshBasicMaterial({ visible: false });

    const robotMap = new Map<DepartmentId, RobotMeshParts>();
    const clickableHitboxes: THREE.Object3D[] = [];

    const initialActors = actorsRef.current;
    initialActors.forEach((actor) => {
      const root = new THREE.Group();
      const groundY = getFloorElevationAt(actor.pos.x, actor.pos.z);
      root.position.set(actor.pos.x, 0, actor.pos.z);

      addContactShadow(root, 0, groundY + 0.005, 0, 0.68, 0.68);

      const bodyGroup = new THREE.Group();
      bodyGroup.position.y = groundY;
      if (actor.id === 'overview') {
        bodyGroup.scale.setScalar(1.16);
      }
      root.add(bodyGroup);

      // Primary CNC-Machined Titanium-Alloy Armor Material (High Metalness + Brushed Bump + Clearcoat)
      const shellMat = new THREE.MeshPhysicalMaterial({
        color: 0xa2968a,
        metalness: 0.92,
        roughness: 0.22,
        bumpMap: robotMetalBumpTex,
        bumpScale: 0.016,
        roughnessMap: robotMetalBumpTex,
        clearcoat: 0.65,
        clearcoatRoughness: 0.08,
        anisotropy: 0.75,
        envMapIntensity: 1.42,
      });

      const deptAccentMat = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(actor.colorHex),
        metalness: 0.86,
        roughness: 0.22,
        clearcoat: 0.55,
        envMapIntensity: 1.9,
      });

      const visorGlassMat = new THREE.MeshPhysicalMaterial({
        color: 0x07090d,
        metalness: 0.25,
        roughness: 0.05,
        clearcoat: 1.0,
        clearcoatRoughness: 0.04,
        envMapIntensity: 2.2,
      });

      const eyeGlowColor = new THREE.Color(actor.eyeColorHex);
      const eyeGlowMat = new THREE.MeshStandardMaterial({
        color: eyeGlowColor,
        emissive: eyeGlowColor,
        emissiveIntensity: 3.4,
        roughness: 0.08,
      });
      const pupilSparkMat = new THREE.MeshBasicMaterial({ color: 0xffffff });

      // 1. Dark Gunmetal Ribbed Hydraulic Waist Spine (y = 0.42..0.56)
      const waistSpine = new THREE.Mesh(
        new THREE.CylinderGeometry(0.21, 0.24, 0.18, 18),
        darkGunmetalMat
      );
      waistSpine.position.y = 0.49;
      bodyGroup.add(waistSpine);

      const waistChromeBelt = new THREE.Mesh(
        new THREE.TorusGeometry(0.24, 0.025, 8, 24),
        polishedChromeMat
      );
      waistChromeBelt.rotation.x = Math.PI / 2;
      waistChromeBelt.position.y = 0.46;
      bodyGroup.add(waistChromeBelt);

      // 2. CNC Titanium Chest Cuirass (y = 0.54..1.18, centered at 0.84)
      const torso = new THREE.Mesh(robotTorsoGeo, shellMat);
      torso.position.y = 0.84;
      torso.castShadow = !isSoftwareGl;
      bodyGroup.add(torso);

      // Dual Chrome Hydraulic Torso Pistons on Left & Right Ribs
      [-0.31, 0.31].forEach((px) => {
        const piston = new THREE.Mesh(
          new THREE.CylinderGeometry(0.032, 0.032, 0.46, 10),
          polishedChromeMat
        );
        piston.position.set(px, 0.76, 0.14);
        bodyGroup.add(piston);
      });

      // Rear Titanium Jetpack / Cooling Manifold with Dark Gunmetal Louvers
      const backpack = new THREE.Mesh(
        createRoundedBoxExtrudeGeometry(0.5, 0.44, 0.18, 0.05),
        shellMat
      );
      backpack.position.set(0, 0.84, -0.31);
      bodyGroup.add(backpack);

      const backVent = new THREE.Mesh(
        new THREE.BoxGeometry(0.36, 0.26, 0.04),
        darkGunmetalMat
      );
      backVent.position.set(0, 0.84, -0.4);
      bodyGroup.add(backVent);

      // Machined Neck Hydraulic Column & Anodized Collar Ring
      const neckColumn = new THREE.Mesh(
        new THREE.CylinderGeometry(0.16, 0.19, 0.16, 16),
        darkGunmetalMat
      );
      neckColumn.position.y = 1.18;
      bodyGroup.add(neckColumn);

      const collarRing = new THREE.Mesh(
        new THREE.TorusGeometry(0.27, 0.04, 10, 24),
        deptAccentMat
      );
      collarRing.rotation.x = Math.PI / 2;
      collarRing.position.y = 1.15;
      bodyGroup.add(collarRing);

      // Illuminated Chest Reactor Core & Engraved BIS Metallic Plate
      const chestCoreRing = new THREE.Mesh(
        new THREE.TorusGeometry(0.085, 0.02, 8, 20),
        polishedChromeMat
      );
      chestCoreRing.position.set(0, 0.68, 0.27);
      bodyGroup.add(chestCoreRing);

      const chestCoreLight = new THREE.Mesh(
        new THREE.CircleGeometry(0.068, 16),
        eyeGlowMat
      );
      chestCoreLight.position.set(0, 0.68, 0.276);
      bodyGroup.add(chestCoreLight);

      const chestBadge = new THREE.Mesh(
        new THREE.PlaneGeometry(0.28, 0.14),
        new THREE.MeshBasicMaterial({ map: bisBadgeTex })
      );
      chestBadge.position.set(0, 0.92, 0.275);
      bodyGroup.add(chestBadge);

      // 3. Articulated CNC Metallic Head Group (centered at y = 1.56)
      const headGroup = new THREE.Group();
      headGroup.position.y = 1.56;
      bodyGroup.add(headGroup);

      const headMesh = new THREE.Mesh(robotHeadGeo, shellMat);
      headMesh.castShadow = !isSoftwareGl;
      headGroup.add(headMesh);

      // Top Crown Plate & 4 Chrome Hex Rivets
      const crownPlate = new THREE.Mesh(
        createRoundedBoxExtrudeGeometry(0.68, 0.06, 0.48, 0.02),
        brushedTitaniumMat
      );
      crownPlate.position.set(0, 0.38, 0);
      headGroup.add(crownPlate);

      [
        [-0.36, 0.28, 0.395],
        [0.36, 0.28, 0.395],
        [-0.36, -0.26, 0.395],
        [0.36, -0.26, 0.395],
      ].forEach(([rx, ry, rz]) => {
        const bolt = new THREE.Mesh(
          new THREE.CylinderGeometry(0.022, 0.022, 0.02, 6),
          polishedChromeMat
        );
        bolt.rotation.x = Math.PI / 2;
        bolt.position.set(rx, ry, rz);
        headGroup.add(bolt);
      });

      const foreheadPlate = new THREE.Mesh(
        new THREE.PlaneGeometry(0.36, 0.16),
        new THREE.MeshBasicMaterial({ map: bisBadgeTex })
      );
      foreheadPlate.position.set(0, 0.26, 0.402);
      headGroup.add(foreheadPlate);

      // Chrome Outer Visor Bezel + Recessed Optical Smoked Glass Visor
      const visorBezel = new THREE.Mesh(robotVisorBezelGeo, polishedChromeMat);
      visorBezel.position.set(0, -0.02, 0.372);
      headGroup.add(visorBezel);

      const visor = new THREE.Mesh(robotVisorGeo, visorGlassMat);
      visor.position.set(0, -0.02, 0.386);
      headGroup.add(visor);

      // Dual Optical LED Eyes with Precision Chrome Aperture Barrels
      [-0.2, 0.2].forEach((ex) => {
        const barrel = new THREE.Mesh(eyeLensBarrelGeo, polishedChromeMat);
        barrel.rotation.x = Math.PI / 2;
        barrel.position.set(ex, -0.015, 0.415);
        headGroup.add(barrel);
      });

      const leftEye = new THREE.Mesh(eyeOuterGeo, eyeGlowMat);
      leftEye.scale.set(1.0, 1.15, 0.42);
      leftEye.position.set(-0.2, -0.015, 0.438);
      const leftPupil = new THREE.Mesh(eyePupilGeo, pupilSparkMat);
      leftPupil.position.set(0.025, 0.025, 0.09);
      leftEye.add(leftPupil);
      headGroup.add(leftEye);

      const rightEye = new THREE.Mesh(eyeOuterGeo, eyeGlowMat);
      rightEye.scale.set(1.0, 1.15, 0.42);
      rightEye.position.set(0.2, -0.015, 0.438);
      const rightPupil = new THREE.Mesh(eyePupilGeo, pupilSparkMat);
      rightPupil.position.set(0.025, 0.025, 0.09);
      rightEye.add(rightPupil);
      headGroup.add(rightEye);

      // Acoustic Servo Ear-Pods with Chrome Cooling Rings & Telemetry Antenna
      [-0.54, 0.54].forEach((ex) => {
        const ear = new THREE.Mesh(earCupGeo, deptAccentMat);
        ear.rotation.z = Math.PI / 2;
        ear.position.set(ex, 0, 0);
        headGroup.add(ear);

        const earRing = new THREE.Mesh(
          new THREE.TorusGeometry(0.18, 0.025, 8, 20),
          polishedChromeMat
        );
        earRing.rotation.y = Math.PI / 2;
        earRing.position.set(ex + (ex > 0 ? 0.07 : -0.07), 0, 0);
        headGroup.add(earRing);
      });

      const antennaPole = new THREE.Mesh(
        new THREE.CylinderGeometry(0.012, 0.02, 0.22, 8),
        polishedChromeMat
      );
      antennaPole.position.set(0.46, 0.44, -0.08);
      headGroup.add(antennaPole);

      const antennaTip = new THREE.Mesh(
        new THREE.SphereGeometry(0.032, 10, 8),
        eyeGlowMat
      );
      antennaTip.position.set(0.46, 0.56, -0.08);
      headGroup.add(antennaTip);

      // 4. Articulated Mechanical Arms (Shoulder Pauldron -> Gunmetal Ball -> Upper Arm -> Chrome Elbow -> Forearm -> Gripper)
      const buildArmGroup = (sideX: number): THREE.Group => {
        const ag = new THREE.Group();
        ag.position.set(sideX, 0.98, 0);

        const pauldron = new THREE.Mesh(shoulderPauldronGeo, deptAccentMat);
        pauldron.position.set(sideX > 0 ? 0.04 : -0.04, 0.04, 0);
        ag.add(pauldron);

        const shoulderJoint = new THREE.Mesh(jointSphereGeo, darkGunmetalMat);
        ag.add(shoulderJoint);

        const upperArm = new THREE.Mesh(upperLimbGeo, shellMat);
        upperArm.position.y = -0.14;
        ag.add(upperArm);

        const elbowHinge = new THREE.Mesh(
          new THREE.CylinderGeometry(0.085, 0.085, 0.14, 12),
          polishedChromeMat
        );
        elbowHinge.rotation.z = Math.PI / 2;
        elbowHinge.position.y = -0.26;
        ag.add(elbowHinge);

        const forearm = new THREE.Mesh(lowerLimbGeo, shellMat);
        forearm.position.y = -0.37;
        ag.add(forearm);

        const wristCuff = new THREE.Mesh(
          new THREE.CylinderGeometry(0.088, 0.088, 0.05, 12),
          darkGunmetalMat
        );
        wristCuff.position.y = -0.47;
        ag.add(wristCuff);

        const gripperClaw = new THREE.Mesh(
          new THREE.TorusGeometry(0.075, 0.026, 8, 16, Math.PI * 1.35),
          polishedChromeMat
        );
        gripperClaw.rotation.z = Math.PI / 2;
        gripperClaw.position.y = -0.53;
        ag.add(gripperClaw);

        bodyGroup.add(ag);
        return ag;
      };

      const leftArm = buildArmGroup(-0.48);
      const rightArm = buildArmGroup(0.48);

      // 5. Articulated Legs & Hydraulic Magnetic-Clamp Boots (Sole bottom strictly at local y = 0.00!)
      // Hip pivot at y = 0.44 -> boot sole bottom at local y = -0.44 => world y = 0.00!
      const buildLegGroup = (sideX: number): THREE.Group => {
        const lg = new THREE.Group();
        lg.position.set(sideX, 0.44, 0);

        const hipServo = new THREE.Mesh(jointSphereGeo, darkGunmetalMat);
        lg.add(hipServo);

        const thigh = new THREE.Mesh(
          new THREE.CylinderGeometry(0.105, 0.095, 0.18, 16),
          shellMat
        );
        thigh.position.y = -0.11;
        lg.add(thigh);

        const kneeJoint = new THREE.Mesh(
          new THREE.CylinderGeometry(0.09, 0.09, 0.15, 12),
          polishedChromeMat
        );
        kneeJoint.rotation.z = Math.PI / 2;
        kneeJoint.position.y = -0.22;
        lg.add(kneeJoint);

        const shin = new THREE.Mesh(
          new THREE.CylinderGeometry(0.095, 0.088, 0.14, 16),
          shellMat
        );
        shin.position.y = -0.3;
        lg.add(shin);

        // Heavy metallic boot upper: height 0.09 centered at -0.375 (spans -0.33 to -0.42)
        const bootUpper = new THREE.Mesh(
          createRoundedBoxExtrudeGeometry(0.24, 0.09, 0.32, 0.025),
          shellMat
        );
        bootUpper.position.set(0, -0.375, 0.035);
        lg.add(bootUpper);

        const toeCap = new THREE.Mesh(
          new THREE.BoxGeometry(0.22, 0.055, 0.12),
          deptAccentMat
        );
        toeCap.position.set(0, -0.385, 0.145);
        lg.add(toeCap);

        // Dark gunmetal magnetic tread sole: height 0.04 centered at -0.42 (bottom strictly at -0.44 -> y = 0.00!)
        const bootSole = new THREE.Mesh(
          new THREE.BoxGeometry(0.25, 0.04, 0.34),
          darkGunmetalMat
        );
        bootSole.position.set(0, -0.42, 0.035);
        lg.add(bootSole);

        bodyGroup.add(lg);
        return lg;
      };

      const leftLeg = buildLegGroup(-0.2);
      const rightLeg = buildLegGroup(0.2);

      // Department-specific metallic accessories
      if (actor.accessory === 'commander-crest') {
        const crest = new THREE.Mesh(
          new THREE.BoxGeometry(0.44, 0.11, 0.24),
          anodizedGoldMat
        );
        crest.position.set(0, 0.42, 0.16);
        headGroup.add(crest);
      } else if (actor.accessory === 'marketing-beret') {
        const beret = new THREE.Mesh(
          new THREE.CylinderGeometry(0.46, 0.35, 0.15, 24),
          crimsonAnodizedAlloyMat
        );
        beret.position.set(-0.08, 0.43, 0.02);
        beret.rotation.z = 0.22;
        headGroup.add(beret);
      } else if (actor.accessory === 'knowledge-mortarboard') {
        const board = new THREE.Mesh(
          new THREE.BoxGeometry(0.92, 0.055, 0.92),
          darkGunmetalMat
        );
        board.position.set(0, 0.45, 0);
        board.rotation.y = Math.PI / 4;
        headGroup.add(board);

        const tassel = new THREE.Mesh(
          new THREE.CylinderGeometry(0.025, 0.04, 0.34, 8),
          anodizedGoldMat
        );
        tassel.position.set(0.4, 0.29, 0.2);
        headGroup.add(tassel);

        [-0.2, 0.2].forEach((gx) => {
          const rim = new THREE.Mesh(
            new THREE.TorusGeometry(0.145, 0.02, 8, 20),
            anodizedGoldMat
          );
          rim.position.set(gx, -0.015, 0.445);
          headGroup.add(rim);
        });
      } else if (actor.accessory === 'studio-headphones') {
        const headband = new THREE.Mesh(
          new THREE.TorusGeometry(0.56, 0.05, 12, 28, Math.PI),
          crimsonAnodizedAlloyMat
        );
        headband.position.set(0, 0.02, 0);
        headGroup.add(headband);
      } else if (actor.accessory === 'ops-cap') {
        const visorBill = new THREE.Mesh(
          new THREE.BoxGeometry(0.7, 0.055, 0.32),
          darkGunmetalMat
        );
        visorBill.position.set(0, 0.25, 0.46);
        headGroup.add(visorBill);
      }

      const hitbox = new THREE.Mesh(hitboxGeo, hitboxMat);
      hitbox.position.set(0, 1.2, 0);
      hitbox.userData = { departmentId: actor.id, agentCode: actor.agentCode };
      root.add(hitbox);
      clickableHitboxes.push(hitbox);

      scene.add(root);
      robotMap.set(actor.id, {
        root,
        bodyGroup,
        headGroup,
        leftArm,
        rightArm,
        leftLeg,
        rightLeg,
        leftEye,
        rightEye,
        shellMaterials: [shellMat],
        hitbox,
      });
    });

    // 6B. Articulated Seated Assistant Robots in the 4 Side Conference Chairs & Station Chairs
    // Positioned at the exact outer chair coordinates (0.58m outside the oval table rim) so robots NEVER clip the table!
    const seatedBotMat = brushedTitaniumMat;
    const seatedVisorMat = new THREE.MeshPhysicalMaterial({
      color: 0x07090d,
      metalness: 0.25,
      roughness: 0.05,
      clearcoat: 1.0,
    });
    const seatedCyanEyeMat = new THREE.MeshStandardMaterial({
      color: 0x67e8f9,
      emissive: 0x38bdf8,
      emissiveIntensity: 3.2,
    });
    const seatedAmberEyeMat = new THREE.MeshStandardMaterial({
      color: 0xff9e44,
      emissive: 0xf97316,
      emissiveIntensity: 3.2,
    });

    const seatedRobotConfigs = [
      ...conferenceSeats
        .filter((s) => s.hasSeatedAssistant)
        .map((s) => ({
          x: s.chairX,
          z: s.chairZ,
          baseY: 0.024,
          rot: s.chairRotY,
          scale: 0.8,
          eyeMat: s.assistantEyeColor === 'cyan' ? seatedCyanEyeMat : seatedAmberEyeMat,
        })),
      // Technical platform operator chair (-8.8 - 1.18, -5.55 - 0.56)
      {
        x: -8.8 - 1.18,
        z: -5.55 - 0.56,
        baseY: PLATFORM_TOP_Y,
        rot: 0.12,
        scale: 0.78,
        eyeMat: seatedCyanEyeMat,
      },
      // Marketing platform operator chair (8.8 - 1.22, -5.55 - 0.56)
      {
        x: 8.8 - 1.22,
        z: -5.55 - 0.56,
        baseY: PLATFORM_TOP_Y,
        rot: 0,
        scale: 0.78,
        eyeMat: seatedAmberEyeMat,
      },
    ];

    const seatedHeadGroups: THREE.Group[] = [];

    seatedRobotConfigs.forEach((sb) => {
      const sg = new THREE.Group();
      // Place group at exact floor/platform surface elevation; seat cushion top is at local y = 0.48
      sg.position.set(sb.x, sb.baseY, sb.z);
      sg.rotation.y = sb.rot;
      sg.scale.setScalar(sb.scale);

      // Seated pelvis & bent legs resting cleanly on the floor/platform outside the table
      [-0.17, 0.17].forEach((lx) => {
        const thigh = new THREE.Mesh(
          new THREE.CylinderGeometry(0.085, 0.08, 0.24, 12),
          seatedBotMat
        );
        thigh.rotation.x = Math.PI / 2;
        thigh.position.set(lx, 0.52, 0.12);
        sg.add(thigh);

        const knee = new THREE.Mesh(jointSphereGeo, polishedChromeMat);
        knee.position.set(lx, 0.52, 0.24);
        sg.add(knee);

        const shin = new THREE.Mesh(
          new THREE.CylinderGeometry(0.08, 0.075, 0.34, 12),
          seatedBotMat
        );
        shin.position.set(lx, 0.32, 0.24);
        sg.add(shin);

        const boot = new THREE.Mesh(
          new THREE.BoxGeometry(0.2, 0.09, 0.24),
          darkGunmetalMat
        );
        boot.position.set(lx, 0.12, 0.27);
        sg.add(boot);
      });

      const sWaist = new THREE.Mesh(
        new THREE.CylinderGeometry(0.19, 0.21, 0.14, 14),
        darkGunmetalMat
      );
      sWaist.position.y = 0.56;
      sg.add(sWaist);

      const sTorso = new THREE.Mesh(robotTorsoGeo, seatedBotMat);
      sTorso.position.y = 0.86;
      sg.add(sTorso);

      // Articulated seated arms resting comfortably above chair armrests (z <= 0.22, never touching table!)
      [-0.44, 0.44].forEach((ax) => {
        const sShoulder = new THREE.Mesh(jointSphereGeo, darkGunmetalMat);
        sShoulder.position.set(ax, 0.96, 0);
        sg.add(sShoulder);

        const sUpperArm = new THREE.Mesh(
          new THREE.CylinderGeometry(0.08, 0.075, 0.22, 12),
          seatedBotMat
        );
        sUpperArm.position.set(ax, 0.83, 0.02);
        sg.add(sUpperArm);

        const sElbow = new THREE.Mesh(
          new THREE.SphereGeometry(0.078, 10, 8),
          polishedChromeMat
        );
        sElbow.position.set(ax, 0.72, 0.04);
        sg.add(sElbow);

        const sForearm = new THREE.Mesh(
          new THREE.CylinderGeometry(0.072, 0.068, 0.2, 12),
          seatedBotMat
        );
        sForearm.rotation.x = Math.PI / 2 - 0.15;
        sForearm.position.set(ax * 0.92, 0.72, 0.14);
        sg.add(sForearm);
      });

      const sNeck = new THREE.Mesh(
        new THREE.CylinderGeometry(0.15, 0.17, 0.14, 14),
        darkGunmetalMat
      );
      sNeck.position.y = 1.2;
      sg.add(sNeck);

      const sHeadGroup = new THREE.Group();
      sHeadGroup.position.y = 1.54;
      sg.add(sHeadGroup);
      seatedHeadGroups.push(sHeadGroup);

      const sHead = new THREE.Mesh(robotHeadGeo, seatedBotMat);
      sHeadGroup.add(sHead);

      const sVisorBezel = new THREE.Mesh(robotVisorBezelGeo, polishedChromeMat);
      sVisorBezel.position.set(0, -0.02, 0.372);
      sHeadGroup.add(sVisorBezel);

      const sVisor = new THREE.Mesh(robotVisorGeo, seatedVisorMat);
      sVisor.position.set(0, -0.02, 0.386);
      sHeadGroup.add(sVisor);

      [-0.19, 0.19].forEach((ex) => {
        const sEye = new THREE.Mesh(eyeOuterGeo, sb.eyeMat);
        sEye.scale.set(1.0, 1.15, 0.42);
        sEye.position.set(ex, -0.02, 0.438);
        sHeadGroup.add(sEye);
      });

      [-0.54, 0.54].forEach((ex) => {
        const sEar = new THREE.Mesh(earCupGeo, crimsonAnodizedAlloyMat);
        sEar.rotation.z = Math.PI / 2;
        sEar.position.set(ex, 0, 0);
        sHeadGroup.add(sEar);
      });

      officeGroup.add(sg);
    });

    if (!isSoftwareGl) {
      renderer.compile(scene, camera);
    }

    // 7. Keyboard Listeners (WASD / Arrows to walk/run Commander, Space to Jump, E to Talk)
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (
        target &&
        (target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.tagName === 'SELECT')
      ) {
        return;
      }
      keysRef.current[e.code] = true;

      if (e.code === 'Space') {
        e.preventDefault();
        actorsRef.current = actorsRef.current.map((a) =>
          a.id === 'overview' || a.id === focusedDeptRef.current
            ? triggerActorJump(a, 7.5)
            : a
        );
      } else if (e.code === 'KeyE') {
        const commander = actorsRef.current[0];
        const { nearest } = findNearestAgentToPosition(commander.pos, actorsRef.current);
        if (nearest) {
          handleTriggerPairwiseChat(nearest.id);
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysRef.current[e.code] = false;
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    // 8. Click Raycasting on 3D Robots AND Click-to-Move on the 3D Floor (With Obstacle Protection!)
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleCanvasClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);

      const robotHits = raycaster.intersectObjects(clickableHitboxes, false);
      if (robotHits.length > 0) {
        const deptId = robotHits[0].object.userData.departmentId as DepartmentId;
        handleWalkCommanderToStation(deptId);
        return;
      }

      const floorHits = raycaster.intersectObject(baseFloor, false);
      if (floorHits.length > 0) {
        const pt = floorHits[0].point;
        const safePt = resolvePositionAgainstObstacles(pt.x, pt.z, 0.65);
        walkRingPosRef.current = { x: safePt.x, z: safePt.z };
        walkRingTimerRef.current = 2.8;
        actorsRef.current = setCommanderWalkTarget(
          actorsRef.current,
          safePt.x,
          safePt.z,
          true
        );
      }
    };

    renderer.domElement.addEventListener('click', handleCanvasClick);

    // 9. Resize Handler + ResizeObserver
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 1000;
      const h = container.clientHeight || 520;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);
    const resizeObserver = new ResizeObserver(() => handleResize());
    resizeObserver.observe(container);

    // 10. Game Loop with Collision Avoidance, Ground Elevation, Live Monitor Screens & Software-WebGL `afterDraw` Pacing
    const clock = new THREE.Clock();
    let frameId = 0;
    let lastHudUpdate = 0;
    let lastScreenUpdate = -1;
    let autoChatCooldown = 5.0;

    function afterDraw(cb: () => void) {
      frameId = window.setTimeout(() => requestAnimationFrame(cb), 80);
    }

    function tick() {
      const dt = Math.min(clock.getDelta(), 0.08);
      const elapsed = clock.getElapsedTime();
      const isReduced = reduceMotionRef.current;

      // Live Computer Monitor & Laptop Screen Animation (~12 FPS canvas texture updates)
      if (!isReduced && elapsed - lastScreenUpdate >= 0.085) {
        lastScreenUpdate = elapsed;
        drawAnimatedMonitorScreen(techScreenTex, 'technical', elapsed, activeProduct.sku);
        drawAnimatedMonitorScreen(mktScreenTex, 'marketing', elapsed, activeProduct.sku);
        drawAnimatedMonitorScreen(opsCheckTex, 'ops-check', elapsed, activeProduct.sku);
        drawAnimatedMonitorScreen(opsStoreTex, 'ops-store', elapsed, activeProduct.sku);
        drawAnimatedMonitorScreen(laptopScreenTex, 'laptop-terminal', elapsed, activeProduct.sku);
      }

      // Subtle lifelike head nod/turn for seated assistant robots at conference table & workstations
      if (!isReduced) {
        seatedHeadGroups.forEach((shg, sIdx) => {
          shg.rotation.y = Math.sin(elapsed * 1.6 + sIdx * 1.3) * 0.14;
          shg.rotation.x = Math.cos(elapsed * 2.1 + sIdx * 0.9) * 0.05;
        });
      }

      // Update Walk Target Ring visibility on floor
      if (walkRingTimerRef.current > 0) {
        walkRingTimerRef.current = Math.max(0, walkRingTimerRef.current - dt);
        const ringFloorY = getFloorElevationAt(
          walkRingPosRef.current.x,
          walkRingPosRef.current.z
        );
        walkTargetRing.position.set(
          walkRingPosRef.current.x,
          ringFloorY + 0.015,
          walkRingPosRef.current.z
        );
        const pulseScale = 1 + Math.sin(elapsed * 8) * 0.15;
        walkTargetRing.scale.setScalar(pulseScale);
        (walkTargetRing.material as THREE.MeshBasicMaterial).opacity = Math.min(
          0.88,
          walkRingTimerRef.current
        );
      } else {
        (walkTargetRing.material as THREE.MeshBasicMaterial).opacity = 0;
      }

      // Periodic autonomous 2-way social dialogue between agents
      autoChatCooldown -= dt;
      if (autoChatCooldown <= 0 && !isReduced) {
        autoChatCooldown = 6.8;
        const pair =
          PAIRWISE_DIALOGUES[dialogueIndexRef.current % PAIRWISE_DIALOGUES.length];
        dialogueIndexRef.current += 1;
        actorsRef.current = actorsRef.current.map((a) => {
          if (a.id === pair.speakerA) {
            return {
              ...triggerActorJump(a, 5.2),
              isTalking: true,
              talkingWithId: pair.speakerB,
              currentSpeech: pair.lineA,
              speechTimer: 5.5,
            };
          }
          if (a.id === pair.speakerB) {
            return {
              ...a,
              isTalking: true,
              talkingWithId: pair.speakerA,
              currentSpeech: pair.lineB,
              speechTimer: 5.5,
            };
          }
          return a;
        });
      }

      // True PBR Metallic Presets (All presets maintain high physical metalness!)
      const targetMetalness =
        finishPresetRef.current === 'mirror-chrome'
          ? 0.98
          : finishPresetRef.current === 'matte-ceramic'
          ? 0.78
          : 0.9;
      const targetRoughness =
        finishPresetRef.current === 'mirror-chrome'
          ? 0.06
          : finishPresetRef.current === 'matte-ceramic'
          ? 0.34
          : 0.2;

      const keys = keysRef.current;
      const snapshotActors = actorsRef.current;

      const movedActors = snapshotActors.map((actor, idx) => {
        let updated = stepActorPhysics(actor, dt);

        if (updated.speechTimer > 0) {
          updated.speechTimer = Math.max(0, updated.speechTimer - dt);
          if (updated.speechTimer === 0) {
            updated.isTalking = false;
            updated.talkingWithId = null;
          }
        }

        const moveX =
          updated.id === 'overview'
            ? (keys['KeyD'] || keys['ArrowRight'] ? 1 : 0) -
              (keys['KeyA'] || keys['ArrowLeft'] ? 1 : 0)
            : 0;
        const moveZ =
          updated.id === 'overview'
            ? (keys['KeyS'] || keys['ArrowDown'] ? 1 : 0) -
              (keys['KeyW'] || keys['ArrowUp'] ? 1 : 0)
            : 0;

        if (updated.id === 'overview' && (moveX !== 0 || moveZ !== 0)) {
          updated.customTargetPos = null;
          const isSprint = Boolean(keys['ShiftLeft'] || keys['ShiftRight']);
          const speed = isSprint ? 7.4 : 5.4;
          const len = Math.hypot(moveX, moveZ);
          const nx = moveX / len;
          const nz = moveZ / len;
          const steered = stepActorMovementWithCollision(
            updated.pos.x,
            updated.pos.z,
            nx,
            nz,
            speed,
            dt,
            0.62
          );
          updated.pos.x = steered.x;
          updated.pos.z = steered.z;
          updated.rotationY = steered.rotationY;
          updated.walkPhase += dt * (isSprint ? 15 : 11);
          updated.isMoving = true;
          updated.isRunning = isSprint;
        } else if (updated.customTargetPos) {
          const dx = updated.customTargetPos.x - updated.pos.x;
          const dz = updated.customTargetPos.z - updated.pos.z;
          const dist = Math.hypot(dx, dz);
          if (dist < 0.32) {
            updated.customTargetPos = null;
            updated.isMoving = false;
            updated.isRunning = false;
            updated.pauseTimer = 1.8;
            if (!updated.isJumping) {
              updated = triggerActorJump(updated, 5.6);
            }
          } else {
            const runSpeed = 5.6;
            const steered = stepActorMovementWithCollision(
              updated.pos.x,
              updated.pos.z,
              dx / dist,
              dz / dist,
              runSpeed,
              dt,
              0.6
            );
            updated.pos.x = steered.x;
            updated.pos.z = steered.z;
            updated.rotationY = steered.rotationY;
            updated.walkPhase += dt * 13.5;
            updated.isMoving = true;
            updated.isRunning = true;
          }
        } else if (!isReduced) {
          if (updated.pauseTimer > 0) {
            updated.pauseTimer = Math.max(0, updated.pauseTimer - dt);
            updated.isMoving = false;

            if (updated.talkingWithId) {
              const partner = snapshotActors.find((p) => p.id === updated.talkingWithId);
              if (partner) {
                const pdx = partner.pos.x - updated.pos.x;
                const pdz = partner.pos.z - updated.pos.z;
                updated.rotationY = Math.atan2(pdx * 0.65, Math.max(1.8, pdz + 2.5));
              }
            } else {
              updated.rotationY = THREE.MathUtils.damp(
                updated.rotationY,
                updated.pos.x < -1 ? 0.35 : updated.pos.x > 1 ? -0.35 : 0,
                5,
                dt
              );
            }
          } else {
            const target = updated.waypoints[updated.waypointIndex] || updated.homePos;
            const dx = target.x - updated.pos.x;
            const dz = target.z - updated.pos.z;
            const dist = Math.hypot(dx, dz);

            if (dist < 0.32) {
              updated.waypointIndex = (updated.waypointIndex + 1) % updated.waypoints.length;
              updated.pauseTimer = 1.5 + (idx % 3) * 0.5;
              updated.isMoving = false;

              if (updated.waypointIndex === 1 && !updated.isJumping) {
                updated = triggerActorJump(updated, 5.4);
                const lines = AGENT_DIALOGUE_SCRIPT[updated.id];
                updated.isTalking = true;
                updated.currentSpeech = lines[Math.floor(elapsed + idx) % lines.length];
                updated.speechTimer = 5.0;
              }
            } else {
              const walkSpeed = updated.id === 'overview' ? 3.2 : 2.6;
              const steered = stepActorMovementWithCollision(
                updated.pos.x,
                updated.pos.z,
                dx / dist,
                dz / dist,
                walkSpeed,
                dt,
                0.58
              );
              updated.pos.x = steered.x;
              updated.pos.z = steered.z;
              updated.rotationY = steered.rotationY;
              updated.walkPhase += dt * 9.5;
              updated.isMoving = true;
              updated.isRunning = false;
            }
          }
        }

        return updated;
      });

      // Enforce Robot-to-Robot & Obstacle Separation
      actorsRef.current = resolveActorToActorCollisions(movedActors, 1.3);

      // Apply transforms to Three.js mesh parts with strict non-negative floor clearance
      actorsRef.current.forEach((updated, idx) => {
        const parts = robotMap.get(updated.id);
        if (!parts) return;

        parts.shellMaterials.forEach((m) => {
          m.metalness = targetMetalness;
          m.roughness = targetRoughness;
        });

        const floorY = getFloorElevationAt(updated.pos.x, updated.pos.z);
        parts.root.position.set(updated.pos.x, 0, updated.pos.z);

        const gaitBob =
          !isReduced && updated.isMoving
            ? Math.abs(Math.sin(updated.walkPhase)) * (updated.isRunning ? 0.095 : 0.065)
            : 0;
        parts.bodyGroup.position.y = floorY + Math.max(0, updated.pos.y) + gaitBob;

        parts.bodyGroup.rotation.y = THREE.MathUtils.damp(
          parts.bodyGroup.rotation.y,
          updated.rotationY,
          10,
          dt
        );

        if (!isReduced) {
          const swingAmp = updated.isMoving ? (updated.isRunning ? 0.42 : 0.3) : 0;
          const sinPhase = Math.sin(updated.walkPhase);
          const swing = sinPhase * swingAmp;
          parts.leftLeg.rotation.x = swing;
          parts.rightLeg.rotation.x = -swing;
          // Lift swinging leg upward so neither boot toe nor heel ever dips below floorY!
          parts.leftLeg.position.y =
            0.44 + (updated.isMoving ? Math.max(0, sinPhase) * 0.08 : 0);
          parts.rightLeg.position.y =
            0.44 + (updated.isMoving ? Math.max(0, -sinPhase) * 0.08 : 0);

          if (updated.isJumping) {
            parts.leftArm.rotation.z = 0.95;
            parts.rightArm.rotation.z = -0.95;
            parts.leftArm.rotation.x = -0.3;
            parts.rightArm.rotation.x = -0.3;
          } else if (updated.isTalking) {
            parts.leftArm.rotation.z = 0.22 + Math.sin(elapsed * 7 + idx) * 0.12;
            parts.rightArm.rotation.z = -0.58 - Math.sin(elapsed * 9 + idx) * 0.24;
            parts.leftArm.rotation.x = -0.25;
            parts.rightArm.rotation.x = -0.45;
            parts.headGroup.rotation.z = Math.sin(elapsed * 5 + idx) * 0.08;
            parts.headGroup.rotation.x = Math.sin(elapsed * 6) * 0.05;
          } else {
            parts.leftArm.rotation.z = 0.12;
            parts.rightArm.rotation.z = -0.12;
            parts.leftArm.rotation.x = -swing * 0.75;
            parts.rightArm.rotation.x = swing * 0.75;
            parts.headGroup.rotation.z = 0;
            parts.headGroup.rotation.x = 0;
          }
        }
      });

      // Smooth 8D Camera Choreography
      if (cameraModeRef.current === 'cinematic_8d') {
        const orbitX = Math.sin(elapsed * 0.22) * 8.5;
        const orbitZ = 19.5 + Math.cos(elapsed * 0.22) * 2.5;
        _targetCamPos.set(orbitX, 14.5, orbitZ);
        _targetLookAt.set(0, 0.9, 0.2);
        camera.position.lerp(_targetCamPos, 1 - Math.exp(-3 * dt));
        controls.target.lerp(_targetLookAt, 1 - Math.exp(-4 * dt));
      } else if (cameraModeRef.current === 'follow_commander') {
        const cmd = actorsRef.current[0];
        _targetCamPos.set(cmd.pos.x, 7.6, cmd.pos.z + 9.6);
        _targetLookAt.set(cmd.pos.x, 1.2, cmd.pos.z);
        camera.position.lerp(_targetCamPos, 1 - Math.exp(-5 * dt));
        controls.target.lerp(_targetLookAt, 1 - Math.exp(-6 * dt));
      } else if (cameraModeRef.current === 'meeting_closeup') {
        const targetActor =
          actorsRef.current.find((a) => a.id === focusedDeptRef.current) ||
          actorsRef.current[0];
        _targetCamPos.set(targetActor.pos.x + 2.4, 4.6, targetActor.pos.z + 5.8);
        _targetLookAt.set(targetActor.pos.x, 1.3, targetActor.pos.z);
        camera.position.lerp(_targetCamPos, 1 - Math.exp(-5 * dt));
        controls.target.lerp(_targetLookAt, 1 - Math.exp(-6 * dt));
      }

      controls.update();
      renderer.render(scene, camera);

      // Project 3D speech bubbles to 2D overlay at <= 10Hz
      const now = performance.now();
      if (now - lastHudUpdate > 110) {
        lastHudUpdate = now;
        const w = renderer.domElement.clientWidth || width;
        const h = renderer.domElement.clientHeight || height;

        const stationBannerAnchors: Record<DepartmentId, { x: number; y: number; z: number }> = {
          overview: { x: 0, y: 3.25, z: -4.4 },
          technical: { x: -8.8, y: 3.35, z: -6.8 },
          marketing: { x: 8.8, y: 3.35, z: -6.8 },
          knowledge: { x: -10.6, y: 1.85, z: 2.95 },
          imagestudio: { x: 10.6, y: 1.85, z: 2.95 },
          operations: { x: -4.2, y: 1.65, z: 6.8 },
          memory: { x: 4.2, y: 1.65, z: 6.8 },
        };

        const nextBubbles: ProjectedBubble[] = actorsRef.current.map((a) => {
          const anchor = stationBannerAnchors[a.id];
          _projVec.set(anchor.x, anchor.y, anchor.z);
          _projVec.project(camera);
          const rawSx = ((_projVec.x + 1) / 2) * w;
          const rawSy = ((-_projVec.y + 1) / 2) * h;
          const clampedSx = Math.max(96, Math.min(w - 96, rawSx));
          const clampedSy = Math.max(64, Math.min(h - 24, rawSy));
          return {
            id: a.id,
            agentCode: a.agentCode,
            displayName: a.displayName,
            roleTitle: a.roleTitle,
            colorHex: a.colorHex,
            text: a.currentSpeech,
            screenX: clampedSx,
            screenY: clampedSy,
            visible:
              _projVec.z < 1 &&
              rawSx > 8 &&
              rawSx < w - 8 &&
              rawSy > 12 &&
              rawSy < h - 12,
            isTalking: a.isTalking,
          };
        });
        setBubbles(nextBubbles);
      }

      if (isSoftwareGl) {
        afterDraw(tick);
      } else {
        frameId = requestAnimationFrame(tick);
      }
    }

    renderer.render(scene, camera);
    container.dataset.rendered = "true";
    tick();

    return () => {
      cancelAnimationFrame(frameId);
      clearTimeout(frameId);
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('resize', handleResize);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener('click', handleCanvasClick);
      controls.dispose();
      renderer.dispose();
    };
  }, [activeProduct.sku]);

  const switchCameraMode = (
    mode: 'overview' | 'cinematic_8d' | 'follow_commander' | 'meeting_closeup'
  ) => {
    cameraModeRef.current = mode;
    setCameraMode(mode);
  };

  const activeTalkingIds = bubbles
    .filter((b) => b.isTalking)
    .slice(0, 1)
    .map((b) => b.id);

  return (
    <div className="w-full frame-8d-stage rounded-2xl border border-[#685043] overflow-hidden select-none flex flex-col">
      {/* Spacious 8D WebGL Viewport Area */}
      <div className="relative w-full h-[480px] lg:h-[530px] overflow-hidden agent-floor-grid">
        {/* Dedicated Empty Ref Mount for WebGLRenderer Canvas */}
        <div
          ref={canvasMountRef}
          data-testid="agent-office-3d-canvas"
          className="w-full h-full cursor-pointer"
        />

        {/* Top HUD Bar: Live Speech Bubble Ticker + Collision-Free Controls Guide */}
        <div className="absolute top-2.5 left-3 right-3 z-10 pointer-events-none flex flex-wrap items-center justify-between gap-2">
          <div className="max-w-full lg:max-w-[58%] bg-gradient-to-b from-[#2A1F1A]/95 to-[#18120F]/95 border border-[#8A6B58] rounded-full px-3.5 py-1 text-[11px] text-[#FAF6F0] flex items-center gap-2 shadow-[inset_0_1px_0_rgba(255,248,235,0.18),0_8px_20px_-4px_rgba(0,0,0,0.65)]">
            <Volume2 className="w-3.5 h-3.5 text-[#E03B2F] shrink-0" />
            <span className="truncate font-semibold">{liveConversationLog}</span>
          </div>

          <div className="hidden sm:flex bg-gradient-to-b from-[#261C18]/92 to-[#16100E]/92 border border-[#6E5648] rounded-full px-3 py-1 text-[10.5px] font-mono text-[#E5D9CE] items-center gap-1.5 shadow-[inset_0_1px_0_rgba(255,248,235,0.14),0_8px_20px_-4px_rgba(0,0,0,0.6)]">
            <Gamepad2 className="w-3.5 h-3.5 text-[#F59E0B] shrink-0" />
            <span>Robot Kim Loại CNC 8D</span>
            <span aria-hidden="true">·</span>
            <span>Không xuyên sàn & đồ vật</span>
            <span aria-hidden="true">·</span>
            <span>WASD / Click Sàn: Chạy</span>
            <span aria-hidden="true">·</span>
            <span>Space: Nhảy</span>
          </div>
        </div>

        {/* 3D Projected Speech Bubbles & Reference-Matched Department Banners */}
        <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
          {bubbles.map((b) => {
            if (!b.visible) return null;
            const isFocused = focusedDept === b.id;
            const showSpeechBubble = activeTalkingIds.includes(b.id);
            const stationMeta = STATION_WALK_TARGETS[b.id];
            const DeptIcon = stationMeta.Icon;

            return (
              <div
                key={b.id}
                style={{
                  transform: `translate3d(${Math.round(b.screenX)}px, ${Math.round(
                    b.screenY
                  )}px, 0) translate(-50%, -100%)`,
                }}
                className="absolute top-0 left-0 pointer-events-auto transition-transform duration-100"
              >
                {showSpeechBubble && (
                  <div className="mb-1.5 w-[184px] card-8d-light text-[#1E1916] rounded-xl px-2.5 py-1.5 border border-[#D9382C] text-[10px] leading-tight font-medium shadow-[inset_0_1px_0_#FFFFFF,0_10px_24px_-4px_rgba(0,0,0,0.55)]">
                    <div className="font-mono font-bold text-[9px] text-[#B91C1C] uppercase mb-0.5 flex items-center justify-between gap-1">
                      <span className="truncate">{b.displayName}</span>
                      {b.id !== 'overview' && (
                        <button
                          type="button"
                          onClick={() => handleOpenDepartment(b.id)}
                          className="text-[9px] font-bold text-[#D9382C] hover:underline inline-flex items-center gap-0.5 shrink-0"
                        >
                          <span>Mở tab</span>
                          <ArrowUpRight className="w-2.5 h-2.5" />
                        </button>
                      )}
                    </div>
                    <div className="line-clamp-2 text-[#2B221E]">{b.text}</div>
                  </div>
                )}

                <button
                  type="button"
                  onClick={() => handleWalkCommanderToStation(b.id)}
                  className={`mx-auto flex items-center gap-2 px-2.5 py-1 rounded-xl border transition-all text-left cursor-pointer ${
                    isFocused
                      ? 'bg-gradient-to-b from-[#4A3025]/96 to-[#2E1D16]/96 text-[#FAF6F0] border-[#F59E0B] ring-1 ring-[#E03B2F]/70 shadow-[inset_0_1px_0_rgba(255,248,235,0.25),0_8px_20px_-3px_rgba(0,0,0,0.7)]'
                      : 'bg-gradient-to-b from-[#36261F]/94 to-[#221713]/94 text-[#F5EFE6] border-[#B48C70]/85 hover:border-[#FDE68A] shadow-[inset_0_1px_0_rgba(255,248,235,0.18),0_6px_16px_-3px_rgba(0,0,0,0.65)]'
                  }`}
                >
                  <DeptIcon className="w-3.5 h-3.5 text-[#FDE68A] shrink-0" />
                  <div className="leading-none">
                    <div className="text-[11px] font-bold text-[#FFFBEB] whitespace-nowrap">
                      {stationMeta.title}
                    </div>
                    {b.id !== 'overview' && (
                      <div className="text-[8.5px] text-[#D8C5B4] whitespace-nowrap mt-0.5">
                        {stationMeta.subtitle}
                      </div>
                    )}
                  </div>
                </button>
              </div>
            );
          })}
        </div>
      </div>

      {/* Dedicated Bottom Control Bar */}
      <div className="card-8d-dark border-t border-[#4E3E36] px-3.5 py-2.5 space-y-2">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              type="button"
              onClick={handleTriggerAllJump}
              className="px-2.5 py-1.5 rounded-lg btn-8d-crimson text-white text-xs font-bold transition-all inline-flex items-center gap-1.5 whitespace-nowrap cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Nhảy tập thể (Space)</span>
            </button>

            <button
              type="button"
              onClick={() => handleTriggerPairwiseChat()}
              className="px-2.5 py-1.5 rounded-lg bg-gradient-to-b from-[#CA6718] to-[#9A4409] hover:from-[#D97706] hover:to-[#B45309] text-white border border-[#F59E0B]/40 shadow-[inset_0_1px_0_rgba(255,255,255,0.28),0_4px_10px_rgba(0,0,0,0.45)] text-xs font-bold transition-all inline-flex items-center gap-1.5 whitespace-nowrap cursor-pointer"
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Robot Đối thoại 2 chiều (Phím E)</span>
            </button>

            <button
              type="button"
              onClick={handleRallyToConferenceTable}
              className="px-2.5 py-1.5 rounded-lg bg-gradient-to-b from-[#362A24] to-[#241C18] hover:from-[#42342C] hover:to-[#2D231E] text-[#FAF6F0] border border-[#6E5648] shadow-[inset_0_1px_0_rgba(255,248,235,0.14),0_4px_10px_rgba(0,0,0,0.45)] text-xs font-bold transition-all inline-flex items-center gap-1.5 whitespace-nowrap cursor-pointer"
            >
              <Users className="w-3.5 h-3.5 text-[#F59E0B]" />
              <span>Tập hợp quanh Bàn họp {activeProduct.sku}</span>
            </button>

            {focusedDept !== 'overview' && (
              <button
                type="button"
                onClick={() => handleOpenDepartment(focusedDept)}
                className="px-2.5 py-1.5 rounded-lg card-8d-interactive text-[#B91C1C] border border-[#E6B0A6] text-xs font-extrabold inline-flex items-center gap-1 whitespace-nowrap cursor-pointer"
              >
                <span>Mở nghiệp vụ {STATION_WALK_TARGETS[focusedDept].title}</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div
              role="group"
              aria-label="Góc máy 8D"
              className="inline-flex items-center card-8d-dark-recessed p-1 rounded-xl border border-[#3E322C]"
            >
              {[
                { id: 'overview', label: 'Toàn cảnh Rộng rãi' },
                { id: 'cinematic_8d', label: 'Quỹ đạo 8D' },
                { id: 'follow_commander', label: 'Theo Chỉ huy' },
                { id: 'meeting_closeup', label: 'Cận cảnh Robot' },
              ].map((cam) => (
                <button
                  key={cam.id}
                  type="button"
                  onClick={() => switchCameraMode(cam.id as typeof cameraMode)}
                  className={`px-2 py-1 rounded-lg text-[11px] font-medium transition-all whitespace-nowrap cursor-pointer ${
                    cameraMode === cam.id
                      ? 'btn-8d-crimson text-white'
                      : 'text-[#B8AAA0] hover:text-white'
                  }`}
                >
                  {cam.label}
                </button>
              ))}
            </div>

            <button
              type="button"
              onClick={() => setDockCollapsed((prev) => !prev)}
              className="px-2.5 py-1 rounded-lg bg-gradient-to-b from-[#2A211D] to-[#1A1412] border border-[#463831] shadow-[inset_0_1px_0_rgba(255,248,235,0.1),0_3px_8px_rgba(0,0,0,0.4)] text-[11px] font-mono text-[#D5C7BC] hover:text-white inline-flex items-center gap-1 cursor-pointer"
            >
              {dockCollapsed ? (
                <>
                  <ChevronUp className="w-3 h-3 text-[#E03B2F]" />
                  <span>Mở thêm</span>
                </>
              ) : (
                <>
                  <ChevronDown className="w-3 h-3 text-[#E03B2F]" />
                  <span>Thu gọn</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Row 2 (Collapsible): Quick Walk-To-Station Buttons + Metallic Finish Selector */}
        {!dockCollapsed && (
          <div className="pt-1.5 border-t border-[#3A2E28] flex flex-wrap items-center justify-between gap-2 text-xs">
            <div className="flex flex-wrap items-center gap-1.5">
              <span className="text-[11px] font-semibold text-[#D5C7BC] inline-flex items-center gap-1">
                <Footprints className="w-3.5 h-3.5 text-[#F59E0B]" />
                <span>Cho Chỉ huy chạy tới (Tự tránh vật cản):</span>
              </span>
              {(
                ['technical', 'marketing', 'knowledge', 'imagestudio', 'operations'] as DepartmentId[]
              ).map((deptId) => (
                <button
                  key={deptId}
                  type="button"
                  onClick={() => handleWalkCommanderToStation(deptId)}
                  className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all cursor-pointer ${
                    focusedDept === deptId
                      ? 'btn-8d-crimson text-white border-[#F26B60]/50'
                      : 'bg-gradient-to-b from-[#261E1A] to-[#16110F] text-[#E5D9CE] border-[#433630] hover:border-[#D9382C] shadow-[inset_0_1px_0_rgba(255,248,235,0.08),0_2px_5px_rgba(0,0,0,0.35)]'
                  }`}
                >
                  {STATION_WALK_TARGETS[deptId].title}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1">
                <Palette className="w-3.5 h-3.5 text-[#F59E0B]" />
                <label htmlFor="robot-finish-select" className="sr-only">
                  Chất liệu vỏ Robot
                </label>
                <select
                  id="robot-finish-select"
                  aria-label="Chất liệu vỏ Robot"
                  value={finishPreset}
                  onChange={(e) => onChangeFinishPreset(e.target.value as RobotFinishPreset)}
                  className="card-8d-dark-recessed text-[#FAF6F0] text-[11px] font-mono px-2 py-0.5 rounded-lg border border-[#433630]"
                >
                  <option value="anodized-metal">Vỏ: Titan Phay Xước CNC 8D</option>
                  <option value="mirror-chrome">Vỏ: Thép Chrome Phản Quang</option>
                  <option value="matte-ceramic">Vỏ: Hợp Kim Gunmetal Mờ</option>
                </select>
              </div>

              <div className="hidden sm:flex items-center gap-1">
                <label htmlFor="robot-eye-select" className="sr-only">
                  Kiểu mắt biểu cảm Robot
                </label>
                <select
                  id="robot-eye-select"
                  aria-label="Kiểu mắt biểu cảm Robot"
                  value={eyeStyle}
                  onChange={(e) => onChangeEyeStyle(e.target.value as RobotEyeStyle)}
                  className="card-8d-dark-recessed text-[#FAF6F0] text-[11px] font-mono px-2 py-0.5 rounded-lg border border-[#433630]"
                >
                  <option value="rounded">Mắt: Quang Học Ấm Áp BIS</option>
                  <option value="happy">Mắt: Hào hứng</option>
                  <option value="focused">Mắt: Tập trung</option>
                  <option value="wink">Mắt: Nháy mắt</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
