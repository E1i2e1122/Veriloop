import './globals.css';
import localFont from 'next/font/local';
import { Providers } from '@/components/Providers';
import { Toaster } from '@/components/ui/sonner';

// Fonts are bundled from npm (@fontsource-variable) instead of downloaded from Google
// at build time, so builds work in restricted or air-gapped networks.
const sora = localFont({
    src: '../../node_modules/@fontsource-variable/sora/files/sora-latin-wght-normal.woff2',
    variable: '--font-sora',
    display: 'swap',
    weight: '100 800',
});

const jetbrainsMono = localFont({
    src: '../../node_modules/@fontsource-variable/jetbrains-mono/files/jetbrains-mono-latin-wght-normal.woff2',
    variable: '--font-jetbrains-mono',
    display: 'swap',
    weight: '100 800',
});

export const metadata = {
    title: 'Veriloop',
    description: 'Autonomous AI Test Automation',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" suppressHydrationWarning className={`${sora.variable} ${jetbrainsMono.variable}`}>
            <body>
                <Providers>
                    {children}
                    <Toaster position="bottom-right" />
                </Providers>
            </body>
        </html>
    );
}
