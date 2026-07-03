import { useCallback, useEffect, useState } from 'react';
import { platformControlApi } from '../../api';
import { useAuth } from './AuthProvider';

type JsonRecord = Record<string, unknown>;

export function usePlatformPermissions() {
  const { admin, withFreshToken } = useAuth();
  const [permissions, setPermissions] = useState<Set<string>>(new Set());
  const [loadingPermissions, setLoadingPermissions] = useState(true);

  useEffect(() => {
    let active = true;
    async function loadPermissions() {
      if (!admin) {
        setLoadingPermissions(false);
        return;
      }
      setLoadingPermissions(true);
      try {
        const rolePage = await withFreshToken((accessToken) =>
          platformControlApi.list<JsonRecord>(accessToken, `/v1/platform-admin/access-control/users/${admin.actor_id}/roles`),
        );
        const loaded = new Set<string>();
        await Promise.all(
          rolePage.data.map(async (role) => {
            const roleId = role.id;
            if (typeof roleId !== 'string') return;
            const permissionPage = await withFreshToken((accessToken) =>
              platformControlApi.list<JsonRecord>(accessToken, `/v1/platform-admin/access-control/roles/${roleId}/permissions`),
            );
            permissionPage.data.forEach((permission) => {
              const permissionKey = permission.permission_key;
              if (typeof permissionKey === 'string') loaded.add(permissionKey);
            });
          }),
        );
        if (active) setPermissions(loaded);
      } catch {
        if (active) setPermissions(new Set());
      } finally {
        if (active) setLoadingPermissions(false);
      }
    }

    void loadPermissions();
    return () => {
      active = false;
    };
  }, [admin, withFreshToken]);

  const can = useCallback((permission: string) => permissions.has(permission), [permissions]);
  return { permissions, can, loadingPermissions };
}
