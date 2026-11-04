import { DepartmentId } from '../types/bisTypes';

export type RobotFinishPreset = 'anodized-metal' | 'mirror-chrome' | 'matte-ceramic';
export type RobotEyeStyle = 'rounded' | 'focused' | 'happy' | 'wink';

export interface Agent3DActorState {
  id: DepartmentId;
  agentCode: string;
  roleTitle: string;
  colorHex: string;
  homePos: { x: number; z: number };
  pos: { x: number; y: number; z: number };
  targetPos: { x: number; z: number };
  velY: number;
  rotationY: number;
  walkPhase: number;
  isJumping: boolean;
  isTalking: boolean;
  currentSpeech: string;
  speechTimer: number;
  waypoints: { x: number; z: number }[];
  waypointIndex: number;
  pauseTimer: number;
}

export interface AgentDialogueLine {
  speakerId: DepartmentId;
  speakerCode: string;
  listenerCode: string;
  text: string;
  skuRef: string;
}

export const AGENT_DIALOGUE_SCRIPT: Record<DepartmentId, string[]> = {
  overview: [
    'COMMANDER: Kiểm tra tiến độ chuẩn hóa G:\\My Drive\\BIS_AI_PROJECT!',
    'COMMANDER: Nhớ tuyệt đối không tự duyệt ảnh 1254×1254 khi chưa soi tem hãng.',
    'COMMANDER: Hãy giữ nguyên ngữ cảnh SKU khi chuyển giữa các phòng ban!',
  ],
  technical: [
    'ATLAS-T1: Đã đọc xong trang 14–15 PDF James Heal, phát hiện 2 thông số cần kỹ sư duyệt!',
    'ATLAS-T1: Mã BR-LAB70 đang lệch thông số lưu lượng gió 50Hz và 60Hz ở trang 21.',
    'ATLAS-T1: Mọi thông số trích xuất đều đã ghim tọa độ BBOX trên trang PDF gốc.',
  ],
  marketing: [
    'ARCHER-M2: Đã biên tập xong 7 phần nội dung cho JH-M235-9, đang chờ mã lô vải mài SM25.',
    'ARCHER-M2: Bộ đếm SEO Tiếng Việt (63/70 ký tự) và Tiếng Anh đã đạt chuẩn xanh!',
    'ARCHER-M2: Tôi vừa trao đổi với ATLAS-T1 để lấy thêm dẫn chứng ISO 12947.',
  ],
  imagestudio: [
    'LUMEN-I3: Đã gom 5 ảnh ứng viên cho JH-M235-9 từ PDF trang 14 và web jamesheal.co.uk!',
    'LUMEN-I3: Khung 1254 × 1254 px nền trắng BIS đã sẵn sàng chờ người phụ trách bấm duyệt.',
    'LUMEN-I3: Tôi không bao giờ tự chọn ảnh đầu tiên — mời bạn vào bàn 3 cột để đối chiếu!',
  ],
  operations: [
    'SAGE-O4: Cảnh báo! Mã JH-M235-9 giống 86% với mã cũ JH-M235-9S trên Haravan.',
    'SAGE-O4: Mã X-Rite Ci7800 đã đạt đủ 5/5 điều kiện, sẵn sàng Tạo bản nháp trên Haravan!',
    'SAGE-O4: Hệ thống khóa chặt lệnh xóa — chỉ tạo bản nháp an toàn trên Haravan.',
  ],
  knowledge: [
    'VERA-K5: Đã lập chỉ mục 4 bộ Catalogue PDF 2026 trong G:\\My Drive\\BIS_AI_PROJECT.',
    'VERA-K5: Đã chuẩn hóa thuật ngữ "Quỹ đạo chuyển động Lissajous" theo ISO 12947-1.',
    'VERA-K5: Tra cứu theo trang và dịch thuật ngữ dệt nhuộm luôn sẵn sàng!',
  ],
  memory: [
    'CHRONO-V6: Đã lưu phiên bản v2.4 quy tắc dịch "mài mòn và vón cục vải".',
    'CHRONO-V6: Có 2 bản ghi hiệu chỉnh cục bộ đang chờ đồng bộ với Python Backend.',
    'CHRONO-V6: Bạn có thể thu hồi (Rollback) bất kỳ phiên bản biên tập nào chỉ với 1 cú nhấp!',
  ],
};

export function createInitialAgentActors(): Agent3DActorState[] {
  return [
    {
      id: 'overview',
      agentCode: 'COMMANDER-BIS',
      roleTitle: 'Điều hành Trung tâm (Bạn điều khiển WASD / Space)',
      colorHex: '#E11D48',
      homePos: { x: 0, z: 1.5 },
      pos: { x: 0, y: 0, z: 1.5 },
      targetPos: { x: 0, z: 1.5 },
      velY: 0,
      rotationY: 0,
      walkPhase: 0,
      isJumping: false,
      isTalking: true,
      currentSpeech: 'Chào mừng tới văn phòng 3D BIS_AI_PROJECT! Dùng WASD để chạy, Space để nhảy!',
      speechTimer: 6,
      waypoints: [{ x: 0, z: 1.5 }],
      waypointIndex: 0,
      pauseTimer: 0,
    },
    {
      id: 'technical',
      agentCode: 'ATLAS-T1',
      roleTitle: 'Technical & PDF Evidence',
      colorHex: '#F59E0B',
      homePos: { x: -9.5, z: -5.5 },
      pos: { x: -9.5, y: 0, z: -5.5 },
      targetPos: { x: -4.5, z: -2.0 },
      velY: 0,
      rotationY: 0.6,
      walkPhase: 0,
      isJumping: false,
      isTalking: true,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.technical[0],
      speechTimer: 5,
      waypoints: [
        { x: -9.5, z: -5.5 },
        { x: -4.2, z: -2.2 },
        { x: -1.8, z: -3.5 },
        { x: -8.0, z: -3.0 },
      ],
      waypointIndex: 1,
      pauseTimer: 0,
    },
    {
      id: 'marketing',
      agentCode: 'ARCHER-M2',
      roleTitle: 'Marketing & SEO Song ngữ',
      colorHex: '#E2E8F0',
      homePos: { x: 0, z: -6.8 },
      pos: { x: 0, y: 0, z: -6.8 },
      targetPos: { x: 2.2, z: -2.5 },
      velY: 0,
      rotationY: 0,
      walkPhase: 1.2,
      isJumping: false,
      isTalking: false,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.marketing[0],
      speechTimer: 0,
      waypoints: [
        { x: 0, z: -6.8 },
        { x: -1.5, z: -2.8 },
        { x: 3.5, z: -3.2 },
        { x: 0, z: -4.5 },
      ],
      waypointIndex: 1,
      pauseTimer: 0.5,
    },
    {
      id: 'imagestudio',
      agentCode: 'LUMEN-I3',
      roleTitle: 'Image Studio 1254×1254',
      colorHex: '#0EA5E9',
      homePos: { x: 9.5, z: -5.5 },
      pos: { x: 9.5, y: 0, z: -5.5 },
      targetPos: { x: 5.0, z: -1.5 },
      velY: 0,
      rotationY: -0.6,
      walkPhase: 2.4,
      isJumping: false,
      isTalking: true,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.imagestudio[0],
      speechTimer: 7,
      waypoints: [
        { x: 9.5, z: -5.5 },
        { x: 4.5, z: -2.0 },
        { x: 7.5, z: 0.5 },
        { x: 8.8, z: -4.2 },
      ],
      waypointIndex: 1,
      pauseTimer: 0,
    },
    {
      id: 'operations',
      agentCode: 'SAGE-O4',
      roleTitle: 'Operations & Haravan Draft',
      colorHex: '#EF4444',
      homePos: { x: 9.2, z: 5.2 },
      pos: { x: 9.2, y: 0, z: 5.2 },
      targetPos: { x: 4.2, z: 2.8 },
      velY: 0,
      rotationY: -2.2,
      walkPhase: 0.7,
      isJumping: false,
      isTalking: false,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.operations[0],
      speechTimer: 0,
      waypoints: [
        { x: 9.2, z: 5.2 },
        { x: 3.8, z: 2.4 },
        { x: 6.5, z: -0.5 },
        { x: 8.2, z: 4.0 },
      ],
      waypointIndex: 1,
      pauseTimer: 1.0,
    },
    {
      id: 'knowledge',
      agentCode: 'VERA-K5',
      roleTitle: 'Knowledge & Thuật ngữ Dệt',
      colorHex: '#10B981',
      homePos: { x: -9.2, z: 5.2 },
      pos: { x: -9.2, y: 0, z: 5.2 },
      targetPos: { x: -4.2, z: 2.6 },
      velY: 0,
      rotationY: 2.2,
      walkPhase: 1.9,
      isJumping: false,
      isTalking: false,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.knowledge[0],
      speechTimer: 0,
      waypoints: [
        { x: -9.2, z: 5.2 },
        { x: -3.8, z: 2.4 },
        { x: -6.5, z: -0.5 },
        { x: -8.0, z: 4.2 },
      ],
      waypointIndex: 1,
      pauseTimer: 0.3,
    },
    {
      id: 'memory',
      agentCode: 'CHRONO-V6',
      roleTitle: 'Memory & Phiên bản',
      colorHex: '#A855F7',
      homePos: { x: 0, z: 6.5 },
      pos: { x: 0, y: 0, z: 6.5 },
      targetPos: { x: 0, z: 2.8 },
      velY: 0,
      rotationY: Math.PI,
      walkPhase: 3.1,
      isJumping: false,
      isTalking: false,
      currentSpeech: AGENT_DIALOGUE_SCRIPT.memory[0],
      speechTimer: 0,
      waypoints: [
        { x: 0, z: 6.5 },
        { x: -1.8, z: 3.0 },
        { x: 2.0, z: 3.0 },
        { x: 0, z: 5.2 },
      ],
      waypointIndex: 1,
      pauseTimer: 0.8,
    },
  ];
}

export function triggerActorJump(actor: Agent3DActorState, jumpVelocity = 6.8): Agent3DActorState {
  if (actor.pos.y > 0.05) return actor;
  return {
    ...actor,
    velY: jumpVelocity,
    isJumping: true,
  };
}

export function stepActorPhysics(
  actor: Agent3DActorState,
  dt: number,
  gravity = 18.5
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
