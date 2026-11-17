import Link from 'next/link';
import { Compass, Home } from 'lucide-react';

export default function NotFound() {
    return (
        <main className="route-state route-state--page">
            <div className="route-state-icon">
                <Compass size={26} />
            </div>
            <p className="route-state-code">404</p>
            <h1>Page not found</h1>
            <p>The page you are looking for doesn&apos;t exist or has moved.</p>
            <div className="route-state-actions">
                <Link href="/" className="btn btn-primary">
                    <Home size={16} /> Back to overview
                </Link>
            </div>
        </main>
    );
}
