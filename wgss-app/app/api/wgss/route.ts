import { env } from 'cloudflare:workers';
import { getChatGPTUser } from '../../chatgpt-auth';
import { getActor, type Runtime } from '../../../server/wgss/core';
import { handleRequest } from '../../../server/wgss/api';

export const dynamic = 'force-dynamic';
async function handle(request: Request) {
  const runtime = env as unknown as Runtime;
  const user = await getChatGPTUser();
  return handleRequest(request, runtime, getActor(user?.userId || null, runtime, user?.email || null));
}
export const GET = handle;
export const POST = handle;
