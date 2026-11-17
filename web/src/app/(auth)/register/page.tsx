'use client';

import { useSearchParams, useRouter } from 'next/navigation';
import { Suspense, useEffect } from 'react';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { AuthLoading, AuthShell } from '@/components/auth/AuthShell';
import { useAuth } from '@/contexts/AuthContext';
import { safeRedirectPath } from '@/lib/safe-redirect';

function RegisterContent() {
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
        <AuthShell title="Create your account" subtitle="Start automating your tests in minutes">
            <RegisterForm redirectTo={returnTo} />
        </AuthShell>
    );
}

export default function RegisterPage() {
    return (
        <Suspense fallback={<AuthLoading />}>
            <RegisterContent />
        </Suspense>
    );
}
