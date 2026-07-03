import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardBody } from '../../components/ui/Card';
import { Skeleton } from '../../components/ui/Skeleton';
import { PLATFORM_MODULES } from '../modules/moduleConfig';
import { platformControlApi } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';

type JsonRecord = Record<string, unknown>;

const OVERVIEW_MODULES = PLATFORM_MODULES.slice(0, 6);

export function OverviewPage() {
  const { admin, withFreshToken } = useAuth();
  const [counts, setCounts] = useState<Record<string, number | null>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadCounts() {
      setLoading(true);
      const results = await Promise.all(
        OVERVIEW_MODULES.map(async (module) => {
          try {
            const page = await withFreshToken((accessToken) =>
              platformControlApi.list<JsonRecord>(accessToken, module.listPath, { limit: '1' }),
            );
            // The list endpoint doesn't return a total count, so we surface
            // whether there is any data plus a "more available" signal
            // instead of fabricating a total.
            return [module.slug, page.data.length + (page.page.has_more ? 1 : 0)] as const;
          } catch {
            return [module.slug, null] as const;
          }
        }),
      );
      if (active) {
        setCounts(Object.fromEntries(results));
        setLoading(false);
      }
    }
    void loadCounts();
    return () => {
      active = false;
    };
  }, [withFreshToken]);

  return (
    <AppShell title="Overview" subtitle={`Welcome back, ${admin?.display_name ?? ''}`}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {OVERVIEW_MODULES.map((module) => (
          <Link key={module.slug} to={`/platform/${module.slug}`} className="group">
            <Card className="h-full transition-shadow hover:shadow-float">
              <CardBody>
                <div className="flex items-start justify-between mb-3">
                  <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                    <module.icon size={18} className="text-slate-600" />
                  </div>
                  <ArrowRight size={16} className="text-slate-300 group-hover:text-slate-500 group-hover:translate-x-0.5 transition-all" />
                </div>
                <p className="text-sm font-bold text-slate-900">{module.title}</p>
                <p className="text-xs text-slate-500 mt-1 leading-relaxed line-clamp-2">{module.description}</p>
                <div className="mt-3">
                  {loading ? (
                    <Skeleton className="h-4 w-16" />
                  ) : counts[module.slug] === null ? (
                    <span className="text-xs text-slate-400">Unavailable</span>
                  ) : (
                    <span className="text-xs font-semibold text-slate-600">
                      {counts[module.slug]}{counts[module.slug] === 1 ? ' record' : '+ records'}
                    </span>
                  )}
                </div>
              </CardBody>
            </Card>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
