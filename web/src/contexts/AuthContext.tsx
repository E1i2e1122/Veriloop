'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { API_BASE } from '@/lib/api';

export interface User {
    id: string;
    email: string;
    full_name: string | null;
    is_active: boolean;
    is_superuser: boolean;
    email_verified: boolean;
    created_at: string;
    last_login: string | null;
}

interface AuthContextType {
    user: User | null;
    isLoading: boolean;
    isAuthenticated: boolean;
    login: (email: string, password: string) => Promise<void>;
    register: (email: string, password: string, fullName?: string) => Promise<void>;
    logout: () => Promise<void>;
    refreshAccessToken: () => Promise<boolean>;
    getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | null>(null);

// Store access token in memory (not localStorage for security)
let accessToken: string | null = null;

// Token refresh interval (refresh 1 minute before expiry)
const TOKEN_REFRESH_BUFFER_MS = 60 * 1000;
const ACCESS_TOKEN_LIFETIME_MS = 15 * 60 * 1000; // 15 minutes

// ---- Refresh mutex ----
// Prevents concurrent refresh attempts that trigger the backend's
// token-reuse-attack detector (which revokes ALL user sessions).
let refreshPromise: Promise<boolean> | null = null;

function refreshWithMutex(): Promise<boolean> {
    if (refreshPromise) {
        return refreshPromise;
    }

    refreshPromise = (async () => {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
            return false;
        }

        try {
            const response = await fetch(`${API_BASE}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
                credentials: 'include',
            });

            if (!response.ok) {
                localStorage.removeItem('refresh_token');
                accessToken = null;
                return false;
            }

            const data = await response.json();
            accessToken = data.access_token;
            localStorage.setItem('refresh_token', data.refresh_token);
            return true;
        } catch (error) {
            console.error('Token refresh failed:', error);
            return false;
        }
    })().finally(() => {
        refreshPromise = null;
    });

    return refreshPromise;
}

// ---- Global fetch interceptor ----
// Many pages call `fetch(`${API_BASE}/...`)` directly. Attach the in-memory access token to
// every backend request that doesn't set its own Authorization header, and refresh once on 401.
// Media, downloads, and EventSource streams authenticate with the httpOnly session cookie instead.
const AUTH_ENDPOINT_PATTERN = /\/auth\/(login|register|refresh|logout)(\?|$)/;

function isBackendUrl(url: string): boolean {
    if (url.startsWith(API_BASE)) return true;
    if (typeof window === 'undefined' || !API_BASE.startsWith('/')) return false;
    try {
        const parsed = new URL(url, window.location.origin);
        return parsed.origin === window.location.origin && parsed.pathname.startsWith(API_BASE);
    } catch {
        return false;
    }
}

function isReplayableBody(body: BodyInit | null | undefined): boolean {
    return (
        body == null ||
        typeof body === 'string' ||
        body instanceof FormData ||
        body instanceof URLSearchParams ||
        body instanceof Blob
    );
}

function installAuthFetchInterceptor() {
    if (typeof window === 'undefined') return;
    const marker = '__authFetchInterceptor';
    const win = window as unknown as Record<string, unknown>;
    if (win[marker]) return;
    win[marker] = true;

    const originalFetch = window.fetch.bind(window);
    window.fetch = async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
        if (input instanceof Request) return originalFetch(input, init);
        const url = input.toString();
        if (!isBackendUrl(url) || AUTH_ENDPOINT_PATTERN.test(url)) return originalFetch(input, init);

        const callerHeaders = new Headers(init?.headers);
        if (callerHeaders.has('Authorization')) return originalFetch(input, init);

        const send = (token: string | null) => {
            if (!token) return originalFetch(input, init);
            const headers = new Headers(init?.headers);
            headers.set('Authorization', `Bearer ${token}`);
            return originalFetch(input, { ...init, headers });
        };

        const response = await send(accessToken);
        if (response.status !== 401 || !isReplayableBody(init?.body)) return response;

        const refreshed = await refreshWithMutex();
        return refreshed ? send(accessToken) : response;
    };
}

installAuthFetchInterceptor();

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

    const clearRefreshTimer = useCallback(() => {
        if (refreshTimerRef.current) {
            clearTimeout(refreshTimerRef.current);
            refreshTimerRef.current = null;
        }
    }, []);

    const scheduleTokenRefresh = useCallback(() => {
        clearRefreshTimer();
        // Schedule refresh 1 minute before token expires
        const refreshDelay = ACCESS_TOKEN_LIFETIME_MS - TOKEN_REFRESH_BUFFER_MS;
        refreshTimerRef.current = setTimeout(async () => {
            const success = await refreshWithMutex();
            if (success) {
                scheduleTokenRefresh();
            }
        }, refreshDelay);
    }, [clearRefreshTimer]);

    const fetchUser = useCallback(async () => {
        if (!accessToken) {
            const refreshed = await refreshWithMutex();
            if (!refreshed) {
                setUser(null);
                setIsLoading(false);
                return;
            }
            scheduleTokenRefresh();
        }

        try {
            const response = await fetch(`${API_BASE}/auth/me`, {
                headers: { Authorization: `Bearer ${accessToken}` },
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else if (response.status === 401) {
                // Token expired, try refresh (mutex prevents races)
                const refreshed = await refreshWithMutex();
                if (refreshed) {
                    scheduleTokenRefresh();
                    const retryResponse = await fetch(`${API_BASE}/auth/me`, {
                        headers: { Authorization: `Bearer ${accessToken}` },
                    });
                    if (retryResponse.ok) {
                        const userData = await retryResponse.json();
                        setUser(userData);
                    } else {
                        setUser(null);
                    }
                } else {
                    setUser(null);
                }
            } else {
                setUser(null);
            }
        } catch (error) {
            console.error('Failed to fetch user:', error);
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    }, [scheduleTokenRefresh]);

    useEffect(() => {
        // Check for existing refresh token on mount
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
            fetchUser();
        } else {
            setIsLoading(false);
        }

        return () => {
            clearRefreshTimer();
        };
    }, [fetchUser, clearRefreshTimer]);

    const login = useCallback(async (email: string, password: string) => {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            credentials: 'include',
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login failed');
        }

        const data = await response.json();
        accessToken = data.access_token;
        localStorage.setItem('refresh_token', data.refresh_token);
        scheduleTokenRefresh();
        await fetchUser();
    }, [fetchUser, scheduleTokenRefresh]);

    const register = useCallback(async (email: string, password: string, fullName?: string) => {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email,
                password,
                full_name: fullName || null
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        // Auto-login after registration
        await login(email, password);
    }, [login]);

    const logout = useCallback(async () => {
        clearRefreshTimer();
        const refreshToken = localStorage.getItem('refresh_token');

        if (refreshToken) {
            try {
                await fetch(`${API_BASE}/auth/logout`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ refresh_token: refreshToken }),
                    credentials: 'include',
                });
            } catch (error) {
                // Ignore logout errors - still clear local state
                console.error('Logout request failed:', error);
            }
        }

        accessToken = null;
        localStorage.removeItem('refresh_token');
        setUser(null);
    }, [clearRefreshTimer]);

    const refreshAccessToken = useCallback(async (): Promise<boolean> => {
        const success = await refreshWithMutex();
        if (success) {
            scheduleTokenRefresh();
        }
        return success;
    }, [scheduleTokenRefresh]);

    const getAccessToken = useCallback(() => {
        return accessToken;
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                isLoading,
                isAuthenticated: !!user,
                login,
                register,
                logout,
                refreshAccessToken,
                getAccessToken,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

/**
 * Helper function to make authenticated API calls.
 * Automatically handles token refresh on 401 responses.
 * Uses the shared refresh mutex to prevent concurrent refresh attempts
 * that would trigger the backend's token-reuse-attack detector.
 */
export async function fetchWithAuth(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    const makeRequest = async (token: string | null) => {
        return fetch(url, {
            ...options,
            headers: {
                ...options.headers,
                ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
        });
    };

    let response = await makeRequest(accessToken);

    // If unauthorized, refresh via mutex (prevents concurrent refreshes)
    if (response.status === 401) {
        const refreshed = await refreshWithMutex();
        if (refreshed) {
            response = await makeRequest(accessToken);
        }
    }

    return response;
}

/**
 * Get the current access token for use in API calls.
 * Returns null if not authenticated.
 */
export function getAuthToken(): string | null {
    return accessToken;
}
