import test from 'node:test';
import assert from 'node:assert/strict';
import {
  evaluateSeoMetadata,
  toggleCompareCandidateSelection,
  evaluateHaravanDraftReadiness,
  mapStepToDepartment,
} from './workflowRules';
import {
  createInitialAgentActors,
  triggerActorJump,
  stepActorPhysics,
  findNearestAgentToPosition,
  setCommanderWalkTarget,
  rallyAllAgentsToTable,
  isPointInsideObstacle,
  resolvePositionAgainstObstacles,
  stepActorMovementWithCollision,
  resolveActorToActorCollisions,
  getFloorElevationAt,
  CONFERENCE_TABLE_SPEC,
  getConferenceTableSeats,
} from './agentOfficeSim';
import { INITIAL_PRODUCTS } from '../data/mockBisData';

test('mapStepToDepartment maps 4-step pipeline accurately', () => {
  assert.equal(mapStepToDepartment('source'), 'technical');
  assert.equal(mapStepToDepartment('content'), 'marketing');
  assert.equal(mapStepToDepartment('images'), 'imagestudio');
  assert.equal(mapStepToDepartment('approval'), 'operations');
});

test('evaluateSeoMetadata validates character counts for bilingual SEO', () => {
  const validSeo = {
    titleVi: 'Máy kiểm tra mài mòn vải Martindale James Heal M235-9 chuẩn ISO',
    descVi: 'Thiết bị kiểm tra độ bền mài mòn và vón cục vải Martindale 9 vị trí James Heal M235-9 chính hãng UK, đáp ứng tiêu chuẩn ISO 12947 và ASTM D4966.',
    slugVi: 'may-kiem-tra-mai-mon-vai-martindale-james-heal-m235-9',
    titleEn: 'James Heal M235-9 Martindale Abrasion & Pilling Tester (9-Station)',
    descEn: 'Official James Heal M235-9 9-station Martindale abrasion and pilling tester compliant with ISO 12947 and ASTM D4966 textile testing standards.',
    keywords: ['Martindale M235', 'ISO 12947', 'James Heal'],
  };
  const res = evaluateSeoMetadata(validSeo);
  assert.equal(res.isValid, true);
  assert.equal(res.warnings.length, 0);

  const invalidSeo = {
    ...validSeo,
    titleVi: '',
    descEn: 'Too short',
  };
  const badRes = evaluateSeoMetadata(invalidSeo);
  assert.equal(badRes.isValid, false);
  assert.ok(badRes.warnings.length >= 2);
});

test('toggleCompareCandidateSelection enforces max 3 images for side-by-side compare', () => {
  let state = toggleCompareCandidateSelection([], 'img-1', 3);
  assert.deepEqual(state.nextIds, ['img-1']);
  state = toggleCompareCandidateSelection(state.nextIds, 'img-2', 3);
  state = toggleCompareCandidateSelection(state.nextIds, 'img-3', 3);
  assert.deepEqual(state.nextIds, ['img-1', 'img-2', 'img-3']);

  const overflow = toggleCompareCandidateSelection(state.nextIds, 'img-4', 3);
  assert.equal(overflow.limitReached, true);
  assert.deepEqual(overflow.nextIds, ['img-1', 'img-2', 'img-3']);

  const removed = toggleCompareCandidateSelection(state.nextIds, 'img-2', 3);
  assert.deepEqual(removed.nextIds, ['img-1', 'img-3']);
});

test('evaluateHaravanDraftReadiness blocks Haravan draft until human approves 1254x1254 image and specs', () => {
  const martindale = INITIAL_PRODUCTS[0];
  const initialReadiness = evaluateHaravanDraftReadiness(martindale);
  assert.equal(initialReadiness.canCreateDraft, false);
  assert.ok(initialReadiness.blockingReasons.length > 0);

  const fullyApprovedProduct = {
    ...martindale,
    specs: martindale.specs.map((s) => ({ ...s, status: 'approved' as const })),
    marketingSections: martindale.marketingSections.map((m) => ({
      ...m,
      hasMissingEvidence: false,
    })),
    activeProcessedRender: {
      renderId: 'rnd-approved',
      sourceImageId: 'cand-jh-1',
      backgroundId: 'bis-pure-white' as const,
      paddingPercent: 10,
      shadowIntensity: 15,
      contrastBoost: true,
      dimensions: '1254 × 1254 px' as const,
      createdAt: '2026-11-04 09:00',
      status: 'approved' as const,
      approvedBy: 'Trần Minh Quân',
    },
    duplicates: martindale.duplicates.map((d) => ({
      ...d,
      resolution: 'confirmed_unique' as const,
    })),
  };

  const approvedReadiness = evaluateHaravanDraftReadiness(fullyApprovedProduct);
  assert.equal(approvedReadiness.canCreateDraft, true);
  assert.equal(approvedReadiness.blockingReasons.length, 0);
});

test('3D agent office walk target, rally to table, jump physics, floor elevation, and nearest neighbor detection work accurately', () => {
  const actors = createInitialAgentActors();
  assert.equal(actors.length, 7);

  let commander = actors[0];
  assert.equal(commander.isJumping, false);

  commander = triggerActorJump(commander, 7.0);
  assert.equal(commander.isJumping, true);
  assert.equal(commander.velY, 7.0);

  commander = stepActorPhysics(commander, 0.05);
  assert.ok(commander.pos.y > 0);

  // Land after sufficient time
  for (let i = 0; i < 30; i++) {
    commander = stepActorPhysics(commander, 0.05);
  }
  assert.equal(commander.pos.y, 0);
  assert.equal(commander.isJumping, false);

  // Verify floor elevation helper never returns negative height
  assert.ok(getFloorElevationAt(0, -0.2) >= 0.02);
  assert.equal(getFloorElevationAt(7.0, 0.8), 0);

  const walkedActors = setCommanderWalkTarget(actors, 5.5, 0.8, true);
  assert.deepEqual(walkedActors[0].customTargetPos, { x: 5.5, z: 0.8 });
  assert.equal(walkedActors[0].isRunning, true);

  const ralliedActors = rallyAllAgentsToTable(actors, '03026A');
  assert.equal(ralliedActors.every((a) => a.isTalking && a.customTargetPos !== null), true);
  for (const r of ralliedActors) {
    assert.equal(
      isPointInsideObstacle(r.customTargetPos!.x, r.customTargetPos!.z, 0.55),
      false,
      `Rally target for ${r.id} must be outside all obstacles`
    );
  }

  const nearestCheck = findNearestAgentToPosition({ x: 5.6, z: 0.8 }, actors);
  assert.equal(nearestCheck.nearest?.id, 'imagestudio');
});

test('3D collision avoidance prevents robots from walking through tables, desks, or each other', () => {
  const actors = createInitialAgentActors();

  // Every initial robot position and waypoint must be outside all furniture obstacles
  for (const actor of actors) {
    assert.equal(
      isPointInsideObstacle(actor.pos.x, actor.pos.z, 0.55),
      false,
      `Initial pos for ${actor.id} should not intersect any obstacle`
    );
    for (const wp of actor.waypoints) {
      assert.equal(
        isPointInsideObstacle(wp.x, wp.z, 0.55),
        false,
        `Waypoint (${wp.x}, ${wp.z}) for ${actor.id} should not intersect any obstacle`
      );
    }
  }

  // Center of oval conference table (0, -0.2) is inside obstacle and gets pushed outside
  assert.equal(isPointInsideObstacle(0, -0.2, 0.55), true);
  const resolvedTableClick = resolvePositionAgainstObstacles(0, -0.2, 0.58);
  assert.equal(resolvedTableClick.collided, true);
  assert.equal(isPointInsideObstacle(resolvedTableClick.x, resolvedTableClick.z, 0.55), false);

  // Moving straight toward the central table from (0, -3.85) toward (0, 3.8) steers tangentially outside the table
  let cx = 0;
  let cz = -3.85;
  for (let step = 0; step < 60; step++) {
    const dx = 0 - cx;
    const dz = 3.8 - cz;
    const len = Math.hypot(dx, dz) || 1;
    const moved = stepActorMovementWithCollision(cx, cz, dx / len, dz / len, 4.5, 0.05, 0.55);
    cx = moved.x;
    cz = moved.z;
    assert.equal(
      isPointInsideObstacle(cx, cz, 0.5),
      false,
      `Step ${step}: robot at (${cx.toFixed(2)}, ${cz.toFixed(2)}) must never enter the table`
    );
  }

  // Overlapping robots are pushed apart by resolveActorToActorCollisions
  const overlapping = actors.map((a, idx) =>
    idx < 2 ? { ...a, pos: { x: 5.5 + idx * 0.1, y: 0, z: 0.8 } } : a
  );
  const separated = resolveActorToActorCollisions(overlapping, 1.25);
  const sepDist = Math.hypot(
    separated[1].pos.x - separated[0].pos.x,
    separated[1].pos.z - separated[0].pos.z
  );
  assert.ok(sepDist >= 1.2, `Expected separated distance >= 1.2, got ${sepDist}`);
});

test('Conference table chairs and seated robots are strictly outside the oval tabletop rim (zero table clipping)', () => {
  const seats = getConferenceTableSeats(CONFERENCE_TABLE_SPEC, 0.58);
  assert.equal(seats.length, 5);

  const ellipseValue = (x: number, z: number) => {
    const nx = (x - CONFERENCE_TABLE_SPEC.centerX) / CONFERENCE_TABLE_SPEC.rx;
    const nz = (z - CONFERENCE_TABLE_SPEC.centerZ) / CONFERENCE_TABLE_SPEC.rz;
    return nx * nx + nz * nz;
  };

  for (const seat of seats) {
    // 1. Chair center must be strictly outside the oval tabletop (ellipseValue > 1.25)
    const chairEv = ellipseValue(seat.chairX, seat.chairZ);
    assert.ok(
      chairEv > 1.25,
      `Chair ${seat.id} at (${seat.chairX.toFixed(2)}, ${seat.chairZ.toFixed(2)}) must be outside table (got ${chairEv.toFixed(3)})`
    );

    // 2. Seated robot's forward-most knee/boot (+0.27 * 0.80 = 0.216m inward along chairRotY) must also be strictly outside the tabletop!
    const forwardX = seat.chairX + Math.sin(seat.chairRotY) * (0.27 * 0.8);
    const forwardZ = seat.chairZ + Math.cos(seat.chairRotY) * (0.27 * 0.8);
    const kneeEv = ellipseValue(forwardX, forwardZ);
    assert.ok(
      kneeEv > 1.08,
      `Seated robot knee/boot at ${seat.id} must not clip into conference table (got ${kneeEv.toFixed(3)})`
    );

    // 3. Corresponding laptop must sit cleanly inside the oval tabletop (ellipseValue < 0.85)
    const laptopEv = ellipseValue(seat.laptopX, seat.laptopZ);
    assert.ok(
      laptopEv < 0.85,
      `Laptop at ${seat.id} must sit inside the conference tabletop (got ${laptopEv.toFixed(3)})`
    );
  }
});



