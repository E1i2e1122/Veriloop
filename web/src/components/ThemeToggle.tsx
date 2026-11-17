'use client';

import { useEffect, useState } from 'react';
import { useTheme } from 'next-themes';
import { Moon, Sun } from 'lucide-react';

interface ThemeToggleProps {
    className?: string;
}

/** Switches between the light and dark themes; the choice is remembered per browser. */
export function ThemeToggle({ className = '' }: ThemeToggleProps) {
    const { resolvedTheme, setTheme } = useTheme();
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
    }, []);

    // Until mounted the theme is unknown on the server; render the default (dark) state.
    const isDark = !mounted || resolvedTheme !== 'light';
    const next = isDark ? 'light' : 'dark';

    return (
        <button
            type="button"
            className={`theme-toggle ${className}`.trim()}
            onClick={() => setTheme(next)}
            aria-label={`Switch to ${next} theme`}
            title={`Switch to ${next} theme`}
        >
            {isDark ? <Sun size={15} aria-hidden="true" /> : <Moon size={15} aria-hidden="true" />}
        </button>
    );
}
