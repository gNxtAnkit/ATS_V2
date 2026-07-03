import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react';
import { useParams, Navigate } from 'react-router-dom';
import { Search, ShieldAlert, X } from 'lucide-react';
import { AppShell } from '../../components/layout/AppShell';
import { Card, CardBody } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { DataTable, inferColumns, type JsonRecord } from '../../components/ui/DataTable';
import { RecordDetail } from '../../components/ui/RecordDetail';
import { ConfirmDialog } from '../../components/ui/ConfirmDialog';
import { platformControlApi, toSafeUserMessage } from '../../api';
import { useAuth } from '../../lib/auth/AuthProvider';
import { usePlatformPermissions } from '../../lib/auth/usePlatformPermissions';
import { PLATFORM_MODULES, type PlatformActionConfig } from './moduleConfig';

export function ModulePage() {
  const { moduleSlug } = useParams<{ moduleSlug: string }>();
  const module = PLATFORM_MODULES.find((candidate) => candidate.slug === moduleSlug);

  const { withFreshToken } = useAuth();
  const { can, loadingPermissions } = usePlatformPermissions();

  const [rows, setRows] = useState<JsonRecord[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<JsonRecord | null>(null);
  const [pendingAction, setPendingAction] = useState<PlatformActionConfig | null>(null);
  const [actionBusy, setActionBusy] = useState(false);

  const loadRows = useCallback(
    async (cursorParam: string | null, replace: boolean) => {
      if (!module) return;
      setLoading(true);
      setError(null);
      try {
        const query: Record<string, string> = { limit: '50' };
        if (cursorParam) query.cursor = cursorParam;
        if (search.trim()) query.q = search.trim();
        const page = await withFreshToken((accessToken) => platformControlApi.list<JsonRecord>(accessToken, module.listPath, query));
        setRows((current) => (replace ? page.data : [...current, ...page.data]));
        setCursor(page.page.next_cursor);
        setHasMore(page.page.has_more);
      } catch (err) {
        setError(toSafeUserMessage(err));
      } finally {
        setLoading(false);
      }
    },
    [module, search, withFreshToken],
  );

  useEffect(() => {
    setSelected(null);
    void loadRows(null, true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [module?.slug]);

  const columns = useMemo(() => inferColumns(rows), [rows]);

  async function handleSearchSubmit(event: FormEvent) {
    event.preventDefault();
    await loadRows(null, true);
  }

  async function executeAction(action: PlatformActionConfig) {
    if (!module) return;
    const path = action.path(selected);
    if (!path) return;
    setActionBusy(true);
    try {
      const body = action.body ? action.body(selected) : undefined;
      const method = action.method;
      const call =
        method === 'POST'
          ? (accessToken: string) => platformControlApi.post<JsonRecord>(accessToken, path, body)
          : method === 'PATCH'
            ? (accessToken: string) => platformControlApi.patch<JsonRecord>(accessToken, path, body ?? {})
            : method === 'PUT'
              ? (accessToken: string) => platformControlApi.put<JsonRecord>(accessToken, path, body ?? {})
              : (accessToken: string) => platformControlApi.delete<JsonRecord>(accessToken, path);
      const result = await withFreshToken(call);
      setSelected(result.data);
      setRows((current) => current.map((row) => (row.id === result.data.id ? result.data : row)));
      setPendingAction(null);
    } catch (err) {
      setError(toSafeUserMessage(err));
    } finally {
      setActionBusy(false);
    }
  }

  async function runAction() {
    if (!pendingAction) return;
    await executeAction(pendingAction);
  }

  if (!module) return <Navigate to="/" replace />;

  if (!loadingPermissions && !can(module.readPermission)) {
    return (
      <AppShell title={module.title}>
        <Card>
          <CardBody className="flex flex-col items-center text-center py-14">
            <ShieldAlert size={28} className="text-slate-300 mb-3" />
            <p className="text-sm font-semibold text-slate-700">You don't have access to this area</p>
            <p className="text-xs text-slate-500 mt-1">
              This section requires the <code className="font-mono">{module.readPermission}</code> permission.
            </p>
          </CardBody>
        </Card>
      </AppShell>
    );
  }

  const availableActions = (module.actions ?? []).filter((action) => can(action.permission));

  return (
    <AppShell title={module.title} subtitle={module.description}>
      {error && (
        <div className="mb-4">
          <Alert variant="error" onDismiss={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
        <Card>
          <CardBody className="p-4 border-b border-slate-100">
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
              <div className="relative flex-1 max-w-sm">
                <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder={`Search ${module.title.toLowerCase()}...`}
                  className="w-full h-9 pl-9 pr-3 text-sm rounded-lg border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-500/20 focus:border-slate-500"
                />
              </div>
              <Button type="submit" variant="secondary" size="sm">
                Search
              </Button>
            </form>
          </CardBody>
          <CardBody className="p-0">
            <DataTable
              rows={rows}
              columns={columns}
              selectedId={typeof selected?.id === 'string' ? selected.id : null}
              onSelect={setSelected}
              loading={loading && rows.length === 0}
              emptyTitle={`No ${module.title.toLowerCase()} found`}
            />
          </CardBody>
          {hasMore && (
            <div className="p-4 border-t border-slate-100 flex justify-center">
              <Button variant="secondary" size="sm" loading={loading} onClick={() => void loadRows(cursor, false)}>
                Load more
              </Button>
            </div>
          )}
        </Card>

        <Card className="h-fit xl:sticky xl:top-6">
          {selected ? (
            <>
              <div className="flex items-center justify-between p-4 border-b border-slate-100">
                <p className="text-sm font-bold text-slate-900">Details</p>
                <button onClick={() => setSelected(null)} className="text-slate-400 hover:text-slate-600">
                  <X size={16} />
                </button>
              </div>
              <CardBody className="max-h-[560px] overflow-auto">
                <RecordDetail record={selected} />
              </CardBody>
              {availableActions.length > 0 && (
                <div className="p-4 border-t border-slate-100 flex flex-wrap gap-2">
                  {availableActions.map((action) => (
                    <Button
                      key={action.label}
                      size="sm"
                      variant={action.destructive ? 'danger' : 'secondary'}
                      onClick={() => (action.confirm ? setPendingAction(action) : void executeAction(action))}
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              )}
            </>
          ) : (
            <CardBody className="py-14 text-center">
              <p className="text-sm text-slate-500">Select a row to view details.</p>
            </CardBody>
          )}
        </Card>
      </div>

      <ConfirmDialog
        open={Boolean(pendingAction)}
        title={pendingAction?.label ?? ''}
        description={pendingAction?.confirm}
        confirmLabel={pendingAction?.label}
        destructive={pendingAction?.destructive}
        busy={actionBusy}
        onConfirm={runAction}
        onCancel={() => setPendingAction(null)}
      />
    </AppShell>
  );
}
