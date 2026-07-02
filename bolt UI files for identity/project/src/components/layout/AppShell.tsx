import { ReactNode, useState, useEffect } from 'react';
import { Sidebar } from './Sidebar';
import { TopBar } from './TopBar';
import { MobileBottomTabs } from './MobileBottomTabs';
import { ui } from '../../lib/theme';

interface AppShellProps {
  children: ReactNode;
  pageTitle: string;
}

export function AppShell({ children, pageTitle }: AppShellProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const stored = localStorage.getItem('sidebar-collapsed');
    if (stored !== null) return stored === 'true';
    return window.innerWidth < 1280;
  });

  useEffect(() => {
    localStorage.setItem('sidebar-collapsed', String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  return (
    /*
     * h-screen + overflow-hidden on the outermost container ensures:
     * — sidebar and topbar never scroll
     * — only <main> scrolls via overflow-y-auto
     * — no horizontal page overflow
     */
    <div className={['flex h-screen overflow-hidden', ui.appSurface].join(' ')}>
      {/* Sidebar — hidden below md, fixed height, does NOT have overflow:hidden so
          the collapse toggle (-right-3) and nav tooltips render correctly */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
      />

      {/* Right column — takes remaining width, flex column, clipped */}
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {/* TopBar — shrink-0 ensures it never scrolls away */}
        <TopBar pageTitle={pageTitle} />

        {/* Workspace — the ONE and ONLY scrollable area */}
        <main className="flex-1 min-h-0 overflow-y-auto overflow-x-hidden">
          <div className="p-4 sm:p-5 lg:p-6 max-w-screen-2xl mx-auto">
            {children}
          </div>
          {/* Bottom spacer for mobile tab bar */}
          <div className="h-20 md:hidden" aria-hidden="true" />
        </main>
      </div>

      {/* Mobile bottom tab bar — rendered via fixed positioning */}
      <MobileBottomTabs />
    </div>
  );
}
