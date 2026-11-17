import { describe, expect, it } from 'vitest';
import { safeRedirectPath } from './safe-redirect';

describe('safeRedirectPath', () => {
    it('keeps same-origin relative paths with query and hash', () => {
        expect(safeRedirectPath('/specs?tab=all#top')).toBe('/specs?tab=all#top');
        expect(safeRedirectPath('/runs/123')).toBe('/runs/123');
    });

    it.each([
        'https://evil.example/phish',
        '//evil.example',
        '/\\evil.example',
        'javascript:alert(1)',
        'specs',
        '',
        null,
        undefined,
    ])('falls back for unsafe value %s', (value) => {
        expect(safeRedirectPath(value)).toBe('/');
    });

    it('supports a custom fallback', () => {
        expect(safeRedirectPath('https://evil.example', '/dashboard')).toBe('/dashboard');
    });
});
