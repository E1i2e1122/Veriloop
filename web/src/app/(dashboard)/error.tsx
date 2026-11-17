'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, Home, RotateCcw } from 'lucide-react';

export default function DashboardError({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        console.error('Dashboard page error:', error);
    }, [error]);

    return (
        <div className="route-state" role="alert">
            <div className="route-state-icon route-state-icon--danger">
                <AlertTriangle size={26} />
            </div>
            <h1>Something went wrong on this page</h1>
            <p>The rest of the dashboard is still available. Try loading the page again, or go back to the overview.</p>
            {error.digest && <p className="route-state-meta">Reference: {error.digest}</p>}
            <div className="route-state-actions">
                <button type="button" className="btn btn-primary" onClick={reset}>
                    <RotateCcw size={16} /> Try again
                </button>
                <Link href="/" className="btn">
                    <Home size={16} /> Back to overview
                </Link>
            </div>
        </div>
    );
}
