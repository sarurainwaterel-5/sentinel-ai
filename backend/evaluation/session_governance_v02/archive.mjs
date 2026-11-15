// Offline test archive only; no application imports and no database migration.
import {readFileSync} from 'node:fs';
import {evaluateSession,canonical,hash} from './evaluator.mjs';
export function dependencies(){return {archive_sha256:hash(readFileSync(new URL('./archive.mjs',import.meta.url)).toString()),evaluator_sha256:hash(readFileSync(new URL('./evaluator.mjs',import.meta.url)).toString()),specification_sha256:hash(readFileSync(new URL('./specification.json',import.meta.url)).toString()),node:process.versions.node,icu:process.versions.icu,tz:process.versions.tz};}
const denied=(status,reason)=>({status,reason,execution_authorization:'DENIED',execution_authorized:false,live_authorized:false});
export function archiveDecision(input,previous=[]){
 for(const record of previous){if(record.input?.setup&&input.setup&&record.input.setup.id===input.setup.id){if(canonical(record.input)===canonical(input))return {status:'DUPLICATE',archive:record,...denied('DUPLICATE','ORIGINAL_RECORD')};return denied('CONFLICT','SETUP_ID_ALREADY_ARCHIVED');}if(record.input?.setup&&input.setup&&record.input.setup.event_id===input.setup.event_id)return denied('CONFLICT','ACQUISITION_EVENT_ALREADY_ARCHIVED');}
 const body={version:'IMAF-SESSION-OFFLINE-ARCHIVE-v1',dependencies:dependencies(),input:structuredClone(input),assessment:evaluateSession(input),trust:'SYNTHETIC_FIXTURE_NOT_AUTHORITATIVE_ACCOUNT_HISTORY'};
 return {status:'ARCHIVED',archive:{...body,record_sha256:hash(body)},execution_authorization:'DENIED',execution_authorized:false};
}
export function replayArchive(archive){
 try{const {record_sha256,...body}=archive;if(hash(body)!==record_sha256)return denied('REPLAY_UNAVAILABLE','ARCHIVE_INTEGRITY');if(canonical(body.dependencies)!==canonical(dependencies()))return denied('REPLAY_UNAVAILABLE','HISTORICAL_DEPENDENCIES_UNAVAILABLE');const reproduced=evaluateSession(body.input);return {status:canonical(reproduced)===canonical(body.assessment)?'REPLAY_MATCH':'REPLAY_MISMATCH',reproduced,original_record_sha256:record_sha256,execution_authorization:'DENIED',execution_authorized:false};}catch{return denied('REPLAY_UNAVAILABLE','MALFORMED_ARCHIVE');}
}
