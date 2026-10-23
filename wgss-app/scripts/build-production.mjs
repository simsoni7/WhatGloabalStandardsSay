import {spawnSync} from 'node:child_process';
import {readdir,readFile,writeFile,unlink,mkdir} from 'node:fs/promises';
import {resolve,join} from 'node:path';
import {gzipSync,gunzipSync} from 'node:zlib';
import {createHash} from 'node:crypto';
import {canonicalWorkspaceScript,canonicalWorkspaceDocument} from '../lib/canonical-workspace.mjs';
// Sites can serve a static index before invoking the framework Worker.
// The asset entry must therefore lead to the same canonical workspace too.
const entry=canonicalWorkspaceScript();
await mkdir('public/workspace',{recursive:true});
await writeFile('public/workspace/canonical-entry.js',entry);
await writeFile('public/workspace/index.html',canonicalWorkspaceDocument(createHash('sha256').update(entry).digest('hex').slice(0,16)));
const indexed=spawnSync(process.execPath,['scripts/build-reference-index.mjs'],{stdio:'inherit'});
if(indexed.status!==0)process.exit(indexed.status||1);
const built=spawnSync(process.execPath,['scripts/run-framework.mjs','build'],{stdio:'inherit'});
if(built.status!==0)process.exit(built.status||1);
// The source files stay literal. Only the transport representation in build output changes.
const root=resolve('dist/client');await unlink(join(root,'_headers')).catch(e=>{if(e.code!=='ENOENT')throw e;});let before=0,after=0,count=0;
async function visit(dir){for(const e of await readdir(dir,{withFileTypes:true})){const p=join(dir,e.name);if(e.isDirectory())await visit(p);else if(e.name.endsWith('.json')){const raw=await readFile(p);JSON.parse(raw.toString('utf8'));const packed=gzipSync(raw,{level:9});if(!gunzipSync(packed).equals(raw))throw Error('JSON transport byte mismatch');await writeFile(p+'.gz',packed);await unlink(p);before+=raw.length;after+=packed.length;count++;}}}
await visit(root);
console.log(JSON.stringify({jsonTransport:'gzip',files:count,uncompressedBytes:before,transportBytes:after,decodedBytesVerified:true}));
