import {createHarness,canonical,syntheticProposal,verifyJournal} from './protocol.mjs';
const harness=createHarness({evaluationTime:'2026-11-15T12:00:00.000Z'});
const wire=canonical(syntheticProposal());
const initial=harness.assess(wire),replay=harness.assess(wire);
console.log(JSON.stringify({initial,replay,journal_verified:verifyJournal(harness.journal()),journal:harness.journal()},null,2));
