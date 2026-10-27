"use client";

import React, { useEffect, useState } from "react";
import { Menu, RefreshCw, Radio, Sun, Moon, PanelLeft, PanelLeftClose } from "lucide-react";
import { useTheme } from "@/context/theme-context";

interface HeaderProps {
  title: string;
  subtitle?: string;
  onMenuClick?: () => void;
  onToggleSidebar?: () => void;
  isSidebarCollapsed?: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Header({
  title,
  subtitle,
  onMenuClick,
  onToggleSidebar,
  isSidebarCollapsed,
  onRefresh,
  isRefreshing,
}: HeaderProps) {
  const [currentTime, setCurrentTime] = useState<string>("");
  const { theme, toggleTheme } = useTheme();

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        new Intl.DateTimeFormat("uz-UZ", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        }).format(now)
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-20 flex h-16 w-full items-center justify-between border-b border-slate-200/90 bg-white/90 px-4 sm:px-6 backdrop-blur-md transition-colors dark:border-slate-800 dark:bg-slate-900/90 shadow-2xs">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger */}
        {onMenuClick && (
          <button
            onClick={onMenuClick}
            className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-2xs hover:bg-slate-100 hover:text-slate-900 lg:hidden dark:border-slate-800 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
            title="Mobil menyuni ochish"
          >
            <Menu className="h-5 w-5" />
          </button>
        )}


        <div>
          <h1 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-[11px] sm:text-xs text-slate-500 dark:text-slate-400 truncate max-w-xs sm:max-w-md">
              {subtitle}
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Real-time Indicator */}
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-800/60 dark:text-slate-300">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
          </span>
          <span className="font-mono">{currentTime || "..."}</span>
        </div>

        {/* Theme Toggle Button (Quyosh / Yarim oy, faqat bitta belgi, yozuvsiz) */}
        <button
          onClick={toggleTheme}
          title={theme === "dark" ? "Kunduzgi rejimga o'tish" : "Tungi rejimga o'tish"}
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-xs hover:bg-slate-100 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700 transition-colors"
        >
          {theme === "dark" ? (
            <Moon className="h-4 w-4 text-indigo-400" />
          ) : (
            <Sun className="h-4 w-4 text-amber-500" />
          )}
        </button>

        {/* Refresh Button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            title="Ma'lumotlarni yangilash"
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm transition-all hover:bg-slate-50 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            <RefreshCw
              className={`h-3.5 w-3.5 text-slate-500 dark:text-slate-400 ${
                isRefreshing ? "animate-spin text-brand-600" : ""
              }`}
            />
            <span className="hidden sm:inline">Yangilash</span>
          </button>
        )}
      </div>
    </header>
  );
}
