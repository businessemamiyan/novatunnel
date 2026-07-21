import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";
import { PageMetaProvider, useCurrentPageMeta } from "./PageMetaContext";

function ShellContent() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const meta = useCurrentPageMeta();

  return (
    <div className="flex h-screen overflow-hidden">
      <div className={`${mobileOpen ? "block" : "hidden"} md:block fixed md:static z-20 h-full`}>
        <Sidebar onNavigate={() => setMobileOpen(false)} />
      </div>
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-10 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={meta.title} subtitle={meta.subtitle} onMenuClick={() => setMobileOpen(true)} />
        <main className="flex-1 overflow-y-auto scrollbar-thin p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default function AppShell() {
  return (
    <PageMetaProvider>
      <ShellContent />
    </PageMetaProvider>
  );
}
