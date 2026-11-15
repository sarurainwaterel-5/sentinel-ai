// Test preloader only. Import before the harness and its consumers.
import net from 'node:net';
import http from 'node:http';
import https from 'node:https';
import dns from 'node:dns';
import {syncBuiltinESMExports} from 'node:module';
const denied=()=>{throw Error('NETWORK_DISABLED_FOR_SYNTHETIC_TEST');};
net.connect=net.createConnection=denied;net.Socket.prototype.connect=denied;
http.request=http.get=https.request=https.get=denied;
dns.lookup=dns.resolve=denied;dns.promises.lookup=dns.promises.resolve=denied;
globalThis.fetch=denied;syncBuiltinESMExports();
