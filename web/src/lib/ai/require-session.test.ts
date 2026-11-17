import { beforeEach, describe, expect, it, vi } from 'vitest';

import { backendFetch } from './backend-client';
import { bearerToken, requireBackendSession } from './require-session';

vi.mock('./backend-client', () => ({
  backendFetch: vi.fn(),
}));

const mockBackendFetch = vi.mocked(backendFetch);

function authStatus(requireAuth: boolean, authenticated: boolean) {
  return {
    ok: true,
    status: 200,
    data: { require_auth: requireAuth, authenticated, user_id: authenticated ? 'u1' : null, is_superuser: false },
  };
}

describe('requireBackendSession', () => {
  beforeEach(() => {
    mockBackendFetch.mockReset();
  });

  it('rejects anonymous callers when the backend enforces auth', async () => {
    mockBackendFetch.mockResolvedValue(authStatus(true, false));
    const response = await requireBackendSession(undefined);
    expect(response?.status).toBe(401);
  });

  it('allows authenticated callers', async () => {
    mockBackendFetch.mockResolvedValue(authStatus(true, true));
    await expect(requireBackendSession('token-a')).resolves.toBeNull();
    expect(mockBackendFetch).toHaveBeenCalledWith('/auth/status', { authToken: 'token-a', timeoutMs: 5000 });
  });

  it('allows anonymous callers when auth is disabled (local development)', async () => {
    mockBackendFetch.mockResolvedValue(authStatus(false, false));
    await expect(requireBackendSession(undefined)).resolves.toBeNull();
  });

  it('fails closed when the session cannot be verified', async () => {
    mockBackendFetch.mockResolvedValue({ ok: false, status: 0, error: 'Backend unreachable' });
    const response = await requireBackendSession('token-a');
    expect(response?.status).toBe(503);
  });
});

describe('bearerToken', () => {
  it('extracts bearer tokens case-insensitively', () => {
    expect(bearerToken(new Request('http://x', { headers: { Authorization: 'Bearer abc' } }))).toBe('abc');
    expect(bearerToken(new Request('http://x', { headers: { Authorization: 'bearer abc' } }))).toBe('abc');
  });

  it('ignores missing or non-bearer credentials', () => {
    expect(bearerToken(new Request('http://x'))).toBeUndefined();
    expect(bearerToken(new Request('http://x', { headers: { Authorization: 'Basic abc' } }))).toBeUndefined();
  });
});
