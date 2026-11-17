'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useEffect } from 'react';
import { LoginForm } from '@/components/auth/LoginForm';
import { AuthLoading, AuthShell } from '@/components/auth/AuthShell';
import { useAuth } from '@/contexts/AuthContext';
import { safeRedirectPath } from '@/lib/safe-redirect';

function LoginContent() {
    const searchParams = useSearchParams();
    const router = useRouter();
    const { isAuthenticated, isLoading } = useAuth();
    const returnTo = safeRedirectPath(searchParams.get('returnTo'));

    // Redirect away once a session exists
    useEffect(() => {
        if (!isLoading && isAuthenticated) {
            router.push(returnTo);
        }
    }, [isAuthenticated, isLoading, router, returnTo]);

    if (isLoading || isAuthenticated) {
        return <AuthLoading />;
    }

    return (
        <AuthShell title="Welcome back" subtitle="Sign in to your account to continue">
            <LoginForm redirectTo={returnTo} />
        </AuthShell>
    );
}

export default function LoginPage() {
    return (
        <Suspense fallback={<AuthLoading />}>
            <LoginContent />
        </Suspense>
    );
}
