'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { Loader2, AlertCircle, Eye, EyeOff, Mail, Lock, User, Check, X } from 'lucide-react';

interface RegisterFormProps {
    redirectTo?: string;
}

interface PasswordRequirement {
    label: string;
    test: (password: string) => boolean;
}

const passwordRequirements: PasswordRequirement[] = [
    { label: 'At least 8 characters', test: (p) => p.length >= 8 },
    { label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
    { label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
    { label: 'One number', test: (p) => /\d/.test(p) },
    { label: 'One special character', test: (p) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
];

export function RegisterForm({ redirectTo = '/' }: RegisterFormProps) {
    const router = useRouter();
    const { register } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const allRequirementsMet = passwordRequirements.every((req) => req.test(password));
    const passwordsMatch = password === confirmPassword && password.length > 0;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!allRequirementsMet) {
            setError('Password does not meet all requirements');
            return;
        }

        if (!passwordsMatch) {
            setError('Passwords do not match');
            return;
        }

        setIsLoading(true);

        try {
            await register(email, password, fullName || undefined);
            router.push(redirectTo);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Registration failed');
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
                    <label htmlFor="fullName" className="form-label">
                        Full name <span className="form-label-optional">(optional)</span>
                    </label>
                    <div className="input-group">
                        <span className="input-icon" aria-hidden="true"><User size={16} /></span>
                        <input
                            id="fullName"
                            type="text"
                            className="form-input"
                            placeholder="Jane Doe"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            autoComplete="name"
                            disabled={isLoading}
                        />
                    </div>
                </div>

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
                            placeholder="Create a strong password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            autoComplete="new-password"
                            disabled={isLoading}
                            aria-describedby="password-requirements"
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
                    {password.length > 0 && (
                        <ul className="password-reqs" id="password-requirements" aria-label="Password requirements">
                            {passwordRequirements.map((req) => {
                                const met = req.test(password);
                                return (
                                    <li key={req.label} className={`password-req${met ? ' is-met' : ''}`}>
                                        {met ? <Check size={12} aria-hidden="true" /> : <X size={12} aria-hidden="true" />}
                                        {req.label}
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </div>

                <div className="form-field">
                    <label htmlFor="confirmPassword" className="form-label">Confirm password</label>
                    <div className="input-group">
                        <span className="input-icon" aria-hidden="true"><Lock size={16} /></span>
                        <input
                            id="confirmPassword"
                            type="password"
                            className="form-input"
                            placeholder="Repeat your password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                            autoComplete="new-password"
                            disabled={isLoading}
                            aria-invalid={confirmPassword.length > 0 && !passwordsMatch}
                        />
                    </div>
                    {confirmPassword.length > 0 && !passwordsMatch && (
                        <p className="form-error-text">Passwords do not match</p>
                    )}
                </div>

                <button
                    type="submit"
                    className="btn btn-primary auth-submit"
                    disabled={isLoading || !allRequirementsMet || !passwordsMatch}
                >
                    {isLoading ? (
                        <>
                            <Loader2 size={16} className="animate-spin" aria-hidden="true" />
                            Creating account…
                        </>
                    ) : (
                        'Create account'
                    )}
                </button>
            </form>

            <p className="auth-footer">
                Already have an account? <Link href="/login">Sign in</Link>
            </p>
        </>
    );
}
