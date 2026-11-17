'use client';

import type { ReactNode } from 'react';
import { Loader2 } from 'lucide-react';
import { ThemeToggle } from '@/components/ThemeToggle';

interface AuthShellProps {
    title: string;
    subtitle?: string;
    children: ReactNode;
}

/** Shared layout for the sign-in and registration screens. */
export function AuthShell({ title, subtitle, children }: AuthShellProps) {
    return (
        <div className="auth-shell">
            <div className="auth-shell-toolbar">
                <ThemeToggle />
            </div>
            <main className="auth-container">
                <div className="auth-card">
                    <div className="auth-brand">
                        <img src="/logo.svg" alt="" className="auth-brand-mark" width={52} height={52} />
                        <div className="auth-brand-name">Veriloop</div>
                        <h1 className="auth-title">{title}</h1>
                        {subtitle && <p className="auth-subtitle">{subtitle}</p>}
                    </div>
                    <div className="auth-divider" />
                    {children}
                </div>
                <p className="auth-legal">Autonomous AI Test Automation</p>
            </main>
        </div>
    );
}

/** Full-screen loading state used while the session is checked or a redirect is pending. */
export function AuthLoading() {
    return (
        <div className="auth-shell" role="status" aria-live="polite">
            <div className="auth-loading-inner">
                <img src="/logo.svg" alt="" width={48} height={48} className="auth-brand-mark" />
                <div className="auth-loading-label">
                    <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                    <span>Loading…</span>
                </div>
            </div>
        </div>
    );
}
