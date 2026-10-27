import {imageMime} from './images';
import {preparePublications} from './publications';
import {ApiError, Runtime, Actor, requireActor, actorId, now, id, stmt, rows, bounded, content, auditStmt, hash, submission, serializeSubmission} from './core';

export async function createSubmission(env: Runtime, actor: Actor, input: any) {
  requireActor(actor); if (!['translation_issue','text','screen'].includes(input.kind)) throw new ApiError(400,'invalid_kind','Choose translation_issue, text, or screen.');
  const external=actor.service&&actor.userId==='wgss-bedrock-quality-agent'&&/^[0-9a-f]{64}$/.test(input.candidateKey||'')?'auto-'+input.candidateKey:null;
  if(external){const prior=await stmt(env,'SELECT * FROM wgss_submissions WHERE id=?',external).first<any>();if(prior)return {item:await serializeSubmission(env,prior),reused:true};}
  const sid = external||id(), time = now(), title = bounded(input.title,'title',300,true), data = JSON.stringify(content(input));
  await env.DB.batch([
    stmt(env,'INSERT INTO wgss_submissions (id,owner_id,kind,status,version,title,content_json,created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?)',sid,actorId(actor),input.kind,'pending',1,title,data,time,time),
    stmt(env,'INSERT INTO wgss_versions (id,submission_id,version,title,content_json,status,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?)',id(),sid,1,title,data,'pending',actorId(actor),time),
    auditStmt(env,actor,'submission.created',sid,{kind:input.kind}),
  ]); return {item:await serializeSubmission(env,await submission(env,actor,sid))};
}
export async function updateSubmission(env: Runtime, actor: Actor, input: any, review: boolean) {
  const sid = bounded(input.id,'id',100,true), old = await submission(env,actor,sid,review);
  if (old.status === 'deleting') throw new ApiError(409,'deletion_in_progress','Deletion is in progress.');
  if (!Number.isInteger(input.expectedVersion) || input.expectedVersion !== old.version) throw new ApiError(409,'version_conflict','The submission changed. Reload and try again.');
  let status = 'pending', title = old.title, data = old.content_json, privacy = 0, readability = 0;
  const extra = [];
  if (review) {
    if (!['approved','held','rejected'].includes(input.decision)) throw new ApiError(400,'invalid_decision','Choose approved, held, or rejected.');
    bounded(input.reason,'reason',2000);
    status = input.decision; privacy = input.privacyReviewed === true ? 1 : 0; readability = input.readabilityReviewed === true ? 1 : 0;
    if (status === 'approved' && (!privacy || !readability)) throw new ApiError(400,'review_required','Privacy and readability review are required for approval.');
    if (input.maskedFileIds !== undefined && !Array.isArray(input.maskedFileIds)) throw new ApiError(400,'invalid_files','Choose derivative files as a list.');
    const selectedFiles: string[] = Array.isArray(input.maskedFileIds) ? input.maskedFileIds : input.maskedFileId ? [input.maskedFileId] : [];
    if (selectedFiles.length > 10 || selectedFiles.some(fid => typeof fid !== 'string' || !fid || fid.length > 100) || new Set(selectedFiles).size !== selectedFiles.length) throw new ApiError(400,'invalid_files','Choose up to ten distinct derivative files.');
    for (const selectedFileId of selectedFiles) {
      const file = await stmt(env,'SELECT * FROM wgss_files WHERE id=? AND submission_id=?',selectedFileId,sid).first<any>();
      if (!file || file.role !== 'masked') throw new ApiError(400,'masked_derivative_required','Choose an uploaded masked derivative.');
      if (!privacy || !readability) throw new ApiError(400,'review_required','Review the exact derivative for privacy and readability.');
      // Re-read object and bind approval to the exact immutable uploaded bytes.
      const object = await env.BUCKET.get(file.object_key); if (!object || await hash(await object.arrayBuffer()) !== file.sha256) throw new ApiError(409,'file_integrity','The derivative bytes could not be verified.');
      extra.push(stmt(env,'UPDATE wgss_files SET review_status=?,reviewed_sha256=? WHERE id=? AND sha256=?','approved',file.sha256,file.id,file.sha256));
    }
    if (status === 'approved' && old.kind === 'screen') {
      const prior = await stmt(env,"SELECT id FROM wgss_files WHERE submission_id=? AND role='masked' AND review_status='approved' AND reviewed_sha256=sha256",sid).first();
      if (!selectedFiles.length && !prior) throw new ApiError(400,'masked_derivative_required','A reviewed masked derivative is required to approve a screen.');
    }
  } else {
    if (actor.role !== 'admin' && old.status === 'approved') throw new ApiError(403,'admin_required','An administrator must revise an approved reference.');
    title = input.title == null ? old.title : bounded(input.title,'title',300,true);
    data = JSON.stringify(content({...JSON.parse(old.content_json),...input}));
    // A changed source invalidates all prior derivative approvals.
    extra.push(stmt(env,"UPDATE wgss_files SET review_status='pending',reviewed_sha256=NULL WHERE submission_id=?",sid));
  }
  const next = old.version + 1, time = now();
  const application = review && status === 'approved' ? await preparePublications(env,actor,old,input,Array.isArray(input.maskedFileIds)?input.maskedFileIds:input.maskedFileId?[input.maskedFileId]:[],next) : {statements:[],entries:[]};
  try {
    await env.DB.batch([
      stmt(env,'INSERT INTO wgss_versions (id,submission_id,version,title,content_json,status,actor_id,created_at,review_reason) VALUES (?,?,?,?,?,?,?,?,?)',id(),sid,next,title,data,status,actorId(actor),time,review?bounded(input.reason,'reason',2000):null),
      stmt(env,'UPDATE wgss_submissions SET version=?,title=?,content_json=?,status=?,privacy_reviewed=?,readability_reviewed=?,updated_at=? WHERE id=? AND version=?',next,title,data,status,privacy,readability,time,sid,old.version),
      ...extra,
      ...application.statements,
      auditStmt(env,actor,review?'submission.reviewed':'submission.versioned',sid,{version:next,decision:status,applied:application.entries}),
    ]);
  } catch { throw new ApiError(409,'version_conflict','The submission changed. Reload and try again.'); }
  return {item:await serializeSubmission(env,await submission(env,actor,sid))};
}
export async function upload(env: Runtime, actor: Actor, form: FormData) {
  requireActor(actor); const sid = bounded(form.get('submissionId'),'submissionId',100,true), source = await submission(env,actor,sid);
  if (source.status === 'deleting') throw new ApiError(409,'deletion_in_progress','Deletion is in progress.');
  if (source.status === 'approved') throw new ApiError(409,'version_required','Create a new version before adding a file to an approved reference.');
  const file = form.get('file'); if (!file || typeof file === 'string') throw new ApiError(400,'file_required','Choose an image.');
  const role = form.get('role'); if (!['original','masked'].includes(String(role))) throw new ApiError(400,'invalid_role','File role must be original or masked.');
  if (file.size < 16 || file.size > 8*1024*1024) throw new ApiError(413,'file_size','Images must be between 16 bytes and 8 MB.');
  const bytes = await file.arrayBuffer(), view = new Uint8Array(bytes);
  const mime = imageMime(view);
  if (!mime || file.type !== mime) throw new ApiError(415,'invalid_image','Only correctly identified PNG, JPEG, or WebP images are accepted.');
  const requestedId = bounded(form.get('clientUploadId'),'clientUploadId',36);
  if (requestedId && !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(requestedId)) throw new ApiError(400,'invalid_upload_id','Invalid upload identifier.');
  const fid = requestedId || id(), digest = await hash(bytes);
  if (requestedId) {
    const existing = await stmt(env,'SELECT * FROM wgss_files WHERE id=?',fid).first<any>();
    if (existing) {
      if (existing.submission_id !== sid || existing.sha256 !== digest || existing.role !== role) throw new ApiError(409,'upload_conflict','This upload identifier belongs to different image bytes.');
      return {item:await serializeSubmission(env,await submission(env,actor,sid)),reused:true};
    }
  }
  if ((await rows(env,'SELECT id FROM wgss_files WHERE submission_id=?',sid)).length >= 10) throw new ApiError(400,'file_limit','At most ten images per submission.');
  // A distinct object key keeps a losing concurrent retry from overwriting or deleting the winner's image.
  const key = `quarantine/${sid}/${id()}`;
  await env.BUCKET.put(key,bytes,{httpMetadata:{contentType:mime},customMetadata:{sha256:digest}});
  try { await env.DB.batch([
    stmt(env,'INSERT INTO wgss_versions (id,submission_id,version,title,content_json,status,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?)',id(),sid,source.version+1,source.title,source.content_json,'pending',actorId(actor),now()),
    stmt(env,"UPDATE wgss_submissions SET version=?,status='pending',privacy_reviewed=0,readability_reviewed=0,updated_at=? WHERE id=? AND version=?",source.version+1,now(),sid,source.version),
    stmt(env,"UPDATE wgss_files SET review_status='pending',reviewed_sha256=NULL WHERE submission_id=?",sid),
    stmt(env,'INSERT INTO wgss_files (id,submission_id,object_key,sha256,mime,size,role,review_status,created_at) VALUES (?,?,?,?,?,?,?,?,?)',fid,sid,key,digest,mime,file.size,role,'pending',now()),
    auditStmt(env,actor,'file.quarantined',sid,{fileId:fid,sha256:digest,role,version:source.version+1})
  ]); }
  catch (error) { await env.BUCKET.delete(key); throw error; }
  return {item:await serializeSubmission(env,await submission(env,actor,sid))};
}
export async function deleteSubmission(env: Runtime, actor: Actor, input: any) {
  const old = await submission(env,actor,bounded(input.id,'id',100,true));
  if (input.expectedVersion !== old.version) throw new ApiError(409,'version_conflict','Reload the current version before deleting.');
  // Claim the next immutable version before touching R2. Concurrent source edits,
  // reviews, and uploads share the same unique version constraint.
  if (old.status !== 'deleting') {
    try { await env.DB.batch([
      stmt(env,'INSERT INTO wgss_versions (id,submission_id,version,title,content_json,status,actor_id,created_at) VALUES (?,?,?,?,?,?,?,?)',id(),old.id,old.version+1,'','{}','deleting',actorId(actor),now()),
      stmt(env,"UPDATE wgss_submissions SET version=?,status='deleting',privacy_reviewed=0,readability_reviewed=0,updated_at=? WHERE id=? AND version=?",old.version+1,now(),old.id,old.version),
    ]); } catch { throw new ApiError(409,'version_conflict','The submission changed. Reload and retry deletion.'); }
  }
  const fs = await rows(env,'SELECT object_key FROM wgss_files WHERE submission_id=?',old.id);
  // A failed storage purge leaves a deleting record that can be retried safely.
  if(fs.length)await env.BUCKET.delete(fs.map(f=>f.object_key));
  await env.DB.batch([
    stmt(env,"UPDATE wgss_publications SET source_submission_id=NULL,patch_json='{}',state='purged',actor_id='' WHERE source_submission_id=?",old.id),
    stmt(env,'DELETE FROM wgss_files WHERE submission_id=?',old.id),stmt(env,'DELETE FROM wgss_versions WHERE submission_id=?',old.id),
    stmt(env,'DELETE FROM wgss_jobs WHERE submission_id=?',old.id),stmt(env,'DELETE FROM wgss_submissions WHERE id=?',old.id),
    stmt(env,'DELETE FROM wgss_audit WHERE entity_id=?',old.id),auditStmt(env,actor,'submission.deleted',old.id,{mediaPurged:true}),
  ]);
  return {deleted:true};
}
