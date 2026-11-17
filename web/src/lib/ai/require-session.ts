import { NextResponse } from 'next/server';
import { backendFetch } from './backend-client';

type AuthStatus = {
  require_auth: boolean;
  authenticated: boolean;
  user_id: string | null;
  is_superuser: boolean;
};

export function bearerToken(req: Request): string | undefined {
  const header = req.headers.get('authorization') || '';
  const [scheme, token] = header.split(' ');
  return scheme?.toLowerCase() === 'bearer' && token ? token : undefined;
}

/**
 * Rejects anonymous callers when the backend enforces authentication, so server-side
 * routes never spend LLM tokens or run assistant actions for unauthenticated users.
 *
 * Returns a response to send back, or null when the request may proceed.
 */
export async function requireBackendSession(authToken?: string): Promise<NextResponse | null> {
  const status = await backendFetch<AuthStatus>('/auth/status', { authToken, timeoutMs: 5000 });
  if (!status.ok || !status.data) {
    return NextResponse.json({ error: 'Could not verify your session. Please try again.' }, { status: 503 });
  }
  if (status.data.require_auth && !status.data.authenticated) {
    return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
  }
  return null;
}
