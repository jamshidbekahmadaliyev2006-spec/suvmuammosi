"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertTriangle,
  KeyRound,
  Radio,
  Settings,
  LogOut,
  Moon,
  Sun,
  Droplets,
  ChevronLeft,
  ChevronRight,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";
import { useTheme } from "@/context/theme-context";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const NAV_ITEMS: NavItem[] = [
  { name: "Bosh sahifa", href: "/dashboard", icon: LayoutDashboard },
  { name: "Hodisalar", href: "/incidents", icon: AlertTriangle },
  { name: "Kalit so'zlar", href: "/detection-rules", icon: KeyRound },
  { name: "Telegram manbalari", href: "/sources", icon: Radio },
  { name: "Sozlamalar", href: "/settings", icon: Settings },
];

interface SidebarProps {
  className?: string;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function Sidebar({ className, collapsed: propCollapsed, onToggleCollapse }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();

  const [internalCollapsed, setInternalCollapsed] = useState(false);
  const isCollapsed = propCollapsed !== undefined ? propCollapsed : internalCollapsed;

  const handleToggle = () => {
    if (onToggleCollapse) {
      onToggleCollapse();
    } else {
      setInternalCollapsed(!internalCollapsed);
    }
  };

  return (
    <aside
      className={cn(
        "sticky top-0 self-start z-30 flex h-screen flex-col border-r border-slate-200 bg-white py-5 transition-all duration-300 dark:border-slate-800 dark:bg-slate-900 select-none overflow-y-auto shrink-0",
        isCollapsed ? "w-20 px-2.5" : "w-64 px-4",
        className
      )}
    >
      {/* Brand Header */}
      <div className={cn("flex items-center mb-8", isCollapsed ? "justify-center px-1" : "justify-between px-2")}>
        <button
          onClick={handleToggle}
          className="flex items-center gap-3 min-w-0 text-left hover:opacity-80 transition-opacity cursor-pointer group"
          title={isCollapsed ? "Menyuni ochish (kengaytirish)" : "Menyuni yopish (ixchamlashtirish)"}
        >
          <div
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 text-white shadow-md shadow-brand-500/20 group-hover:scale-105 transition-transform"
          >
            <Droplets className="h-6 w-6" />
          </div>
          {!isCollapsed && (
            <div className="min-w-0">
              <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white truncate block">
                Suv<span className="text-brand-600 dark:text-brand-400">Nazorati</span>
              </span>
              <span className="block text-[10px] font-medium tracking-wider uppercase text-slate-400 truncate">
                Monitoring Markazi
              </span>
            </div>
          )}
        </button>

        {/* Ochish / Yopish Tugmasi (Collapse Toggle) */}
        {!isCollapsed && (
          <button
            onClick={handleToggle}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-200 transition-colors"
            title="Menyuni ixchamlashtirish"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1.5">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.href}
              href={item.href}
              prefetch={true}
              title={isCollapsed ? item.name : undefined}
              className={cn(
                "flex items-center rounded-xl py-2.5 text-sm font-medium transition-all group",
                isCollapsed ? "justify-center px-2" : "gap-3 px-3.5",
                isActive
                  ? "bg-gradient-to-r from-sky-500 to-brand-600 text-white font-bold shadow-md shadow-sky-500/25 dark:from-sky-600 dark:to-brand-700"
                  : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800/60 dark:hover:text-slate-200"
              )}
            >
              <Icon
                className={cn(
                  "h-5 w-5 shrink-0",
                  isActive
                    ? "text-white"
                    : "text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300"
                )}
              />
              {!isCollapsed && <span className="truncate">{item.name}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Footer / User Profile & Actions */}
      <div className="border-t border-slate-200 pt-4 dark:border-slate-800">
        {/* User Profile */}
        {user && (
          <div
            className={cn(
              "flex items-center rounded-xl bg-slate-50 p-2 dark:bg-slate-800/50",
              isCollapsed ? "flex-col gap-2 justify-center" : "justify-between"
            )}
          >
            <div className={cn("flex items-center gap-2.5 min-w-0", isCollapsed && "justify-center")}>
              <div
                className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-200 font-semibold text-xs text-slate-700 dark:bg-slate-700 dark:text-slate-200 uppercase"
                title={user.username}
              >
                {user.username.slice(0, 2)}
              </div>
              {!isCollapsed && (
                <div className="min-w-0">
                  <p className="truncate text-xs font-semibold text-slate-900 dark:text-slate-100">
                    {user.username}
                  </p>
                  <span className="inline-block rounded px-1.5 py-0.2 text-[10px] font-medium bg-brand-100 text-brand-800 dark:bg-brand-900/50 dark:text-brand-300">
                    {user.role}
                  </span>
                </div>
              )}
            </div>

            <button
              onClick={logout}
              title="Tizimdan chiqish"
              className="rounded-lg p-1.5 text-slate-400 hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40 dark:hover:text-rose-400 transition-colors"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
