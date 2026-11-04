import { DepartmentId } from '../types/bisTypes';

export type RobotFinishPreset = 'anodized-metal' | 'mirror-chrome' | 'matte-ceramic';
export type RobotEyeStyle = 'rounded' | 'focused' | 'happy' | 'wink';
export type RobotAccessoryType =
  | 'commander-crest'
  | 'tech-visor-lab'
  | 'marketing-beret'
  | 'studio-headphones'
  | 'ops-cap'
  | 'knowledge-mortarboard'
  | 'memory-gold-headset';

export interface SceneObstacle {
  id: string;
  label: string;
  kind: 'ellipse' | 'box';
  x: number;
  z: number;
  /** For ellipse: X semi-axis; For box: half-width along X */
  rx: number;
  /** For ellipse: Z semi-axis; For box: half-depth along Z */
  rz: number;
}

export interface ConferenceTableSpec {
  centerX: number;
  centerZ: number;
  baseRadius: number;
  scaleX: number;
  scaleZ: number;
  /** Outer X semi-axis of the oval tabletop (baseRadius * scaleX) */
  rx: number;
  /** Outer Z semi-axis of the oval tabletop (baseRadius * scaleZ) */
  rz: number;
}

export const CONFERENCE_TABLE_SPEC: ConferenceTableSpec = {
  centerX: 0,
  centerZ: -0.2,
  baseRadius: 2.65,
  scaleX: 1.15,
  scaleZ: 0.76,
  rx: 2.65 * 1.15, // 3.0475m
  rz: 2.65 * 0.76, // 2.014m
};

export interface ConferenceSeatSlot {
  id: string;
  theta: number;
  rimX: number;
  rimZ: number;
  normalX: number;
  normalZ: number;
  chairX: number;
  chairZ: number;
  chairRotY: number;
  chairScale: number;
  hasSeatedAssistant: boolean;
  assistantEyeColor: 'cyan' | 'amber';
  laptopX: number;
  laptopZ: number;
  laptopRotY: number;
}

/**
 * Computes the 5 executive conference chair & seated robot slots strictly outside the oval tabletop
 * along the true outward normal of the ellipse so knees, arms, and chairs NEVER intersect the table.
 */
export function getConferenceTableSeats(
  spec: ConferenceTableSpec = CONFERENCE_TABLE_SPEC,
  chairClearanceFromRim = 0.58
): ConferenceSeatSlot[] {
  const configs: Array<{
    id: string;
    theta: number;
    chairScale: number;
    hasSeatedAssistant: boolean;
    assistantEyeColor: 'cyan' | 'amber';
  }> = [
    {
      id: 'head-commander',
      theta: Math.PI,
      chairScale: 1.06,
      hasSeatedAssistant: false,
      assistantEyeColor: 'amber',
    },
    {
      id: 'seat-nw',
      theta: -Math.PI * 0.64,
      chairScale: 0.95,
      hasSeatedAssistant: true,
      assistantEyeColor: 'cyan',
    },
    {
      id: 'seat-ne',
      theta: Math.PI * 0.64,
      chairScale: 0.95,
      hasSeatedAssistant: true,
      assistantEyeColor: 'cyan',
    },
    {
      id: 'seat-sw',
      theta: -Math.PI * 0.36,
      chairScale: 0.95,
      hasSeatedAssistant: true,
      assistantEyeColor: 'amber',
    },
    {
      id: 'seat-se',
      theta: Math.PI * 0.36,
      chairScale: 0.95,
      hasSeatedAssistant: true,
      assistantEyeColor: 'amber',
    },
  ];

  return configs.map((cfg) => {
    const sinT = Math.sin(cfg.theta);
    const cosT = Math.cos(cfg.theta);
    const rimX = spec.centerX + spec.rx * sinT;
    const rimZ = spec.centerZ + spec.rz * cosT;

    // True outward normal of the ellipse (x/rx)^2 + (z/rz)^2 = 1 at (rimX, rimZ)
    const rawNx = spec.rz * sinT;
    const rawNz = spec.rx * cosT;
    const normLen = Math.hypot(rawNx, rawNz) || 1;
    const normalX = rawNx / normLen;
    const normalZ = rawNz / normLen;

    const chairX = rimX + normalX * chairClearanceFromRim;
    const chairZ = rimZ + normalZ * chairClearanceFromRim;
    // Face directly inward along (-normalX, -normalZ) perpendicular to the table edge
    const chairRotY = Math.atan2(-normalX, -normalZ);

    // Place corresponding laptop 0.44m inside the table rim facing outward toward the chair
    const laptopX = rimX - normalX * 0.44;
    const laptopZ = rimZ - normalZ * 0.44;
    const laptopRotY = Math.atan2(normalX, normalZ);

    return {
      id: cfg.id,
      theta: cfg.theta,
      rimX,
      rimZ,
      normalX,
      normalZ,
      chairX,
      chairZ,
      chairRotY,
      chairScale: cfg.chairScale,
      hasSeatedAssistant: cfg.hasSeatedAssistant,
      assistantEyeColor: cfg.assistantEyeColor,
      laptopX,
      laptopZ,
      laptopRotY,
    };
  });
}

/**
 * Physical 3D Furniture, Platform & Equipment Colliders in the Spacious 8D Command Room.
 * Matches 1:1 with the 3D meshes in AgentOffice3DCanvas.tsx so robots never clip through
 * platforms, tables, chairs, monitors, or props.
 */
export const SCENE_OBSTACLES: SceneObstacle[] = [
  {
    id: 'central-conference-table',
    label: 'Bàn họp Bầu dục Trung tâm 03026A & 5 Ghế xoay',
    kind: 'ellipse',
    x: 0,
    z: -0.2,
    rx: 3.68,
    rz: 2.92,
  },
  {
    id: 'technical-desk-rig',
    label: 'Bục & Bàn Kỹ thuật CAD/PDF',
    kind: 'box',
    x: -8.8,
    z: -5.55,
    rx: 2.75,
    rz: 1.42,
  },
  {
    id: 'marketing-desk-rig',
    label: 'Bục & Bàn Marketing Nội dung/SEO',
    kind: 'box',
    x: 8.8,
    z: -5.55,
    rx: 2.75,
    rz: 1.42,
  },
  {
    id: 'knowledge-library-rig',
    label: 'Bục Thư viện Tri thức, Kệ sách & Bàn tra cứu',
    kind: 'box',
    x: -10.35,
    z: 0.8,
    rx: 1.82,
    rz: 1.95,
  },
  {
    id: 'imagestudio-booth-rig',
    label: 'Bục Buồng chụp Image Studio, Đèn Softbox & Tripod',
    kind: 'box',
    x: 10.35,
    z: 0.8,
    rx: 1.82,
    rz: 1.95,
  },
  {
    id: 'operations-console-rig',
    label: 'Bục Điều hành Vận hành & Cặp Màn hình Kép',
    kind: 'box',
    x: 0,
    z: 6.18,
    rx: 4.05,
    rz: 1.18,
  },
  {
    id: 'fabric-rack-left',
    label: 'Cụm Cuộn vải Dệt may Tiền cảnh Trái',
    kind: 'box',
    x: -11.4,
    z: 5.9,
    rx: 1.65,
    rz: 1.25,
  },
  {
    id: 'fabric-rack-right',
    label: 'Cụm Cuộn vải Dệt may Tiền cảnh Phải',
    kind: 'box',
    x: 11.4,
    z: 5.9,
    rx: 1.65,
    rz: 1.25,
  },
];

/**
 * Returns the exact physical floor/rug/platform top elevation at world (x, z)
 * so every robot's metallic boot soles sit 100% flush on the surface below without sinking.
 */
export function getFloorElevationAt(x: number, z: number): number {
  // Check central woven conference rug (ellipse centered at 0, -0.2, semi-axes 5.35 x 3.80, top at y = 0.024)
  const rugNx = x / 5.35;
  const rugNz = (z - -0.2) / 3.8;
  if (rugNx * rugNx + rugNz * rugNz <= 1.0) {
    return 0.024;
  }
  return 0.0;
}

export interface Agent3DActorState {
  id: DepartmentId;
  agentCode: string;
  displayName: string;
  roleTitle: string;
  colorHex: string;
  eyeColorHex: string;
  accessory: RobotAccessoryType;
  homePos: { x: number; z: number };
  pos: { x: number; y: number; z: number };
  targetPos: { x: number; z: number };
  customTargetPos: { x: number; z: number } | null;
  velY: number;
  rotationY: number;
  walkPhase: number;
  isMoving: boolean;
  isRunning: boolean;
  isJumping: boolean;
  isTalking: boolean;
  talkingWithId: DepartmentId | null;
  currentSpeech: string;
  speechTimer: number;
  waypoints: { x: number; z: number }[];
  waypointIndex: number;
  pauseTimer: number;
}

export interface PairwiseDialogueExchange {
  id: string;
  speakerA: DepartmentId;
  speakerB: DepartmentId;
  lineA: string;
  lineB: string;
}

export const AGENT_DIALOGUE_SCRIPT: Record<DepartmentId, string[]> = {
  overview: [
    'Chỉ huy BIS: Phiên 03026A đang chạy đồng bộ! Mời các trạm báo cáo tiến độ quanh bàn họp!',
    'Chỉ huy BIS: Nhớ đối chiếu kỹ bảng thông số trang 16 và chuẩn ảnh Benchmark trước khi duyệt.',
    'Chỉ huy BIS: Mình đang đi kiểm tra từng bộ phận — bấm vào sàn hoặc dùng WASD để điều khiển mình nhé!',
  ],
  technical: [
    'Technical Robot: Đã bóc tách thông số 03026A từ trang 16 PDF: Lực kéo 0.5 – 50 kN, độ chính xác ±0.5%!',
    'Technical Robot: Đã ghim trích dẫn BIS_Testing_Equipment_Catalog.pdf (Trang 16) cho Marketing và Vận hành.',
    'Technical Robot: Tốc độ kéo 0.1 – 500 mm/min và hành trình 1,200 mm đã khớp 100% tài liệu gốc.',
  ],
  marketing: [
    'Marketing Robot: Đã biên tập mô tả song ngữ VI/EN và tối ưu SEO 148/160 ký tự cho máy 03026A!',
    'Marketing Robot: Đã cập nhật thẻ Xem trước cửa hàng (Storefront Preview) cho thiết bị đo độ bền kéo vải.',
    'Marketing Robot: Cảm ơn Technical! Mình đã đưa chuẩn ISO 13934-1 và ASTM D5034 vào 4 gạch đầu dòng nổi bật.',
  ],
  imagestudio: [
    'Image Studio Robot: Đang chụp và xử lý ảnh 03026A trong buồng chụp BIS theo 4 tiêu chí Benchmark!',
    'Image Studio Robot: Đã kiểm tra rõ chi tiết kẹp mẫu, nền phòng thí nghiệm và ánh sáng đồng nhất.',
    'Image Studio Robot: Có 3 ảnh ứng viên từ Trang 16 và Trang 18 PDF đang chờ người phụ trách phê duyệt.',
  ],
  operations: [
    'Operations Robot: Phát hiện sản phẩm tương tự 03026 (phiên bản 30 kN) với độ tương đồng 92%!',
    'Operations Robot: Đã hoàn tất 5/5 mục kiểm tra phê duyệt, sẵn sàng Tạo bản nháp trên Haravan!',
    'Operations Robot: Khác biệt chính đã ghi rõ: 03026A có dải tải 50 kN so với 30 kN của mã 03026.',
  ],
  knowledge: [
    'Knowledge Robot: Đã tra cứu 4 tài liệu tiêu chuẩn ISO 13934-1 (Trang 5, 8, 11) và ASTM D5034!',
    'Knowledge Robot: Đã đồng bộ hướng dẫn vận hành máy 03026A (Trang 3, 7, 12) vào Thư viện Tri thức.',
    'Knowledge Robot: Mọi trích dẫn trang PDF đều đã liên kết trực tiếp sang bộ phận Kỹ thuật và Bộ nhớ.',
  ],
  memory: [
    'Memory Robot: Đã lưu phiên bản v1.2 (Cập nhật mô tả SEO 148 ký tự) bởi Nguyễn Minh Anh lúc 15:18!',
    'Memory Robot: Ghi chú tri thức 03026A nhắc lịch kiểm tra hiệu chuẩn định kỳ 12 tháng.',
    'Memory Robot: CSDL nội bộ đã đồng bộ xanh, bản nháp Haravan SKU 03026A đang chờ đẩy lên cửa hàng.',
  ],
};

export const PAIRWISE_DIALOGUES: PairwiseDialogueExchange[] = [
  {
    id: 'tech-mkt',
    speakerA: 'technical',
    speakerB: 'marketing',
    lineA: 'Technical → Marketing: Mình vừa gửi thông số 0.5–50 kN và hành trình 1,200 mm ở Trang 16 nhé!',
    lineB: 'Marketing → Technical: Tuyệt vời! Mình đã đưa ngay vào mô tả SEO 148/160 ký tự đạt chuẩn xanh!',
  },
  {
    id: 'studio-ops',
    speakerA: 'imagestudio',
    speakerB: 'operations',
    lineA: 'Image Studio → Operations: Ảnh 1 (Trang 16) đã rõ chi tiết kẹp mẫu và đạt 4/4 chuẩn Benchmark!',
    lineB: 'Operations → Image Studio: Đã nhận! Mình đã tích xanh mục Hình ảnh trong checklist phê duyệt 03026A.',
  },
  {
    id: 'know-tech',
    speakerA: 'knowledge',
    speakerB: 'technical',
    lineA: 'Knowledge → Technical: Tiêu chuẩn ISO 13934-1 Trang 5 & 8 xác nhận phương pháp thử băng vải nhé!',
    lineB: 'Technical → Knowledge: Cảm ơn thư viện! Mình đã đính kèm trích dẫn chuẩn quốc tế vào hồ sơ 03026A.',
  },
  {
    id: 'cmd-ops',
    speakerA: 'overview',
    speakerB: 'operations',
    lineA: 'Chỉ huy BIS → Operations: Kết quả kiểm tra trùng lặp mã 03026A thế nào rồi?',
    lineB: 'Operations → Chỉ huy BIS: Giống 92% với mã 03026 (30 kN), nhưng 03026A là bản 50 kN — đủ điều kiện tạo nháp Haravan!',
  },
  {
    id: 'cmd-studio',
    speakerA: 'overview',
    speakerB: 'imagestudio',
    lineA: 'Chỉ huy BIS → Image Studio: Tiến độ xử lý bộ ảnh 03026A trong buồng chụp đến đâu rồi?',
    lineB: 'Image Studio → Chỉ huy BIS: Đang căn khung 4:3 và 1:1 sắc nét, mời anh/chị bấm Phê duyệt ảnh!',
  },
  {
    id: 'mem-mkt',
    speakerA: 'memory',
    speakerB: 'marketing',
    lineA: 'Memory → Marketing: Mình đã lưu lịch sử phiên bản v1.2 cho bản biên tập VI/EN của bạn rồi nhé!',
    lineB: 'Marketing → Memory: Cảm ơn Memory! Nhờ vậy mình có thể khôi phục v1.1 bất cứ lúc nào.',
  },
];

const ROOM_BOUNDS = {
  minX: -12.0,
  maxX: 12.0,
  minZ: -6.8,
  maxZ: 6.2,
} as const;

/**
 * Checks whether a 2D floor point (with robot radius padding) intersects any obstacle.
 */
export function isPointInsideObstacle(
  x: number,
  z: number,
  actorRadius = 0.55,
  obstacles: SceneObstacle[] = SCENE_OBSTACLES
): boolean {
  for (const obs of obstacles) {
    if (obs.kind === 'ellipse') {
      const rx = obs.rx + actorRadius;
      const rz = obs.rz + actorRadius;
      const nx = (x - obs.x) / rx;
      const nz = (z - obs.z) / rz;
      if (nx * nx + nz * nz < 1.0) {
        return true;
      }
    } else {
      const halfW = obs.rx + actorRadius;
      const halfD = obs.rz + actorRadius;
      if (Math.abs(x - obs.x) < halfW && Math.abs(z - obs.z) < halfD) {
        return true;
      }
    }
  }
  return false;
}

/**
 * Multi-pass solver that projects any floor coordinate (x, z) outside all furniture obstacles
 * and within room perimeter bounds so robots never clip into corners or adjacent props.
 */
export function resolvePositionAgainstObstacles(
  x: number,
  z: number,
  actorRadius = 0.58,
  obstacles: SceneObstacle[] = SCENE_OBSTACLES
): { x: number; z: number; collided: boolean } {
  let rxPos = Math.max(ROOM_BOUNDS.minX, Math.min(ROOM_BOUNDS.maxX, x));
  let rzPos = Math.max(ROOM_BOUNDS.minZ, Math.min(ROOM_BOUNDS.maxZ, z));
  let collided = false;

  for (let pass = 0; pass < 3; pass++) {
    for (const obs of obstacles) {
      if (obs.kind === 'ellipse') {
        const semiX = obs.rx + actorRadius;
        const semiZ = obs.rz + actorRadius;
        const dx = rxPos - obs.x;
        const dz = rzPos - obs.z;
        const normDistSq = (dx * dx) / (semiX * semiX) + (dz * dz) / (semiZ * semiZ);
        if (normDistSq < 1.0) {
          collided = true;
          const angle =
            Math.abs(dx) < 0.0001 && Math.abs(dz) < 0.0001
              ? -Math.PI / 2
              : Math.atan2(dz / semiZ, dx / semiX);
          rxPos = obs.x + Math.cos(angle) * (semiX + 0.06);
          rzPos = obs.z + Math.sin(angle) * (semiZ + 0.06);
        }
      } else {
        const halfW = obs.rx + actorRadius;
        const halfD = obs.rz + actorRadius;
        const dx = rxPos - obs.x;
        const dz = rzPos - obs.z;
        const overlapX = halfW - Math.abs(dx);
        const overlapZ = halfD - Math.abs(dz);

        if (overlapX > 0 && overlapZ > 0) {
          collided = true;
          if (overlapX < overlapZ) {
            rxPos = obs.x + (dx >= 0 ? halfW + 0.06 : -(halfW + 0.06));
          } else {
            rzPos = obs.z + (dz >= 0 ? halfD + 0.06 : -(halfD + 0.06));
          }
        }
      }
    }
    rxPos = Math.max(ROOM_BOUNDS.minX, Math.min(ROOM_BOUNDS.maxX, rxPos));
    rzPos = Math.max(ROOM_BOUNDS.minZ, Math.min(ROOM_BOUNDS.maxZ, rzPos));
  }

  return {
    x: rxPos,
    z: rzPos,
    collided,
  };
}

/**
 * Moves an actor toward a desired direction or target with smooth tangential sliding around obstacles
 * so robots walk cleanly around the central conference table, platforms, and desks without clipping.
 */
export function stepActorMovementWithCollision(
  currentX: number,
  currentZ: number,
  dirX: number,
  dirZ: number,
  speed: number,
  dt: number,
  actorRadius = 0.58
): { x: number; z: number; rotationY: number; deflected: boolean } {
  const stepDist = speed * dt;
  const rawNextX = currentX + dirX * stepDist;
  const rawNextZ = currentZ + dirZ * stepDist;

  if (!isPointInsideObstacle(rawNextX, rawNextZ, actorRadius)) {
    const primaryTry = resolvePositionAgainstObstacles(rawNextX, rawNextZ, actorRadius);
    if (!primaryTry.collided) {
      return {
        x: primaryTry.x,
        z: primaryTry.z,
        rotationY: Math.atan2(dirX, dirZ),
        deflected: false,
      };
    }
  }

  // Tangential steering fan: prefer consistent clockwise/counterclockwise bypass around central table
  const baseAngle = Math.atan2(dirX, dirZ);
  const turnSign = currentX >= 0 ? 1 : -1;
  const offsets = [0.52, 0.88, 1.22, 1.54];
  const candidateAngles: number[] = [];
  for (const off of offsets) {
    candidateAngles.push(baseAngle + turnSign * off);
    candidateAngles.push(baseAngle - turnSign * off);
  }

  for (const ang of candidateAngles) {
    const sx = Math.sin(ang);
    const sz = Math.cos(ang);
    const candidateX = currentX + sx * stepDist;
    const candidateZ = currentZ + sz * stepDist;
    if (!isPointInsideObstacle(candidateX, candidateZ, actorRadius)) {
      const clamped = resolvePositionAgainstObstacles(candidateX, candidateZ, actorRadius);
      if (!isPointInsideObstacle(clamped.x, clamped.z, actorRadius * 0.95)) {
        return {
          x: clamped.x,
          z: clamped.z,
          rotationY: ang,
          deflected: true,
        };
      }
    }
  }

  const fallback = resolvePositionAgainstObstacles(rawNextX, rawNextZ, actorRadius);
  return {
    x: fallback.x,
    z: fallback.z,
    rotationY: Math.atan2(fallback.x - currentX || dirX, fallback.z - currentZ || dirZ),
    deflected: true,
  };
}

/**
 * Separates robots from each other while respecting all furniture obstacles.
 */
export function resolveActorToActorCollisions(
  actors: Agent3DActorState[],
  minSeparation = 1.25
): Agent3DActorState[] {
  const next = actors.map((a) => ({
    ...a,
    pos: { ...a.pos },
  }));

  for (let pass = 0; pass < 5; pass++) {
    for (let i = 0; i < next.length; i++) {
      for (let j = i + 1; j < next.length; j++) {
        const a = next[i];
        const b = next[j];
        const dx = b.pos.x - a.pos.x;
        const dz = b.pos.z - a.pos.z;
        const dist = Math.hypot(dx, dz);
        if (dist > 0.0001 && dist < minSeparation) {
          const push = (minSeparation - dist) * 0.55;
          const nx = dx / dist;
          const nz = dz / dist;
          // Add slight perpendicular stagger so 3 colinear robots don't jam against each other
          const perpX = -nz * 0.12;
          const perpZ = nx * 0.12;
          const resA = resolvePositionAgainstObstacles(
            a.pos.x - (nx + perpX) * push,
            a.pos.z - (nz + perpZ) * push,
            0.56
          );
          const resB = resolvePositionAgainstObstacles(
            b.pos.x + (nx + perpX) * push,
            b.pos.z + (nz + perpZ) * push,
            0.56
          );
          a.pos.x = resA.x;
          a.pos.z = resA.z;
          b.pos.x = resB.x;
          b.pos.z = resB.z;
        }
      }
    }
  }

  return next;
}

export function createInitialAgentActors(): Agent3DActorState[] {
  return [
    {
      id: 'overview',
      agentCode: 'COMMANDER-BIS',
      displayName: 'Chỉ huy BIS',
      roleTitle: 'Chỉ huy Phòng điều hành (WASD / Click Sàn để Chạy)',
      colorHex: '#D9382C',
      eyeColorHex: '#FF9E44',
      accessory: 'commander-crest',
      homePos: { x: 0, z: -3.85 },
      pos: { x: 0, y: 0, z: -3.85 },
      targetPos: { x: 4.55, z: -1.85 },
      customTargetPos: null,
      velY: 0,
      rotationY: 0,
      walkPhase: 0,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: true,
      talkingWithId: 'imagestudio',
      currentSpeech: AGENT_DIALOGUE_SCRIPT.overview[0],
      speechTimer: 6,
      waypoints: [
        { x: 0, z: -3.85 },
        { x: 4.55, z: -1.85 },
        { x: 4.65, z: 1.45 },
        { x: -4.65, z: 1.45 },
        { x: -4.55, z: -1.85 },
      ],
      waypointIndex: 1,
      pauseTimer: 2.2,
    },
    {
      id: 'technical',
      agentCode: 'TECHNICAL',
      displayName: 'Technical Robot',
      roleTitle: 'Hồ sơ kỹ thuật · Spec · PDF',
      colorHex: '#0EA5E9',
      eyeColorHex: '#67E8F9',
      accessory: 'tech-visor-lab',
      homePos: { x: -7.4, z: -3.25 },
      pos: { x: -7.4, y: 0, z: -3.25 },
      targetPos: { x: -5.4, z: -3.1 },
      customTargetPos: null,
      velY: 0,
      rotationY: 0.35,
      walkPhase: 0.8,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: true,
      talkingWithId: 'marketing',
      currentSpeech: AGENT_DIALOGUE_SCRIPT.technical[0],
      speechTimer: 5.5,
      waypoints: [
        { x: -7.4, z: -3.25 },
        { x: -5.4, z: -3.1 },
        { x: -4.65, z: -2.0 },
        { x: -6.5, z: -3.25 },
      ],
      waypointIndex: 1,
      pauseTimer: 1.8,
    },
    {
      id: 'marketing',
      agentCode: 'MARKETING',
      displayName: 'Marketing Robot',
      roleTitle: 'Nội dung sản phẩm · Truyền thông',
      colorHex: '#E03B2F',
      eyeColorHex: '#FF9E44',
      accessory: 'marketing-beret',
      homePos: { x: 7.4, z: -3.25 },
      pos: { x: 7.4, y: 0, z: -3.25 },
      targetPos: { x: 5.4, z: -3.1 },
      customTargetPos: null,
      velY: 0,
      rotationY: -0.28,
      walkPhase: 1.6,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: false,
      talkingWithId: null,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.marketing[0],
      speechTimer: 0,
      waypoints: [
        { x: 7.4, z: -3.25 },
        { x: 5.4, z: -3.1 },
        { x: 4.65, z: -2.0 },
        { x: 6.5, z: -3.25 },
      ],
      waypointIndex: 1,
      pauseTimer: 2.0,
    },
    {
      id: 'knowledge',
      agentCode: 'KNOWLEDGE',
      displayName: 'Knowledge Robot',
      roleTitle: 'Thư viện · Tri thức · Lưu trữ',
      colorHex: '#D97706',
      eyeColorHex: '#FF9E44',
      accessory: 'knowledge-mortarboard',
      homePos: { x: -6.8, z: 0.85 },
      pos: { x: -6.8, y: 0, z: 0.85 },
      targetPos: { x: -5.3, z: 0.85 },
      customTargetPos: null,
      velY: 0,
      rotationY: 0.52,
      walkPhase: 2.3,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: false,
      talkingWithId: null,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.knowledge[0],
      speechTimer: 0,
      waypoints: [
        { x: -6.8, z: 0.85 },
        { x: -5.3, z: 0.85 },
        { x: -4.75, z: 0.25 },
        { x: -6.3, z: 1.65 },
      ],
      waypointIndex: 1,
      pauseTimer: 1.9,
    },
    {
      id: 'imagestudio',
      agentCode: 'IMAGE STUDIO',
      displayName: 'Image Studio Robot',
      roleTitle: 'Chụp · Xử lý · Ảnh sản phẩm',
      colorHex: '#E03B2F',
      eyeColorHex: '#FF9E44',
      accessory: 'studio-headphones',
      homePos: { x: 6.8, z: 0.85 },
      pos: { x: 6.8, y: 0, z: 0.85 },
      targetPos: { x: 5.3, z: 0.85 },
      customTargetPos: null,
      velY: 0,
      rotationY: -0.52,
      walkPhase: 3.1,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: false,
      talkingWithId: null,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.imagestudio[0],
      speechTimer: 0,
      waypoints: [
        { x: 6.8, z: 0.85 },
        { x: 5.3, z: 0.85 },
        { x: 4.75, z: 1.2 },
        { x: 6.3, z: -0.2 },
      ],
      waypointIndex: 1,
      pauseTimer: 1.7,
    },
    {
      id: 'operations',
      agentCode: 'OPERATIONS',
      displayName: 'Operations Robot',
      roleTitle: 'Quản lý tác vụ · Kiểm duyệt · Xuất bản',
      colorHex: '#10B981',
      eyeColorHex: '#67E8F9',
      accessory: 'ops-cap',
      homePos: { x: -2.6, z: 4.05 },
      pos: { x: -2.6, y: 0, z: 4.05 },
      targetPos: { x: -1.85, z: 3.75 },
      customTargetPos: null,
      velY: 0,
      rotationY: 0.32,
      walkPhase: 4.0,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: false,
      talkingWithId: null,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.operations[0],
      speechTimer: 0,
      waypoints: [
        { x: -2.6, z: 4.05 },
        { x: -1.85, z: 3.75 },
        { x: -0.95, z: 4.0 },
        { x: -3.2, z: 4.05 },
      ],
      waypointIndex: 1,
      pauseTimer: 2.1,
    },
    {
      id: 'memory',
      agentCode: 'MEMORY',
      displayName: 'Memory Robot',
      roleTitle: 'Lịch sử · Ghi chú · Đồng bộ',
      colorHex: '#F59E0B',
      eyeColorHex: '#FF9E44',
      accessory: 'memory-gold-headset',
      homePos: { x: 2.6, z: 4.05 },
      pos: { x: 2.6, y: 0, z: 4.05 },
      targetPos: { x: 1.85, z: 3.75 },
      customTargetPos: null,
      velY: 0,
      rotationY: -0.32,
      walkPhase: 5.1,
      isMoving: false,
      isRunning: false,
      isJumping: false,
      isTalking: false,
      talkingWithId: null,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.memory[0],
      speechTimer: 0,
      waypoints: [
        { x: 2.6, z: 4.05 },
        { x: 1.85, z: 3.75 },
        { x: 0.95, z: 4.0 },
        { x: 3.2, z: 4.05 },
      ],
      waypointIndex: 1,
      pauseTimer: 2.0,
    },
  ];
}

export function triggerActorJump(actor: Agent3DActorState, jumpVelocity = 7.2): Agent3DActorState {
  if (actor.pos.y > 0.05) return actor;
  return {
    ...actor,
    velY: jumpVelocity,
    isJumping: true,
  };
}

export function setCommanderWalkTarget(
  actors: Agent3DActorState[],
  targetX: number,
  targetZ: number,
  run = true
): Agent3DActorState[] {
  const safeSpot = resolvePositionAgainstObstacles(targetX, targetZ, 0.65);
  return actors.map((a) => {
    if (a.id !== 'overview') return a;
    return {
      ...a,
      customTargetPos: {
        x: safeSpot.x,
        z: safeSpot.z,
      },
      isRunning: run,
      isMoving: true,
    };
  });
}

export function rallyAllAgentsToTable(
  actors: Agent3DActorState[],
  sku: string
): Agent3DActorState[] {
  // Safe ring positions OUTSIDE the central conference table & chair obstacle (rx: 3.68, rz: 2.92)
  const tableRingOffsets: Record<DepartmentId, { x: number; z: number }> = {
    overview: { x: 0, z: -3.85 },
    technical: { x: -4.55, z: -1.85 },
    marketing: { x: 4.55, z: -1.85 },
    knowledge: { x: -4.65, z: 1.25 },
    imagestudio: { x: 4.65, z: 1.25 },
    operations: { x: -1.95, z: 3.75 },
    memory: { x: 1.95, z: 3.75 },
  };

  return actors.map((a, idx) => {
    const rawSpot = tableRingOffsets[a.id];
    const safeSpot = resolvePositionAgainstObstacles(rawSpot.x, rawSpot.z, 0.62);
    const jumped = triggerActorJump(a, 6.2 + (idx % 3) * 0.5);
    return {
      ...jumped,
      customTargetPos: { x: safeSpot.x, z: safeSpot.z },
      isRunning: true,
      isMoving: true,
      isTalking: true,
      speechTimer: 6.5,
      currentSpeech:
        a.id === 'overview'
          ? `Chỉ huy BIS: Tập hợp toàn đội quanh bàn họp phiên ${sku}!`
          : `${a.displayName}: Đang chạy về bàn họp trung tâm báo cáo mã ${sku}!`,
    };
  });
}

export function stepActorPhysics(
  actor: Agent3DActorState,
  dt: number,
  gravity = 19.5
): Agent3DActorState {
  const clampedDt = Math.min(dt, 0.1);
  let nextY = actor.pos.y + actor.velY * clampedDt;
  let nextVelY = actor.velY - gravity * clampedDt;
  let nextJumping = actor.isJumping;

  if (nextY <= 0) {
    nextY = 0;
    nextVelY = 0;
    nextJumping = false;
  }

  return {
    ...actor,
    pos: { ...actor.pos, y: nextY },
    velY: nextVelY,
    isJumping: nextJumping,
  };
}

export function findNearestAgentToPosition(
  pos: { x: number; z: number },
  actors: Agent3DActorState[],
  excludeId: DepartmentId = 'overview'
): { nearest: Agent3DActorState | null; distance: number } {
  let nearest: Agent3DActorState | null = null;
  let minDistance = Infinity;

  for (const a of actors) {
    if (a.id === excludeId) continue;
    const dx = a.pos.x - pos.x;
    const dz = a.pos.z - pos.z;
    const dist = Math.hypot(dx, dz);
    if (dist < minDistance) {
      minDistance = dist;
      nearest = a;
    }
  }

  return { nearest, distance: minDistance };
}
