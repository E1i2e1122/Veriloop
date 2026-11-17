import { Skeleton } from '@/components/ui/skeleton';

const ROW_WIDTHS = ['72%', '64%', '81%', '58%', '69%'];

export default function DashboardLoading() {
    return (
        <div aria-busy="true" aria-label="Loading page" className="route-loading">
            <div className="route-loading-header">
                <Skeleton style={{ width: '220px', height: '28px' }} />
                <Skeleton style={{ width: '340px', height: '14px', marginTop: '0.6rem' }} />
            </div>
            <div className="route-loading-stats">
                {[0, 1, 2, 3].map((i) => (
                    <Skeleton key={i} style={{ height: '88px' }} />
                ))}
            </div>
            <div className="route-loading-rows">
                {ROW_WIDTHS.map((width, i) => (
                    <div key={i} className="route-loading-row">
                        <Skeleton style={{ width: '36px', height: '36px' }} />
                        <div style={{ flex: 1 }}>
                            <Skeleton style={{ width, height: '13px' }} />
                            <Skeleton style={{ width: '38%', height: '10px', marginTop: '0.5rem' }} />
                        </div>
                        <Skeleton style={{ width: '64px', height: '22px' }} />
                    </div>
                ))}
            </div>
        </div>
    );
}
