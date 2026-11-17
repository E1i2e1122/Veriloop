'use client';

import { useEffect, useState } from 'react';
import { usePathname } from 'next/navigation';
import { Menu, X } from 'lucide-react';
import { Sidebar } from '@/components/Sidebar';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ChatProvider } from '@/components/assistant/ChatProvider';
import { ChatBubble } from '@/components/assistant/ChatBubble';
import { CommandPaletteProvider } from '@/components/command-palette/CommandPaletteProvider';
import { CommandPalette } from '@/components/command-palette/CommandPalette';
import { NextStepBanner } from '@/components/workflow/NextStepBanner';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const [navOpen, setNavOpen] = useState(false);

    // Close the mobile navigation drawer after navigating.
    useEffect(() => {
        setNavOpen(false);
    }, [pathname]);

    useEffect(() => {
        if (!navOpen) return;
        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') setNavOpen(false);
        };
        window.addEventListener('keydown', onKeyDown);
        return () => window.removeEventListener('keydown', onKeyDown);
    }, [navOpen]);

    return (
        <ProtectedRoute>
            <ChatProvider>
                <CommandPaletteProvider>
                    <div className="dashboard-shell">
                        <div id="dashboard-navigation" className={`dashboard-sidebar${navOpen ? ' is-open' : ''}`}>
                            <Sidebar />
                        </div>
                        {navOpen && (
                            <div className="dashboard-nav-backdrop" aria-hidden="true" onClick={() => setNavOpen(false)} />
                        )}
                        <main className="dashboard-main">
                            <header className="mobile-topbar">
                                <button
                                    type="button"
                                    className="btn-icon"
                                    aria-label={navOpen ? 'Close navigation' : 'Open navigation'}
                                    aria-expanded={navOpen}
                                    aria-controls="dashboard-navigation"
                                    onClick={() => setNavOpen((open) => !open)}
                                >
                                    {navOpen ? <X size={20} /> : <Menu size={20} />}
                                </button>
                                <span className="mobile-topbar-brand">
                                    <img src="/logo.svg" alt="" width={24} height={24} />
                                    Veriloop
                                </span>
                                <ThemeToggle className="mobile-topbar-theme" />
                            </header>
                            <NextStepBanner />
                            {children}
                        </main>
                    </div>
                    {/* The assistant page already hosts the full chat, so the floating button is hidden there */}
                    {pathname !== '/assistant' && <ChatBubble />}
                    <CommandPalette />
                </CommandPaletteProvider>
            </ChatProvider>
        </ProtectedRoute>
    );
}
