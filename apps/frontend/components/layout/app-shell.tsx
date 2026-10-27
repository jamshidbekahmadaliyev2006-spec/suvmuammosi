"use client";

import React, { useState, useEffect } from "react";
import { Sidebar } from "./sidebar";
import { Header } from "./header";
import { useAuth } from "@/context/auth-context";

interface AppShellProps {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function AppShell({
  title,
  subtitle,
  children,
  onRefresh,
  isRefreshing,
}: AppShellProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const { loading, user } = useAuth();

  useEffect(() => {
    try {
      const saved = localStorage.getItem("suvnazorat_sidebar_collapsed");
      if (saved !== null) {
        setSidebarCollapsed(saved === "true");
      }
    } catch {}
  }, []);

  const toggleSidebar = () => {
    const next = !sidebarCollapsed;
    setSidebarCollapsed(next);
    try {
      localStorage.setItem("suvnazorat_sidebar_collapsed", String(next));
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-slate-50 dark:bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
            SuvNazorat yuklanmoqda...
          </p>
        </div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors">
      {/* Desktop Sidebar (Sticky fixed & collapsible) */}
      <Sidebar
        className="hidden lg:flex"
        collapsed={sidebarCollapsed}
        onToggleCollapse={toggleSidebar}
      />

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="relative z-10 w-64">
            <Sidebar />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col min-w-0">
        <Header
          title={title}
          subtitle={subtitle}
          onMenuClick={() => setMobileMenuOpen(true)}
          onToggleSidebar={toggleSidebar}
          isSidebarCollapsed={sidebarCollapsed}
          onRefresh={onRefresh}
          isRefreshing={isRefreshing}
        />
        <main className="flex-1 p-3.5 sm:p-5 lg:p-6 w-full max-w-[1536px] mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
