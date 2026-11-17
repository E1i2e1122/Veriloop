/**
 * Return a same-origin relative path that is safe to redirect to after login,
 * or the fallback. Rejects absolute URLs, protocol-relative URLs (`//evil.com`),
 * and backslash tricks (`/\evil.com`) to prevent open redirects.
 */
export function safeRedirectPath(value: string | null | undefined, fallback = '/'): string {
    if (!value || !value.startsWith('/') || value.startsWith('//') || value.startsWith('/\\')) {
        return fallback;
    }
    try {
        const base = 'http://local.invalid';
        const parsed = new URL(value, base);
        if (parsed.origin !== base) return fallback;
        return `${parsed.pathname}${parsed.search}${parsed.hash}`;
    } catch {
        return fallback;
    }
}
