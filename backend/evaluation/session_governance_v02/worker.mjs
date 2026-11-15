// Test-only process-restart driver. Private files avoid unreliable piped child stdout.
import {readFileSync,writeFileSync} from 'node:fs';import {archiveDecision,replayArchive}from './archive.mjs';
const [action,input,reply]=process.argv.slice(2),value=JSON.parse(readFileSync(input,'utf8'));
const result=action==='record'?archiveDecision(value):replayArchive(value);
writeFileSync(reply,JSON.stringify(result),{flag:'wx',mode:0o600});
