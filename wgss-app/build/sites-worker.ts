import handler from "vinext/server/fetch-handler";
import { runWithConnectorBinding } from "../lib/connector-context";
import type { ConnectorBinding } from "../lib/connector-contract.mjs";

export default {
  async fetch(request: Request, env: Cloudflare.Env, ctx: ExecutionContext<{ CONNECTORS?: ConnectorBinding }>) {
    const assetPath = new URL(request.url).pathname;
    // Public source JSON stays byte-identical; build output keeps a gzip carrier.
    // Decode the carrier as a stream and let Workers negotiate HTTP compression.
    const jsonPrefixes = ['/integration-data/', '/data/', '/evidence/', '/review/', '/runtime-v40/'];
    if (!import.meta.env.DEV && assetPath.endsWith('.json') && jsonPrefixes.some(prefix => assetPath.startsWith(prefix))) {
      const assets = (env as unknown as {ASSETS?: {fetch(request: Request): Promise<Response>}}).ASSETS;
      if (!assets) return new Response('Asset binding unavailable', {status: 503});
      const packed = await assets.fetch(new Request(new URL(assetPath + '.gz', request.url)));
      if (!packed.ok || !packed.body) return new Response('Not found', {status: 404});
      return new Response(request.method === 'HEAD' ? null : packed.body.pipeThrough(new DecompressionStream('gzip')), {
        headers: {'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'private, max-age=0, must-revalidate', 'X-Content-Type-Options': 'nosniff'},
      });
    }
    let binding = ctx.props?.CONNECTORS;
    // Local preview emulates the same request-scoped capability. This branch and
    // the auxiliary service binding are absent from production builds.
    if (import.meta.env.DEV && !binding && env.CONNECTORS) {
      const preview = env.CONNECTORS;
      const expiresAt = Date.now() + 60_000;
      binding = {
        async getContext() {
          if (Date.now() >= expiresAt) return { status: "request_context_expired" };
          return preview.getContext?.() ?? { status: "binding_unavailable" };
        },
        async invoke(connectorId, actionName, args) {
          if (Date.now() >= expiresAt) {
            return { status: "request_context_expired", message: "This request has expired. Please try again." };
          }
          return preview.invoke(connectorId, actionName, args);
        },
      };
    }
    return runWithConnectorBinding(binding, () => handler.fetch(request, env, ctx));
  },
};
