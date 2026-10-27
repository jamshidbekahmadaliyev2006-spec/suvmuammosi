"use client";

import React, { useEffect, useState, useCallback, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Building2,
  Search,
  Filter,
  Send,
  X,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  MapPin,
  Calendar,
  Plus,
  FolderPlus,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import {
  IncidentListItem,
  IncidentStatus,
  Page,
  DetectionRule,
} from "@/types";
import {
  formatDateTime,
  priorityBadgeClass,
  priorityLabel,
  statusBadgeClass,
  statusLabel,
} from "@/lib/utils";
import { HighlightedText } from "@/components/ui/highlighted-text";

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "Barcha holatlar" },
  { value: "OPEN", label: "Ochiq / Faol (OPEN)" },
  { value: "IN_PROGRESS", label: "Jarayonda (IN_PROGRESS)" },
  { value: "RESOLVED", label: "Hal qilingan (RESOLVED)" },
  { value: "ARCHIVED", label: "Arxivlangan (ARCHIVED)" },
  { value: "INVALID", label: "Noto'g'ri (INVALID)" },
  { value: "DUPLICATE", label: "Takroriy (DUPLICATE)" },
];

function renderIncidentStatusBadge(item: IncidentListItem) {
  const rtype = (item.report_type || "").toUpperCase();

  if (rtype === "NEWS" || rtype === "YANGILIK") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold border bg-sky-50 text-sky-700 border-sky-300 dark:bg-sky-950/50 dark:text-sky-300 dark:border-sky-800 shadow-2xs">
        <span className="h-1.5 w-1.5 rounded-full bg-sky-500 animate-pulse" />
        <span>🔵 OAV Yangiligi</span>
      </span>
    );
  }
  if (rtype === "GRATITUDE" || rtype === "MINNATDORCHILIK" || rtype === "TASHAKKUR") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold border bg-emerald-50 text-emerald-700 border-emerald-300 dark:bg-emerald-950/50 dark:text-emerald-300 dark:border-emerald-800 shadow-2xs">
        <span>🙏 Minnatdorchilik</span>
      </span>
    );
  }
  if (rtype === "ANNOUNCEMENT" || rtype === "RASMIY_ELON") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-semibold border bg-amber-50 text-amber-800 border-amber-300 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-800 shadow-2xs">
        <span>📢 Rasmiy e&apos;lon</span>
      </span>
    );
  }
  if (rtype === "IRRELEVANT" || rtype === "NOTOGRI" || item.status === "INVALID") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium border bg-slate-100 text-slate-500 border-slate-300 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700">
        <span>⚪ Noto&apos;g&apos;ri / Reklama</span>
      </span>
    );
  }

  // Haqiqiy zayavka / murojaat holati
  if (item.status === "RESOLVED") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-bold border bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800 shadow-2xs">
        <span>🟢 Hal qilingan</span>
      </span>
    );
  }
  if (item.status === "IN_PROGRESS") {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-bold border bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950/60 dark:text-amber-300 dark:border-amber-800 shadow-2xs">
        <span>🟡 Jarayonda</span>
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-bold border bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800 shadow-2xs">
      <span>🔴 Hal qilinmagan</span>
    </span>
  );
}

function IncidentsContent() {
  const searchParams = useSearchParams();
  const initialStatus = searchParams?.get("status") || "";

  const [data, setData] = useState<Page<IncidentListItem> | null>(null);
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [loading, setLoading] = useState(true);

  // Filtrlar holati
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<string>(initialStatus);
  const [reportType, setReportType] = useState<string>("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);

  // URL query parametr o'zgarganda holatni yangilash
  useEffect(() => {
    const s = searchParams?.get("status");
    if (s !== null && s !== undefined) {
      setStatus(s);
      setPage(1);
    }
  }, [searchParams]);

  // Faol kalit so'zlar ro'yxati
  useEffect(() => {
    api.listRules({ is_active: true, page_size: 100 }).then((r) => {
      setRules((r as any).items || []);
    }).catch(() => {});
  }, []);

  const activeKeywords = useMemo(() => {
    const list: string[] = [];
    rules
      .filter((r) => r.is_active)
      .forEach((r) => {
        if (!r.keyword) return;
        const parts = r.keyword.split(/[,;\n\r]+/);
        parts.forEach((p) => {
          const trimmed = p.trim();
          if (trimmed.length >= 2) list.push(trimmed);
        });
      });
    return Array.from(new Set(list));
  }, [rules]);

  // Qoidalar xaritasi va asosiy mos kelgan bitta kalit so'zni topish
  const rulesMap = useMemo(() => {
    const map = new Map<number, DetectionRule>();
    rules.forEach((r) => map.set(r.id, r));
    return map;
  }, [rules]);

  const getMatchedRule = useCallback(
    (item: IncidentListItem): DetectionRule | null => {
      if (item.matched_rule_ids && item.matched_rule_ids.length > 0) {
        for (const id of item.matched_rule_ids) {
          const rule = rulesMap.get(id);
          if (rule) return rule;
        }
      }
      // Agar bazada matched_rule_ids bo'sh bo'lsa, qoidalar matni bo'yicha mosini topamiz
      const text = `${item.title || ""} ${item.description || ""}`.toLowerCase();
      for (const rule of rules) {
        if (!rule.keyword) continue;
        const cleanKw = rule.keyword.replace(/[.,!?:;\"'()\[\]{}]/g, " ").trim().toLowerCase();
        if (cleanKw && text.includes(cleanKw)) {
          return rule;
        }
      }
      return null;
    },
    [rulesMap, rules]
  );

  const fetchIncidents = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listIncidents({
        q: query.trim() || undefined,
        status: (status as IncidentStatus) || undefined,
        report_type: reportType || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        page,
        page_size: 15,
      });
      setData(res);
    } catch {
      // Xatolik holati
    } finally {
      setLoading(false);
    }
  }, [query, status, reportType, dateFrom, dateTo, page]);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchIncidents();
  };

  const clearFilters = () => {
    setQuery("");
    setStatus("");
    setReportType("");
    setDateFrom("");
    setDateTo("");
    setPage(1);
  };

  const hasActiveFilters = Boolean(
    query || status || reportType || dateFrom || dateTo
  );

  return (
    <AppShell
      title="Avariyalar va Hodisalar Monitoringi"
      subtitle="Shahar suv tarmog'idagi barcha aniqlangan hodisalar ro'yxati"
      onRefresh={fetchIncidents}
      isRefreshing={loading}
    >
      <div className="space-y-6">
        {/* AI Saralash va Filtrlash Tugmalari (Groq AI) */}
        <div className="flex flex-wrap items-center gap-2 bg-white dark:bg-slate-900 p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 shadow-2xs">
          <span className="text-xs font-bold text-slate-500 dark:text-slate-400 mr-1 flex items-center gap-1.5 pl-1">
            <span className="text-purple-600 dark:text-purple-400 font-extrabold text-sm">✨</span> AI Saralash:
          </span>
          <button
            type="button"
            onClick={() => {
              setReportType("");
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              !reportType
                ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            Barchasi
          </button>
          <button
            type="button"
            onClick={() => {
              setReportType("ZAYAVKA");
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              reportType === "ZAYAVKA" || reportType === "MUROJAAT"
                ? "bg-purple-600 text-white shadow-xs"
                : "bg-purple-50 text-purple-700 hover:bg-purple-100 dark:bg-purple-950/60 dark:text-purple-300 border border-purple-200 dark:border-purple-800"
            }`}
          >
            <span>🟣</span> Fuqaro arizalari (Zayavkalar)
          </button>
          <button
            type="button"
            onClick={() => {
              setReportType("NEWS");
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              reportType === "NEWS" || reportType === "YANGILIK"
                ? "bg-sky-600 text-white shadow-xs"
                : "bg-sky-50 text-sky-700 hover:bg-sky-100 dark:bg-sky-950/60 dark:text-sky-300 border border-sky-200 dark:border-sky-800"
            }`}
          >
            <span>🔵</span> OAV Yangiliklari
          </button>
          <button
            type="button"
            onClick={() => {
              setReportType("ANNOUNCEMENT");
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              reportType === "ANNOUNCEMENT" || reportType === "RASMIY_ELON"
                ? "bg-amber-600 text-white shadow-xs"
                : "bg-amber-50 text-amber-700 hover:bg-amber-100 dark:bg-amber-950/60 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
            }`}
          >
            <span>📢</span> Rasmiy e&apos;lonlar
          </button>
          <button
            type="button"
            onClick={() => {
              setReportType("GRATITUDE");
              setPage(1);
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
              reportType === "GRATITUDE" || reportType === "MINNATDORCHILIK"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800"
            }`}
          >
            <span>🙏</span> Minnatdorchilik
          </button>
        </div>

        {/* Qidiruv va Filtrlash Paneli */}
        <Card className="p-4">
          <form onSubmit={handleSearch} className="space-y-3">
            <div className="flex flex-col gap-3 md:flex-row">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Sarlavha, manzil yoki tuman bo'yicha qidiruv..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                />
              </div>

              <div className="flex flex-wrap items-center gap-2">
                {/* Holat filtri */}
                <div className="w-52">
                  <Select
                    options={STATUS_OPTIONS}
                    value={status}
                    onChange={(e) => {
                      setStatus(e.target.value);
                      setPage(1);
                    }}
                  />
                </div>

                <Button type="submit" size="md">
                  Qidirish
                </Button>

                {hasActiveFilters && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="md"
                    onClick={clearFilters}
                    className="text-slate-500 hover:text-slate-700"
                  >
                    <X className="h-4 w-4 mr-1" /> Tozalash
                  </Button>
                )}
              </div>
            </div>

            {/* Sana filtrlari */}
            <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 text-xs text-slate-500 dark:border-slate-800">
              <span className="flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300">
                <Calendar className="h-3.5 w-3.5" /> Sana oralig'i:
              </span>
              <div className="flex items-center gap-2">
                <label>Dan:</label>
                <input
                  type="date"
                  value={dateFrom}
                  onChange={(e) => {
                    setDateFrom(e.target.value);
                    setPage(1);
                  }}
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
              <div className="flex items-center gap-2">
                <label>Gacha:</label>
                <input
                  type="date"
                  value={dateTo}
                  onChange={(e) => {
                    setDateTo(e.target.value);
                    setPage(1);
                  }}
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
            </div>
          </form>
        </Card>

        {/* Hodisalar Jadvali */}
        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
                <tr>
                  <th className="py-3.5 px-4">Hodisa nomi va Murojaat</th>
                  <th className="py-3.5 px-4">📍 Hudud va Manzil</th>
                  <th className="py-3.5 px-4">Holati</th>
                  <th className="py-3.5 px-4">📢 Manba (Kanal/Guruh)</th>
                  <th className="py-3.5 px-4">Aniqlangan vaqti</th>
                  <th className="py-3.5 px-4 text-right">Amal</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      <div className="flex flex-col items-center justify-center gap-2">
                        <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
                        Yuklanmoqda...
                      </div>
                    </td>
                  </tr>
                ) : !data || data.items.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-slate-400">
                      {hasActiveFilters
                        ? "Tanlangan filtrlar bo'yicha hech qanday hodisa topilmadi."
                        : "Hozircha hech qanday hodisa mavjud emas."}
                    </td>
                  </tr>
                ) : (
                  data.items.map((item) => {
                    const matchedRule = getMatchedRule(item);
                    return (
                    <tr
                      key={item.id}
                      className="transition-colors hover:bg-slate-50/80 dark:hover:bg-slate-800/40"
                    >
                      <td className="py-3.5 px-4 max-w-sm">
                        {/* AI Tahlili Natijasi (Murojaat / Yangilik / Rasmiy e'lon / Minnatdorchilik) */}
                        <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
                          {(item.report_type === "MUROJAAT" || item.report_type === "ZAYAVKA") && (
                            <span className="inline-flex items-center gap-1 rounded bg-purple-50 dark:bg-purple-950/80 px-2 py-0.5 text-[10px] font-bold text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                              <span>🟣</span> Fuqaro arizasi
                            </span>
                          )}
                          {(item.report_type === "YANGILIK" || item.report_type === "NEWS") && (
                            <span className="inline-flex items-center gap-1 rounded bg-sky-50 dark:bg-sky-950/80 px-2 py-0.5 text-[10px] font-bold text-sky-700 dark:text-sky-300 border border-sky-200 dark:border-sky-800">
                              <span>🔵</span> OAV Yangiligi
                            </span>
                          )}
                          {(item.report_type === "RASMIY_ELON" || item.report_type === "ANNOUNCEMENT") && (
                            <span className="inline-flex items-center gap-1 rounded bg-amber-50 dark:bg-amber-950/80 px-2 py-0.5 text-[10px] font-bold text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                              <span>📢</span> Rasmiy e&apos;lon
                            </span>
                          )}
                          {(item.report_type === "GRATITUDE" || item.report_type === "MINNATDORCHILIK") && (
                            <span className="inline-flex items-center gap-1 rounded bg-emerald-50 dark:bg-emerald-950/80 px-2 py-0.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                              <span>🙏</span> Minnatdorchilik
                            </span>
                          )}
                        </div>

                        <Link
                          href={`/incidents/${item.id}`}
                          className="font-bold text-slate-900 hover:text-brand-600 dark:text-slate-100 dark:hover:text-brand-400 block"
                        >
                          <HighlightedText text={item.title} keywords={activeKeywords} />
                        </Link>

                        {/* AI Qisqa xulosasi */}
                        {item.ai_summary && (
                          <div className="mt-1.5 p-2 rounded-lg bg-purple-50/60 dark:bg-purple-950/30 border border-purple-200/50 dark:border-purple-800/40 text-[11px] text-purple-950 dark:text-purple-200 leading-snug">
                            <span className="font-bold text-purple-700 dark:text-purple-400 mr-1">✨ AI xulosa:</span>
                            {item.ai_summary}
                          </div>
                        )}

                        {/* Yechim izohi (agar bartaraf etilgan bo'lsa) */}
                        {item.status === "RESOLVED" && item.resolution_notes && (
                          <div className="mt-1.5 p-2 rounded-lg bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/50 text-[11px] text-emerald-950 dark:text-emerald-200 leading-snug flex items-start gap-1.5">
                            <span className="font-bold text-emerald-800 dark:text-emerald-300 shrink-0">✨ Yechim:</span>
                            <span>{item.resolution_notes}</span>
                          </div>
                        )}

                        {/* Qaysi kalit so'z bo'yicha aniqlanganligi (faqat 1 ta asosiy nishon) */}
                        {matchedRule && (
                          <div className="mt-1 flex items-center gap-1.5">
                            <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-900 border border-amber-300 dark:bg-amber-950/70 dark:border-amber-800 dark:text-amber-200 shadow-2xs">
                              <span className="text-[10px] text-amber-600 dark:text-amber-400 font-extrabold uppercase mr-0.5">Kalit so'z:</span>
                              <span className="underline decoration-amber-500 decoration-[2px] underline-offset-2 font-black">
                                «{matchedRule.keyword?.replace(/\.$/, "")}»
                              </span>
                            </span>
                          </div>
                        )}

                        {item.description && (
                          <div className="mt-2 text-xs text-slate-700 dark:text-slate-300 whitespace-pre-wrap break-words bg-slate-50 dark:bg-slate-800/50 p-2.5 rounded-lg border border-slate-100 dark:border-slate-800 leading-relaxed">
                            <span className="font-sans font-semibold text-[10px] text-slate-400 block mb-1">
                              💬 {item.source_type === "GROUP" ? "Guruhdagi xabar:" : "Telegram xabari:"}
                            </span>
                            <HighlightedText
                              text={item.description}
                              keywords={matchedRule?.keyword ? [matchedRule.keyword, ...activeKeywords] : activeKeywords}
                            />
                          </div>
                        )}
                        {item.media_type === "photo" && item.media_url && (
                          <div className="mt-2">
                            <img
                              src={item.media_url}
                              alt="Hodisa rasmi"
                              className="h-20 w-auto rounded-lg object-cover border border-slate-200 dark:border-slate-700 cursor-pointer hover:scale-105 transition-transform"
                              onClick={() => window.open(item.media_url!, "_blank")}
                            />
                          </div>
                        )}
                        {item.media_type === "video" && (
                          <div className="mt-1 text-[11px] font-semibold text-purple-600 dark:text-purple-400 flex items-center gap-1">
                            <span>🎥 Video xabar biriktirilgan</span>
                          </div>
                        )}
                        {item.location_url && (
                          <div className="mt-1">
                            <a
                              href={item.location_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 hover:underline"
                            >
                              <MapPin className="h-3 w-3" />
                              <span>📍 GPS Xarita (Google Maps)</span>
                            </a>
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4 min-w-[170px]">
                        {item.district || item.address ? (
                          <div className="space-y-1.5">
                            {item.district && (
                              <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-2 py-0.5 text-xs font-bold text-amber-900 border border-amber-200 dark:bg-amber-950/40 dark:border-amber-900/60 dark:text-amber-300">
                                <Building2 className="h-3 w-3 text-amber-600" />
                                {item.district}
                              </span>
                            )}
                            {item.address && (
                              <div className="flex items-center gap-1 text-xs font-semibold text-rose-800 dark:text-rose-300">
                                <MapPin className="h-3.5 w-3.5 text-rose-500 shrink-0" />
                                <span>{item.address}</span>
                              </div>
                            )}
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400 italic">Aniqlanmagan</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        {renderIncidentStatusBadge(item)}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="space-y-1">
                          <span className="inline-flex items-center gap-1 text-xs font-semibold text-sky-800 dark:text-sky-300">
                            <Send className="h-3 w-3 text-sky-500" />
                            {item.source_type === "CHANNEL"
                              ? "Kanal:"
                              : item.source_type === "BOT"
                              ? "Bot orqali:"
                              : "Guruh:"}{" "}
                            {item.source_name}
                          </span>
                          {item.source_username && (
                            <div className="text-[11px] text-slate-400">
                              <a
                                href={`https://t.me/${item.source_username}`}
                                target="_blank"
                                rel="noreferrer"
                                className="text-sky-600 hover:underline dark:text-sky-400"
                              >
                                @{item.source_username}
                              </a>
                            </div>
                          )}
                          <div>
                            {(() => {
                              const descUrl = item.description?.match(/https:\/\/t\.me\/(?:c\/\d+|\w+)(?:\/\d+)+/)?.[0];
                              const directUrl = item.message_url || descUrl || (item.source_username ? `https://t.me/${item.source_username}` : "https://t.me/hokimyatsuvnazorati_bot");
                              return (
                                <a
                                  href={directUrl}
                                  target="_blank"
                                  rel="noreferrer"
                                  className="inline-flex items-center gap-1 text-[11px] font-bold text-sky-600 hover:text-sky-700 hover:underline dark:text-sky-400"
                                  title={item.source_type === "GROUP" ? "Guruhdagi xabarni ochish" : (item.message_url ? "Telegramdagi xabarni ochish" : "Telegramda ochish")}
                                >
                                  Telegramda ochish <ExternalLink className="h-2.5 w-2.5" />
                                </a>
                              );
                            })()}
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-xs text-slate-500 dark:text-slate-400">
                        {formatDateTime(item.first_seen_at)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <Link href={`/incidents/${item.id}`}>
                          <Button size="sm" variant="outline">
                            Batafsil
                          </Button>
                        </Link>
                      </td>
                    </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Sahifalash (Pagination) */}
          {data && data.total > 0 && (
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 dark:border-slate-800">
              <span className="text-xs text-slate-500 dark:text-slate-400">
                Jami <strong>{data.total}</strong> ta hodisadan{" "}
                {(data.page - 1) * data.page_size + 1}–
                {Math.min(data.page * data.page_size, data.total)} ko'rsatilmoqda
              </span>

              <div className="flex items-center gap-2">
                {(() => {
                  const totalPages =
                    data.total_pages ||
                    Math.max(1, Math.ceil((data.total || 0) / (data.page_size || 20)));
                  return (
                    <>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={data.page <= 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                      >
                        <ChevronLeft className="h-4 w-4" /> Oldingi
                      </Button>
                      <span className="text-xs font-semibold px-2 text-slate-700 dark:text-slate-300">
                        {data.page} / {totalPages}
                      </span>
                      <Button
                        size="sm"
                        variant="outline"
                        disabled={data.page >= totalPages}
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      >
                        Keyingi <ChevronRight className="h-4 w-4" />
                      </Button>
                    </>
                  );
                })()}
              </div>
            </div>
          )}
        </Card>
      </div>
    </AppShell>
  );
}

export default function IncidentsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <span className="text-sm font-semibold text-slate-500">Hodisalar yuklanmoqda...</span>
        </div>
      }
    >
      <IncidentsContent />
    </Suspense>
  );
}
