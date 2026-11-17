/**
 * Shared color utilities for severity levels, statuses, and metric thresholds.
 *
 * Every color resolves through the design tokens in `globals.css`, so the same
 * value renders correctly in both the dark and the light theme.
 */

/**
 * Returns `color` at the given opacity (0-1).
 *
 * Works for hex values and CSS custom properties alike (e.g. `var(--success)`),
 * which plain hex-alpha concatenation (`${color}1a`) does not.
 */
export function alpha(color: string, opacity: number): string {
    const pct = Math.round(Math.min(Math.max(opacity, 0), 1) * 1000) / 10;
    return `color-mix(in srgb, ${color} ${pct}%, transparent)`;
}

const NEUTRAL = 'var(--text-secondary)';

const SEVERITY_COLORS: Record<string, string> = {
    critical: 'var(--danger)',
    high: 'var(--orange)',
    medium: 'var(--warning)',
    low: 'var(--primary)',
    info: NEUTRAL,
};

const STATUS_COLORS: Record<string, string> = {
    pending: NEUTRAL,
    running: 'var(--primary)',
    completed: 'var(--success)',
    failed: 'var(--danger)',
    passed: 'var(--success)',
    error: 'var(--orange)',
    cancelled: 'var(--accent)',
};

export function severityColor(severity: string): string {
    return SEVERITY_COLORS[severity?.toLowerCase()] || NEUTRAL;
}

export function severityBg(severity: string): string {
    return alpha(severityColor(severity), 0.12);
}

export function statusColor(status: string): string {
    return STATUS_COLORS[status?.toLowerCase()] || NEUTRAL;
}

export function getResponseTimeColor(ms: number): string {
    if (ms < 200) return 'var(--success)';
    if (ms < 500) return 'var(--warning)';
    return 'var(--danger)';
}

export function getErrorRateColor(rate: number): string {
    if (rate < 1) return 'var(--success)';
    if (rate < 5) return 'var(--warning)';
    return 'var(--danger)';
}

export function getStatusColor(code: string): string {
    if (code.startsWith('2')) return 'var(--success)';
    if (code.startsWith('3')) return 'var(--primary)';
    if (code.startsWith('4')) return 'var(--warning)';
    if (code.startsWith('5')) return 'var(--danger)';
    return NEUTRAL;
}
