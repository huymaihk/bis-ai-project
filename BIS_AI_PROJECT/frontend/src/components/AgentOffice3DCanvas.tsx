import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { DepartmentId, ProductRecord } from '../types/bisTypes';
import {
  AGENT_DIALOGUE_SCRIPT,
  Agent3DActorState,
  createInitialAgentActors,
  findNearestAgentToPosition,
  RobotEyeStyle,
  RobotFinishPreset,
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
} from 'lucide-react';

interface AgentOffice3DCanvasProps {
  activeProduct: ProductRecord;
  reduceMotion: boolean;
  eyeStyle: RobotEyeStyle;
  finishPreset: RobotFinishPreset;
  onChangeEyeStyle: (style: RobotEyeStyle) => void;
  onChangeFinishPreset: (preset: RobotFinishPreset) => void;
  onSelectDepartment: (dept: DepartmentId) => void;
}

interface ProjectedBubble {
  id: DepartmentId;
  agentCode: string;
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
  leftArm: THREE.Mesh;
  rightArm: THREE.Mesh;
  leftLeg: THREE.Mesh;
  rightLeg: THREE.Mesh;
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
    depth: depth - radius * 2,
    bevelEnabled: true,
    bevelSegments: 4,
    steps: 1,
    bevelSize: radius,
    bevelThickness: radius,
  });
  geo.center();
  return geo;
}

export const AgentOffice3DCanvas: React.FC<AgentOffice3DCanvasProps> = ({
  activeProduct,
  reduceMotion,
  eyeStyle,
  finishPreset,
  onChangeEyeStyle,
  onChangeFinishPreset,
  onSelectDepartment,
}) => {
  const canvasMountRef = useRef<HTMLDivElement | null>(null);
  const actorsRef = useRef<Agent3DActorState[]>(createInitialAgentActors());
  const keysRef = useRef<Record<string, boolean>>({});
  const cameraModeRef = useRef<'overview' | 'follow_commander' | 'meeting_closeup'>('overview');
  const focusedDeptRef = useRef<DepartmentId>('imagestudio');
  const finishPresetRef = useRef<RobotFinishPreset>(finishPreset);
  const reduceMotionRef = useRef<boolean>(reduceMotion);
  const onSelectDeptRef = useRef(onSelectDepartment);

  const [cameraMode, setCameraMode] = useState<'overview' | 'follow_commander' | 'meeting_closeup'>('overview');
  const [focusedDept, setFocusedDept] = useState<DepartmentId>('imagestudio');
  const [dockCollapsed, setDockCollapsed] = useState<boolean>(false);
  const [bubbles, setBubbles] = useState<ProjectedBubble[]>([]);
  const [liveConversationLog, setLiveConversationLog] = useState<string>(
    'LUMEN-I3: "Đã gom 5 ảnh ứng viên cho JH-M235-9! Mời bạn duyệt khung 1254×1254!"'
  );

  useEffect(() => {
    finishPresetRef.current = finishPreset;
  }, [finishPreset]);

  useEffect(() => {
    reduceMotionRef.current = reduceMotion;
  }, [reduceMotion]);

  useEffect(() => {
    onSelectDeptRef.current = onSelectDepartment;
  }, [onSelectDepartment]);

  // Trigger a jump on one or all actors
  const handleTriggerAllJump = () => {
    actorsRef.current = actorsRef.current.map((a, idx) =>
      triggerActorJump(a, 6.5 + (idx % 3) * 0.6)
    );
    setLiveConversationLog(
      `Tất cả 7 Robot Agent vừa nhảy hưởng ứng tiến độ mã ${activeProduct.sku}!`
    );
  };

  // Trigger a lively conversation around the active SKU
  const handleTriggerTeamChat = (targetDept?: DepartmentId) => {
    const deptToSpeak = targetDept || focusedDeptRef.current;
    const lines = AGENT_DIALOGUE_SCRIPT[deptToSpeak] || AGENT_DIALOGUE_SCRIPT.overview;
    const pickedLine = lines[Math.floor(Math.random() * lines.length)];

    actorsRef.current = actorsRef.current.map((a) => {
      if (a.id === deptToSpeak || a.id === 'overview') {
        const jumped = triggerActorJump(a, 5.8);
        return {
          ...jumped,
          isTalking: true,
          currentSpeech:
            a.id === deptToSpeak
              ? pickedLine
              : `COMMANDER: Rõ rồi ${a.agentCode}! Đang kiểm tra ${activeProduct.sku}.`,
          speechTimer: 6.5,
        };
      }
      return a;
    });

    setLiveConversationLog(pickedLine);
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

    const width = container.clientWidth || 960;
    const height = container.clientHeight || 500;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x090b10);
    scene.fog = new THREE.FogExp2(0x090b10, 0.018);

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 120);
    camera.position.set(0, 17.5, 22.5);
    camera.lookAt(0, 0.8, 0);

    const renderer = new THREE.WebGLRenderer({
      antialias: !isSoftwareGl,
      powerPreference: 'high-performance',
      preserveDrawingBuffer: true,
    });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.setPixelRatio(isSoftwareGl ? 1 : Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.shadowMap.enabled = !isSoftwareGl;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    container.innerHTML = '';
    container.appendChild(renderer.domElement);

    // 2. Studio Environment Map for Glossy Clearcoat Anodized Metals
    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    scene.environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    pmremGenerator.dispose();

    // 3. Three-Point Warm/Cool Studio Lighting
    const hemiLight = new THREE.HemisphereLight(0xbae6fd, 0x1e1b4b, 0.85);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xfff7ed, 1.9);
    keyLight.position.set(12, 22, 14);
    if (!isSoftwareGl) {
      keyLight.castShadow = true;
      keyLight.shadow.mapSize.width = 1024;
      keyLight.shadow.mapSize.height = 1024;
      keyLight.shadow.camera.left = -18;
      keyLight.shadow.camera.right = 18;
      keyLight.shadow.camera.top = 16;
      keyLight.shadow.camera.bottom = -16;
      keyLight.shadow.bias = -0.0005;
    }
    scene.add(keyLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 1.1);
    rimLight.position.set(-14, 10, -12);
    scene.add(rimLight);

    // 4. OrbitControls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = !isSoftwareGl;
    controls.dampingFactor = 0.06;
    controls.maxPolarAngle = Math.PI / 2 - 0.08;
    controls.minDistance = 6;
    controls.maxDistance = 38;
    controls.target.set(0, 0.8, 0);

    // 5. Build SAMS-Inspired 3D Agent Office Floor & Neon-Trimmed Department Rooms
    const officeGroup = new THREE.Group();
    scene.add(officeGroup);

    // Main Obsidian Base Platform
    const baseFloorGeo = new THREE.BoxGeometry(30, 0.4, 22);
    const baseFloorMat = new THREE.MeshStandardMaterial({
      color: 0x0f131c,
      roughness: 0.75,
      metalness: 0.2,
    });
    const baseFloor = new THREE.Mesh(baseFloorGeo, baseFloorMat);
    baseFloor.position.y = -0.2;
    baseFloor.receiveShadow = !isSoftwareGl;
    officeGroup.add(baseFloor);

    // Subtle Grid Overlay on Floor (Offset by +0.01 to avoid Z-fighting)
    const gridHelper = new THREE.GridHelper(28, 28, 0x1e293b, 0x161e2e);
    gridHelper.position.y = 0.01;
    officeGroup.add(gridHelper);

    // Department Room Zones (Matching Video 1's neon-bordered rooms!)
    const roomSpecs: {
      id: DepartmentId;
      label: string;
      x: number;
      z: number;
      w: number;
      d: number;
      color: number;
    }[] = [
      { id: 'overview', label: 'BIS HQ PLAZA', x: 0, z: 0, w: 6.8, d: 4.8, color: 0xe11d48 },
      { id: 'technical', label: 'TECHNICAL LAB', x: -9.5, z: -5.5, w: 6.2, d: 4.6, color: 0xf59e0b },
      { id: 'marketing', label: 'MARKETING STUDIO', x: 0, z: -6.8, w: 6.2, d: 4.2, color: 0xe2e8f0 },
      { id: 'imagestudio', label: 'IMAGE STUDIO 1254', x: 9.5, z: -5.5, w: 6.6, d: 4.8, color: 0x0ea5e9 },
      { id: 'operations', label: 'HARAVAN VAULT', x: 9.2, z: 5.2, w: 6.2, d: 4.6, color: 0xef4444 },
      { id: 'knowledge', label: 'KNOWLEDGE LIB', x: -9.2, z: 5.2, w: 6.2, d: 4.6, color: 0x10b981 },
      { id: 'memory', label: 'MEMORY CORE', x: 0, z: 6.5, w: 6.0, d: 4.2, color: 0xa855f7 },
    ];

    const sharedDeskGeo = new THREE.BoxGeometry(2.1, 0.65, 1.0);
    const sharedDeskMat = new THREE.MeshStandardMaterial({
      color: 0x1e2433,
      roughness: 0.4,
      metalness: 0.5,
    });
    const sharedScreenGeo = new THREE.BoxGeometry(1.3, 0.85, 0.08);

    roomSpecs.forEach((rm) => {
      const roomGroup = new THREE.Group();
      roomGroup.position.set(rm.x, 0, rm.z);

      // Raised Room Carpet Pad (y = 0.03 to prevent Z-fighting)
      const padGeo = new THREE.BoxGeometry(rm.w, 0.06, rm.d);
      const padMat = new THREE.MeshStandardMaterial({
        color: 0x161b26,
        roughness: 0.6,
        metalness: 0.25,
      });
      const padMesh = new THREE.Mesh(padGeo, padMat);
      padMesh.position.y = 0.03;
      roomGroup.add(padMesh);

      // Glowing Neon Perimeter Curb (Inspired by Video 1 SAMS Office Map)
      const borderMat = new THREE.MeshStandardMaterial({
        color: rm.color,
        emissive: rm.color,
        emissiveIntensity: 0.85,
        roughness: 0.2,
      });

      const curbThickness = 0.12;
      const curbHeight = 0.14;
      const northCurb = new THREE.Mesh(
        new THREE.BoxGeometry(rm.w, curbHeight, curbThickness),
        borderMat
      );
      northCurb.position.set(0, 0.07, -rm.d / 2);
      roomGroup.add(northCurb);

      const southCurb = new THREE.Mesh(
        new THREE.BoxGeometry(rm.w * 0.65, curbHeight, curbThickness),
        borderMat
      );
      southCurb.position.set(0, 0.07, rm.d / 2);
      roomGroup.add(southCurb);

      const westCurb = new THREE.Mesh(
        new THREE.BoxGeometry(curbThickness, curbHeight, rm.d),
        borderMat
      );
      westCurb.position.set(-rm.w / 2, 0.07, 0);
      roomGroup.add(westCurb);

      const eastCurb = new THREE.Mesh(
        new THREE.BoxGeometry(curbThickness, curbHeight, rm.d),
        borderMat
      );
      eastCurb.position.set(rm.w / 2, 0.07, 0);
      roomGroup.add(eastCurb);

      // Workstation Desk & Glowing Holo Monitor inside each department room
      if (rm.id !== 'overview') {
        const desk = new THREE.Mesh(sharedDeskGeo, sharedDeskMat);
        desk.position.set(0, 0.35, -rm.d * 0.22);
        roomGroup.add(desk);

        const screenMat = new THREE.MeshStandardMaterial({
          color: 0x090d16,
          emissive: rm.color,
          emissiveIntensity: 0.45,
          roughness: 0.15,
        });
        const monitor = new THREE.Mesh(sharedScreenGeo, screenMat);
        monitor.position.set(0, 0.95, -rm.d * 0.28);
        roomGroup.add(monitor);
      } else {
        // Central Meeting Holo-Table in BIS HQ Plaza
        const holoTable = new THREE.Mesh(
          new THREE.CylinderGeometry(1.35, 1.15, 0.55, 24),
          sharedDeskMat
        );
        holoTable.position.set(0, 0.3, -0.3);
        roomGroup.add(holoTable);

        const holoRing = new THREE.Mesh(
          new THREE.TorusGeometry(1.1, 0.05, 12, 32),
          borderMat
        );
        holoRing.rotation.x = Math.PI / 2;
        holoRing.position.set(0, 0.62, -0.3);
        roomGroup.add(holoRing);
      }

      officeGroup.add(roomGroup);
    });

    // Illuminated Corridor Pathways connecting BIS HQ Plaza to the 6 Rooms
    const corridorMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      emissive: 0x0ea5e9,
      emissiveIntensity: 0.5,
      roughness: 0.3,
    });
    const corridorCoords = [
      { x: -4.8, z: -2.8, w: 4.5, d: 0.18, rot: 0.48 },
      { x: 0, z: -3.6, w: 0.22, d: 2.8, rot: 0 },
      { x: 4.8, z: -2.8, w: 4.5, d: 0.18, rot: -0.48 },
      { x: 4.8, z: 2.8, w: 4.5, d: 0.18, rot: 0.48 },
      { x: -4.8, z: 2.8, w: 4.5, d: 0.18, rot: -0.48 },
      { x: 0, z: 3.5, w: 0.22, d: 2.6, rot: 0 },
    ];
    corridorCoords.forEach((c) => {
      const strip = new THREE.Mesh(new THREE.BoxGeometry(c.w, 0.03, c.d), corridorMat);
      strip.position.set(c.x, 0.025, c.z);
      strip.rotation.y = c.rot;
      officeGroup.add(strip);
    });

    // 6. Build Composite 11-Part Procedural 3D SAMS-Style Glossy Robots
    const headGeo = createRoundedBoxExtrudeGeometry(1.08, 0.82, 0.86, 0.24);
    const torsoGeo = createRoundedBoxExtrudeGeometry(0.84, 0.72, 0.64, 0.2);
    const visorGeo = createRoundedBoxExtrudeGeometry(0.82, 0.44, 0.16, 0.1);
    const limbGeo = new THREE.CapsuleGeometry(0.13, 0.26, 8, 12);
    const eyeGeo = new THREE.CapsuleGeometry(0.065, 0.08, 6, 10);
    const shadowDiscGeo = new THREE.CircleGeometry(0.68, 24);
    const hitboxGeo = new THREE.CylinderGeometry(0.8, 0.8, 2.2, 8);
    const hitboxMat = new THREE.MeshBasicMaterial({ visible: false });

    const visorGlassMat = new THREE.MeshPhysicalMaterial({
      color: 0x05070b,
      roughness: 0.06,
      metalness: 0.15,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05,
    });

    const shadowDiscMat = new THREE.MeshBasicMaterial({
      color: 0x000000,
      transparent: true,
      opacity: 0.45,
      depthWrite: false,
    });

    const robotMap = new Map<DepartmentId, RobotMeshParts>();
    const clickableHitboxes: THREE.Mesh[] = [];

    actorsRef.current.forEach((actor) => {
      const root = new THREE.Group();
      root.position.set(actor.pos.x, 0, actor.pos.z);

      // Ground Contact Shadow Disc (y = 0.02)
      const shadowDisc = new THREE.Mesh(shadowDiscGeo, shadowDiscMat);
      shadowDisc.rotation.x = -Math.PI / 2;
      shadowDisc.position.y = 0.02;
      root.add(shadowDisc);

      // Glossy Anodized Shell Material (Matches Video 1 SAMS Robot Look)
      const shellMat = new THREE.MeshPhysicalMaterial({
        color: new THREE.Color(actor.colorHex),
        metalness: 0.82,
        roughness: 0.18,
        clearcoat: 1.0,
        clearcoatRoughness: 0.08,
        envMapIntensity: 1.35,
      });

      const bodyGroup = new THREE.Group();
      root.add(bodyGroup);

      // Legs (pivoted at hip)
      const leftLeg = new THREE.Mesh(limbGeo, shellMat);
      leftLeg.position.set(-0.22, 0.26, 0);
      bodyGroup.add(leftLeg);

      const rightLeg = new THREE.Mesh(limbGeo, shellMat);
      rightLeg.position.set(0.22, 0.26, 0);
      bodyGroup.add(rightLeg);

      // Chubby Torso
      const torso = new THREE.Mesh(torsoGeo, shellMat);
      torso.position.set(0, 0.72, 0);
      torso.castShadow = !isSoftwareGl;
      bodyGroup.add(torso);

      // Chest Core Badge
      const badgeMat = new THREE.MeshStandardMaterial({
        color: 0x090d16,
        emissive: new THREE.Color(actor.colorHex),
        emissiveIntensity: 0.6,
        roughness: 0.2,
      });
      const chestBadge = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.16, 0.08), badgeMat);
      chestBadge.position.set(0, 0.74, 0.31);
      bodyGroup.add(chestBadge);

      // Articulated Arms
      const leftArm = new THREE.Mesh(limbGeo, shellMat);
      leftArm.position.set(-0.54, 0.72, 0);
      bodyGroup.add(leftArm);

      const rightArm = new THREE.Mesh(limbGeo, shellMat);
      rightArm.position.set(0.54, 0.72, 0);
      bodyGroup.add(rightArm);

      // Rounded Squircle Helmet Head Group
      const headGroup = new THREE.Group();
      headGroup.position.set(0, 1.44, 0);
      bodyGroup.add(headGroup);

      const helmet = new THREE.Mesh(headGeo, shellMat);
      helmet.castShadow = !isSoftwareGl;
      headGroup.add(helmet);

      const visor = new THREE.Mesh(visorGeo, visorGlassMat);
      visor.position.set(0, -0.02, 0.39);
      headGroup.add(visor);

      // Expressive Luminous Eyes inside Visor
      const eyeMat = new THREE.MeshStandardMaterial({
        color: 0xffffff,
        emissive: actor.id === 'marketing' ? 0x38bdf8 : 0xffffff,
        emissiveIntensity: 1.4,
      });
      const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
      leftEye.position.set(-0.18, -0.01, 0.48);
      headGroup.add(leftEye);

      const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
      rightEye.position.set(0.18, -0.01, 0.48);
      headGroup.add(rightEye);

      // Raycast Hitbox
      const hitbox = new THREE.Mesh(hitboxGeo, hitboxMat);
      hitbox.position.set(0, 1.1, 0);
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

    if (!isSoftwareGl) {
      renderer.compile(scene, camera);
    }

    // 7. Keyboard Listeners (WASD / Arrows to walk Commander, Space to Jump, E to Talk)
    const handleKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA' || target.tagName === 'SELECT')) {
        return;
      }
      keysRef.current[e.code] = true;

      if (e.code === 'Space') {
        e.preventDefault();
        actorsRef.current = actorsRef.current.map((a) =>
          a.id === 'overview' || a.id === focusedDeptRef.current
            ? triggerActorJump(a, 7.0)
            : a
        );
      } else if (e.code === 'KeyE') {
        const commander = actorsRef.current[0];
        const { nearest } = findNearestAgentToPosition(commander.pos, actorsRef.current);
        if (nearest) {
          focusedDeptRef.current = nearest.id;
          setFocusedDept(nearest.id);
          handleTriggerTeamChat(nearest.id);
        }
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      keysRef.current[e.code] = false;
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    // 8. Click Raycasting on 3D Robots
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleCanvasClick = (event: MouseEvent) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const hits = raycaster.intersectObjects(clickableHitboxes, false);
      if (hits.length > 0) {
        const deptId = hits[0].object.userData.departmentId as DepartmentId;
        focusedDeptRef.current = deptId;
        setFocusedDept(deptId);
        handleTriggerTeamChat(deptId);
      }
    };

    renderer.domElement.addEventListener('click', handleCanvasClick);

    // 9. Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth || 960;
      const h = container.clientHeight || 500;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // 10. Game Loop with Software-WebGL `afterDraw` Pacing
    const clock = new THREE.Clock();
    let frameId = 0;
    let lastHudUpdate = 0;

    function afterDraw(cb: () => void) {
      const gl = renderer.getContext() as WebGL2RenderingContext;
      const sync = gl.fenceSync(gl.SYNC_GPU_COMMANDS_COMPLETE, 0);
      gl.flush();
      const poll = () => {
        const state = sync && gl.getSyncParameter(sync, gl.SYNC_STATUS);
        if (state === gl.UNSIGNALED) {
          frameId = window.setTimeout(poll, 5);
        } else {
          if (sync) gl.deleteSync(sync);
          frameId = window.setTimeout(cb, 80);
        }
      };
      frameId = window.setTimeout(poll, 5);
    }

    function tick() {
      const dt = Math.min(clock.getDelta(), 0.1);
      const elapsed = clock.getElapsedTime();
      const isReduced = reduceMotionRef.current;

      // Update material roughness/metalness based on Finish Preset
      const targetMetalness =
        finishPresetRef.current === 'mirror-chrome'
          ? 0.98
          : finishPresetRef.current === 'matte-ceramic'
          ? 0.25
          : 0.82;
      const targetRoughness =
        finishPresetRef.current === 'mirror-chrome'
          ? 0.05
          : finishPresetRef.current === 'matte-ceramic'
          ? 0.55
          : 0.18;

      // Advance each actor's walking, jumping, and talking state
      const keys = keysRef.current;
      actorsRef.current = actorsRef.current.map((actor, idx) => {
        let updated = stepActorPhysics(actor, dt);

        if (updated.speechTimer > 0) {
          updated.speechTimer = Math.max(0, updated.speechTimer - dt);
          if (updated.speechTimer === 0) {
            updated.isTalking = false;
          }
        }

        // Player-controlled Commander (WASD / Arrow keys)
        if (updated.id === 'overview') {
          const moveX =
            (keys['KeyD'] || keys['ArrowRight'] ? 1 : 0) -
            (keys['KeyA'] || keys['ArrowLeft'] ? 1 : 0);
          const moveZ =
            (keys['KeyS'] || keys['ArrowDown'] ? 1 : 0) -
            (keys['KeyW'] || keys['ArrowUp'] ? 1 : 0);

          if (moveX !== 0 || moveZ !== 0) {
            const speed = 5.4;
            const len = Math.hypot(moveX, moveZ);
            const nx = moveX / len;
            const nz = moveZ / len;
            updated.pos.x = THREE.MathUtils.clamp(updated.pos.x + nx * speed * dt, -12.5, 12.5);
            updated.pos.z = THREE.MathUtils.clamp(updated.pos.z + nz * speed * dt, -8.5, 8.5);
            updated.rotationY = Math.atan2(nx, nz);
            updated.walkPhase += dt * 11;
          }
        } else if (!isReduced) {
          // Autonomous Agent Patrol between Department Station & Central Plaza
          if (updated.pauseTimer > 0) {
            updated.pauseTimer = Math.max(0, updated.pauseTimer - dt);
          } else {
            const target = updated.waypoints[updated.waypointIndex] || updated.homePos;
            const dx = target.x - updated.pos.x;
            const dz = target.z - updated.pos.z;
            const dist = Math.hypot(dx, dz);

            if (dist < 0.25) {
              updated.waypointIndex = (updated.waypointIndex + 1) % updated.waypoints.length;
              updated.pauseTimer = 1.6 + (idx % 3) * 0.7;
              // Periodic joyful hop & status speech when arriving at a waypoint
              if (updated.waypointIndex === 1 && !updated.isJumping) {
                updated = triggerActorJump(updated, 5.2);
                const lines = AGENT_DIALOGUE_SCRIPT[updated.id];
                updated.isTalking = true;
                updated.currentSpeech = lines[Math.floor(elapsed) % lines.length];
                updated.speechTimer = 4.5;
              }
            } else {
              const walkSpeed = 2.3;
              updated.pos.x += (dx / dist) * walkSpeed * dt;
              updated.pos.z += (dz / dist) * walkSpeed * dt;
              updated.rotationY = Math.atan2(dx, dz);
              updated.walkPhase += dt * 8.5;
            }
          }
        }

        // Apply transforms to Three.js mesh parts
        const parts = robotMap.get(updated.id);
        if (parts) {
          parts.shellMaterials.forEach((m) => {
            m.metalness = targetMetalness;
            m.roughness = targetRoughness;
          });

          parts.root.position.set(updated.pos.x, 0, updated.pos.z);
          parts.bodyGroup.position.y =
            updated.pos.y + (!isReduced ? Math.abs(Math.sin(updated.walkPhase)) * 0.06 : 0);

          // Smooth Y rotation damping
          parts.bodyGroup.rotation.y = THREE.MathUtils.damp(
            parts.bodyGroup.rotation.y,
            updated.rotationY,
            10,
            dt
          );

          // Limb swing & talking wave animation
          if (!isReduced) {
            const swing = Math.sin(updated.walkPhase) * 0.45;
            parts.leftLeg.rotation.x = swing;
            parts.rightLeg.rotation.x = -swing;

            if (updated.isJumping) {
              parts.leftArm.rotation.z = 0.85;
              parts.rightArm.rotation.z = -0.85;
            } else if (updated.isTalking) {
              parts.leftArm.rotation.z = 0.15;
              parts.rightArm.rotation.z = -0.55 - Math.sin(elapsed * 9) * 0.25;
              parts.headGroup.rotation.z = Math.sin(elapsed * 5) * 0.08;
            } else {
              parts.leftArm.rotation.z = 0.1;
              parts.rightArm.rotation.z = -0.1;
              parts.leftArm.rotation.x = -swing * 0.7;
              parts.rightArm.rotation.x = swing * 0.7;
              parts.headGroup.rotation.z = 0;
            }
          }
        }

        return updated;
      });

      // Smooth Camera Choreography
      if (cameraModeRef.current === 'follow_commander') {
        const cmd = actorsRef.current[0];
        _targetCamPos.set(cmd.pos.x, 7.5, cmd.pos.z + 9.5);
        _targetLookAt.set(cmd.pos.x, 1.2, cmd.pos.z);
        camera.position.lerp(_targetCamPos, 1 - Math.exp(-5 * dt));
        controls.target.lerp(_targetLookAt, 1 - Math.exp(-6 * dt));
      } else if (cameraModeRef.current === 'meeting_closeup') {
        const targetActor =
          actorsRef.current.find((a) => a.id === focusedDeptRef.current) ||
          actorsRef.current[3];
        _targetCamPos.set(targetActor.pos.x + 2.5, 4.2, targetActor.pos.z + 5.8);
        _targetLookAt.set(targetActor.pos.x, 1.3, targetActor.pos.z);
        camera.position.lerp(_targetCamPos, 1 - Math.exp(-5 * dt));
        controls.target.lerp(_targetLookAt, 1 - Math.exp(-6 * dt));
      }

      controls.update();
      renderer.render(scene, camera);

      // Project 3D speech bubbles to 2D overlay at <= 10Hz to avoid React state churn
      const now = performance.now();
      if (now - lastHudUpdate > 110) {
        lastHudUpdate = now;
        const w = renderer.domElement.clientWidth || width;
        const h = renderer.domElement.clientHeight || height;

        const nextBubbles: ProjectedBubble[] = actorsRef.current.map((a) => {
          _projVec.set(a.pos.x, a.pos.y + 2.35, a.pos.z);
          _projVec.project(camera);
          const rawSx = ((_projVec.x + 1) / 2) * w;
          const rawSy = ((-_projVec.y + 1) / 2) * h;
          const clampedSx = Math.max(115, Math.min(w - 115, rawSx));
          const clampedSy = Math.max(95, Math.min(h - 120, rawSy));
          return {
            id: a.id,
            agentCode: a.agentCode,
            roleTitle: a.roleTitle,
            colorHex: a.colorHex,
            text: a.currentSpeech,
            screenX: clampedSx,
            screenY: clampedSy,
            visible: _projVec.z < 1 && rawSx > 15 && rawSx < w - 15 && rawSy > 20 && rawSy < h - 30,
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
    tick();

    return () => {
      cancelAnimationFrame(frameId);
      clearTimeout(frameId);
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('resize', handleResize);
      renderer.domElement.removeEventListener('click', handleCanvasClick);
      controls.dispose();
      renderer.dispose();
    };
  }, []);

  const switchCameraMode = (mode: 'overview' | 'follow_commander' | 'meeting_closeup') => {
    cameraModeRef.current = mode;
    setCameraMode(mode);
  };

  return (
    <div className="relative w-full h-[560px] lg:h-[620px] bg-[#090B10] rounded-2xl border border-[#252B3B] overflow-hidden select-none">
      {/* Dedicated Empty Ref Mount for WebGLRenderer Canvas */}
      <div
        ref={canvasMountRef}
        data-testid="agent-office-3d-canvas"
        className="w-full h-full cursor-grab active:cursor-grabbing"
      />

      {/* Top HUD Bar: Folder Path + Controls Hint + Live Speech Ticker */}
      <div className="absolute top-3 left-3 right-3 z-10 pointer-events-none flex flex-wrap items-center justify-between gap-2">
        <div className="bg-[#0B0C0F]/90 border border-[#2E3648] rounded-lg px-3 py-1.5 text-xs flex items-center gap-2">
          <Gamepad2 className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
          <span className="font-mono font-bold text-white">
            3D OFFICE · G:\My Drive\BIS_AI_PROJECT
          </span>
          <span className="text-[#9CA3AF]" aria-hidden="true">·</span>
          <span className="font-mono text-[#F59E0B]">SKU: {activeProduct.sku}</span>
        </div>

        <div className="hidden xl:flex bg-[#0B0C0F]/90 border border-[#252B3B] rounded-lg px-2.5 py-1.5 text-[11px] font-mono text-[#D1D5DB] items-center gap-1.5">
          <span>WASD: Chạy</span>
          <span aria-hidden="true">·</span>
          <span>Space: Nhảy</span>
          <span aria-hidden="true">·</span>
          <span>Phím E / Click: Nói chuyện</span>
        </div>

        <div className="max-w-xs sm:max-w-sm flex items-center gap-2 bg-[#12151F]/95 border border-[#38BDF8]/50 rounded-lg px-3 py-1.5 text-xs text-[#F3F4F6]">
          <Volume2 className="w-3.5 h-3.5 text-[#38BDF8] shrink-0" />
          <span className="truncate font-medium">{liveConversationLog}</span>
        </div>
      </div>

      {/* 3D Projected Speech Bubbles & Floating Agent Nameplates */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden z-10">
        {bubbles.map((b) => {
          if (!b.visible) return null;
          const isFocused = focusedDept === b.id;
          const showBubble = isFocused || (b.isTalking && b.id === 'overview');
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
              {/* Speech Bubble when Agent is Focused or Commander is Talking */}
              {showBubble && (
                <div className="mb-1.5 w-[210px] bg-[#F8FAFC] text-[#0F172A] rounded-xl px-2.5 py-2 shadow-lg border-2 border-[#0EA5E9] text-[11px] leading-snug font-medium">
                  <div className="font-mono font-bold text-[10px] text-[#0284C7] uppercase mb-0.5 flex items-center justify-between gap-1">
                    <span className="truncate">{b.agentCode} ĐANG NÓI:</span>
                    {b.id !== 'overview' && (
                      <button
                        type="button"
                        onClick={() => onSelectDepartment(b.id)}
                        className="text-[10px] font-bold text-[#E11D48] hover:underline inline-flex items-center gap-0.5 shrink-0"
                      >
                        <span>Mở trạm</span>
                        <ArrowUpRight className="w-2.5 h-2.5" />
                      </button>
                    )}
                  </div>
                  <div className="line-clamp-3">{b.text}</div>
                </div>
              )}

              {/* Compact Agent Nameplate Tag */}
              <button
                type="button"
                onClick={() => {
                  focusedDeptRef.current = b.id;
                  setFocusedDept(b.id);
                  handleTriggerTeamChat(b.id);
                }}
                className={`mx-auto flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-mono font-bold border transition-colors ${
                  isFocused
                    ? 'bg-[#181C26] text-white border-[#38BDF8]'
                    : 'bg-[#090B10]/90 text-[#E2E8F0] border-[#252B3B] hover:border-white'
                }`}
              >
                <span
                  className="w-2 h-2 rounded-xs shrink-0"
                  style={{ backgroundColor: b.colorHex }}
                />
                <span>{b.agentCode}</span>
              </button>
            </div>
          );
        })}
      </div>

      {/* Unified Collapsible Bottom Control Dock (Zero Clipping 2-Row Layout) */}
      <div
        className={`absolute bottom-2.5 left-1/2 -translate-x-1/2 z-20 w-[96%] max-w-[920px] transition-transform duration-200 ${
          dockCollapsed ? 'translate-y-[calc(100%-32px)]' : 'translate-y-0'
        }`}
      >
        {/* Collapse / Expand Handle */}
        <div className="flex justify-center mb-1">
          <button
            type="button"
            onClick={() => setDockCollapsed((prev) => !prev)}
            className="px-3 py-1 rounded-t-lg bg-[#12151F] border border-b-0 border-[#2E3648] text-[11px] font-mono text-[#E2E8F0] hover:text-white flex items-center gap-1.5"
          >
            {dockCollapsed ? (
              <>
                <ChevronUp className="w-3.5 h-3.5 text-[#38BDF8]" />
                <span>▴ Mở Bảng Điều khiển 3D & Tùy chỉnh Nhân vật</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-3.5 h-3.5 text-[#38BDF8]" />
                <span>▾ Thu gọn Điều khiển (Chế độ Quan sát 3D)</span>
              </>
            )}
          </button>
        </div>

        {/* Bottom Dock Body */}
        <div className="bg-[#12151F]/95 border border-[#2E3648] rounded-xl p-2.5 space-y-2">
          {/* Row 1: Game Actions & Camera Choreography Presets */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                onClick={handleTriggerAllJump}
                className="px-2.5 py-1.5 rounded-lg bg-[#E11D48] hover:bg-[#BE123C] text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5 whitespace-nowrap"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Nhảy tập thể (Space)</span>
              </button>

              <button
                type="button"
                onClick={() => handleTriggerTeamChat()}
                className="px-2.5 py-1.5 rounded-lg bg-[#0EA5E9] hover:bg-[#0284C7] text-white text-xs font-bold transition-colors inline-flex items-center gap-1.5 whitespace-nowrap"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>Họp & Báo cáo SKU (Phím E)</span>
              </button>

              {focusedDept !== 'overview' && (
                <button
                  type="button"
                  onClick={() => onSelectDepartment(focusedDept)}
                  className="px-2.5 py-1.5 rounded-lg bg-[#181C26] hover:bg-[#252B3B] text-[#38BDF8] border border-[#38BDF8]/50 text-xs font-semibold inline-flex items-center gap-1 whitespace-nowrap"
                >
                  <span>Vào phòng {focusedDept.toUpperCase()}</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            <div
              role="group"
              aria-label="Góc máy 3D"
              className="inline-flex items-center bg-[#090B10] p-1 rounded-lg border border-[#252B3B]"
            >
              {[
                { id: 'overview', label: 'Toàn cảnh Văn phòng' },
                { id: 'follow_commander', label: 'Theo chân Commander' },
                { id: 'meeting_closeup', label: 'Cận cảnh Robot' },
              ].map((cam) => (
                <button
                  key={cam.id}
                  type="button"
                  onClick={() => switchCameraMode(cam.id as typeof cameraMode)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors whitespace-nowrap ${
                    cameraMode === cam.id
                      ? 'bg-[#1E2330] text-white'
                      : 'text-[#9CA3AF] hover:text-white'
                  }`}
                >
                  {cam.label}
                </button>
              ))}
            </div>
          </div>

          {/* Row 2: SAMS-Style Robot Finish & Eye Customizer ("The colour. The eyes. The finish.") */}
          <div className="pt-1.5 border-t border-[#222836] flex flex-wrap items-center justify-between gap-2 text-xs">
            <span className="text-[11px] font-mono text-[#9CA3AF]">
              TÙY CHỈNH TẠO HÌNH ROBOT 3D (SAMS STUDIO):
            </span>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1.5">
                <Palette className="w-3.5 h-3.5 text-[#F59E0B]" />
                <label htmlFor="robot-finish-select" className="sr-only">
                  Chất liệu vỏ Robot
                </label>
                <select
                  id="robot-finish-select"
                  aria-label="Chất liệu vỏ Robot"
                  value={finishPreset}
                  onChange={(e) => onChangeFinishPreset(e.target.value as RobotFinishPreset)}
                  className="bg-[#090B10] text-[#E2E8F0] text-xs font-mono px-2.5 py-1 rounded-lg border border-[#252B3B]"
                >
                  <option value="anodized-metal">Vỏ: Kim loại Anodized</option>
                  <option value="mirror-chrome">Vỏ: Crôm Bóng Gương</option>
                  <option value="matte-ceramic">Vỏ: Gốm Mờ Studio</option>
                </select>
              </div>

              <div className="flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-[#38BDF8]" />
                <label htmlFor="robot-eye-select" className="sr-only">
                  Kiểu mắt biểu cảm Robot
                </label>
                <select
                  id="robot-eye-select"
                  aria-label="Kiểu mắt biểu cảm Robot"
                  value={eyeStyle}
                  onChange={(e) => onChangeEyeStyle(e.target.value as RobotEyeStyle)}
                  className="bg-[#090B10] text-[#E2E8F0] text-xs font-mono px-2.5 py-1 rounded-lg border border-[#252B3B]"
                >
                  <option value="rounded">Mắt: Tiêu chuẩn SAMS</option>
                  <option value="happy">Mắt: Hào hứng (Vui vẻ)</option>
                  <option value="focused">Mắt: Tập trung Soi lỗi</option>
                  <option value="wink">Mắt: Nháy mắt</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
