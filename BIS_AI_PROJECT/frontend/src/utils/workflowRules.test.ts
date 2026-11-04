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

test('3D agent office jump physics and nearest neighbor detection work accurately', () => {
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

  const nearestCheck = findNearestAgentToPosition({ x: 9.0, z: -5.0 }, actors);
  assert.equal(nearestCheck.nearest?.id, 'imagestudio');
});
