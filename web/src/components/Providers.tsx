'use client';

import { ReactNode } from 'react';
import { ThemeProvider } from 'next-themes';
import { AuthProvider } from '@/contexts/AuthContext';
import { ProjectProvider } from '@/contexts/ProjectContext';

interface ProvidersProps {
    children: ReactNode;
}

export function Providers({ children }: ProvidersProps) {
    return (
        <ThemeProvider
            attribute="data-theme"
            defaultTheme="dark"
            themes={['light', 'dark']}
            enableSystem={false}
            disableTransitionOnChange
            storageKey="app-theme"
        >
            <AuthProvider>
                <ProjectProvider>
                    {children}
                </ProjectProvider>
            </AuthProvider>
        </ThemeProvider>
    );
}
