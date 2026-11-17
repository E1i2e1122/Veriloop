'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, AlertCircle, Eye, EyeOff, Mail, Lock } from 'lucide-react';

interface LoginFormProps {
    redirectTo?: string;
}

export function LoginForm({ redirectTo = '/' }: LoginFormProps) {
    const router = useRouter();
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setIsLoading(true);

        try {
            await login(email, password);
            router.push(redirectTo);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Login failed');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <form onSubmit={handleSubmit} className="auth-form">
                {error && (
                    <div className="form-alert" role="alert">
                        <AlertCircle size={16} aria-hidden="true" />
                        <span>{error}</span>
                    </div>
                )}

                <div className="form-field">
                    <label htmlFor="email" className="form-label">Email</label>
                    <div className="input-group">
                        <span className="input-icon" aria-hidden="true"><Mail size={16} /></span>
                        <input
                            id="email"
                            type="email"
                            className="form-input"
                            placeholder="you@example.com"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                            autoComplete="email"
                            autoFocus
                            disabled={isLoading}
                        />
                    </div>
                </div>

                <div className="form-field">
                    <label htmlFor="password" className="form-label">Password</label>
                    <div className="input-group">
                        <span className="input-icon" aria-hidden="true"><Lock size={16} /></span>
                        <input
                            id="password"
                            type={showPassword ? 'text' : 'password'}
                            className="form-input has-action"
                            placeholder="Enter your password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="current-password"
                            disabled={isLoading}
                        />
                        <button
                            type="button"
                            className="input-action"
                            onClick={() => setShowPassword((visible) => !visible)}
                            aria-label={showPassword ? 'Hide password' : 'Show password'}
                            aria-pressed={showPassword}
                        >
                            {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                    </div>
                </div>

                <button type="submit" className="btn btn-primary auth-submit" disabled={isLoading}>
                    {isLoading ? (
                        <>
                            <Loader2 size={16} className="animate-spin" aria-hidden="true" />
                            Signing in…
                        </>
                    ) : (
                        'Sign in'
                    )}
                </button>
            </form>

            <p className="auth-footer">
                Don&apos;t have an account? <Link href="/register">Create one</Link>
            </p>
        </>
    );
}
