"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  Clock,
  Droplet,
  ExternalLink,
  ChevronRight,
  MapPin,
  Radio,
  RefreshCw,
  Send,
  Filter,
  ChevronDown,
  Check,
  User,
  Phone,
  Bot,
  Camera,
  Video,
  Sparkles,
  RotateCcw,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert } from "@/components/ui/alert";
import { Modal } from "@/components/ui/modal";
import { api } from "@/lib/api";
import { DashboardStats, DetectionRule, IncidentListItem, MessageOut } from "@/types";
import { formatDateTime, statusBadgeClass, statusLabel } from "@/lib/utils";
import { HighlightedText } from "@/components/ui/highlighted-text";

function formatPhoneNumber(phone?: string | null): string {
  if (!phone) return "";
  const cleaned = phone.replace(/[^\d+]/g, "");
  if (cleaned.startsWith("+998") && cleaned.length === 13) {
    return `${cleaned.slice(0, 4)} (${cleaned.slice(4, 6)}) ${cleaned.slice(6, 9)}-${cleaned.slice(9, 11)}-${cleaned.slice(11, 13)}`;
  }
  return phone;
}

interface CitizenDetails {
  name: string | null;
  phone: string | null;
  address: string | null;
  gps: string | null;
  mapUrl: string | null;
  userNote: string | null;
}

function parseCitizenDetails(text?: string | null): CitizenDetails | null {
  if (!text) return null;
  let name: string | null = null;
  let phone: string | null = null;
  let address: string | null = null;
  let gps: string | null = null;
  let mapUrl: string | null = null;
  let userNote: string | null = null;

  const lines = text.split("\n");
  for (const line of lines) {
    const l = line.trim();
    if (/^(?:👤\s*)?(?:Fuqaro|Foydalanuvchi|Yuboruvchi|Murojaatchi|Ism|Akkaunt):\s*(.+)/i.test(l)) {
      name = l.replace(/^(?:👤\s*)?(?:Fuqaro|Foydalanuvchi|Yuboruvchi|Murojaatchi|Ism|Akkaunt):\s*/i, "").trim();
    } else if (/^(?:📞\s*)?(?:Fuqaro\s+)?(?:telefoni|telefon|tel|raqami):\s*(.+)/i.test(l)) {
      phone = l.replace(/^(?:📞\s*)?(?:Fuqaro\s+)?(?:telefoni|telefon|tel|raqami):\s*/i, "").trim();
    } else if (/^(?:📍\s*)?Manzil:\s*(.+)/i.test(l)) {
      address = l.replace(/^(?:📍\s*)?Manzil:\s*/i, "").trim();
    } else if (/GPS:\s*([0-9.,\s]+)/i.test(l)) {
      const match = l.match(/GPS:\s*([0-9.,\s]+)/i);
      if (match) gps = match[1].trim();
    } else if (l.includes("maps.google.com") || l.includes("google.com/maps")) {
      const match = l.match(/https?:\/\/[^\s]+/);
      if (match) {
        mapUrl = match[0];
        const coordMatch = mapUrl.match(/[?&]q=([0-9.,\s]+)/);
        if (coordMatch && !gps) {
          gps = coordMatch[1].trim();
        }
      }
    } else if (/^(?:💬\s*)?(?:Murojaat\s+matni|Izoh|Matn):\s*(.+)/i.test(l)) {
      userNote = l.replace(/^(?:💬\s*)?(?:Murojaat\s+matni|Izoh|Matn):\s*/i, "").trim();
    }
  }

  // Standalone phone number match
  if (!phone) {
    const phoneMatch = text.match(/(?:\+?998[\s-]?\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}|\b998\d{9}\b)/);
    if (phoneMatch) {
      phone = phoneMatch[0];
    }
  }

  if (!userNote && (name || phone || address || gps)) {
    const noteLines = lines.filter(
      (line) =>
        line.trim() &&
        !/^(?:👤|📞|📍|💬|GPS:|https?:|Fuqaro:|Fuqaro\s+telefoni:|Manzil:)/i.test(line.trim())
    );
    if (noteLines.length > 0) {
      userNote = noteLines.join(" ").trim();
    }
  }

  if (name || phone || address || gps || mapUrl || userNote) {
    return { name, phone, address, gps, mapUrl, userNote };
  }
  return null;
}

function getIncidentSourceInfo(inc: IncidentListItem) {
  let sourceName = inc.source_name || "Telegram Kanal";
  let sourceUsername = inc.source_username || "";
  let sourceType = inc.source_type || "CHANNEL";
  let messageUrl = inc.message_url || "";

  if (inc.description) {
    const channelMatch = inc.description.match(/(?:Kanal|Manba|Guruh):\s*([^(@\n]+)(?:\s*\(@?([A-Za-z0-9_]+)\))?/i);
    if (channelMatch) {
      if (channelMatch[1]) sourceName = channelMatch[1].trim();
      if (channelMatch[2]) sourceUsername = channelMatch[2].trim();
    }
    const urlMatch = inc.description.match(/https:\/\/t\.me\/(?:c\/\d+|\w+)(?:\/\d+)+/);
    if (urlMatch) {
      if (!messageUrl) messageUrl = urlMatch[0];
    }
  }

  const isCitizen =
    sourceType === "BOT" ||
    sourceName.toLowerCase().includes("bot") ||
    sourceUsername === "hokimyatsuvnazorati_bot" ||
    Boolean(inc.description && (inc.description.includes("Fuqaro:") || inc.description.includes("Fuqaro telefoni:")));

  if (isCitizen) {
    sourceType = "BOT";
    sourceName = "Telegram Bot (Murojaatlar)";
    sourceUsername = "hokimyatsuvnazorati_bot";
    if (!messageUrl) messageUrl = "https://t.me/hokimyatsuvnazorati_bot";
  }

  const finalUrl =
    messageUrl ||
    (sourceUsername ? `https://t.me/${sourceUsername}` : "https://t.me/hokimyatsuvnazorati_bot");

  return {
    sourceName,
    sourceUsername,
    sourceType,
    messageUrl: finalUrl,
    isCitizen,
  };
}

function formatIncidentTitle(
  inc: IncidentListItem,
  citizen: ReturnType<typeof parseCitizenDetails>,
  isCitizen: boolean
): string {
  if (isCitizen) {
    if (citizen?.name) {
      return `Fuqaro murojaati: ${citizen.name}`;
    }
    let title = inc.title || "";
    title = title.replace(/^(?:Fuqaro murojaati:\s*)+(?:👤\s*)?(?:Fuqaro:\s*)?/i, "");
    if (title.includes("https://maps.google.com") || title.includes("GPS Lokatsiya")) {
      if (inc.district || inc.address) {
        return `Fuqaro murojaati: Lokatsiya orqali (${inc.district || inc.address})`;
      }
      return "Fuqaro murojaati: GPS Lokatsiya orqali";
    }
    title = title.replace(/\*+/g, "").trim();
    if (title.length > 95) {
      title = title.substring(0, 92) + "...";
    }
    return title ? `Fuqaro murojaati: ${title}` : "Fuqaro murojaati: Suv ta'minoti bo'yicha";
  }

  let title = inc.title || "";
  title = title.replace(/\*+/g, "").trim();
  if (title.length > 95) {
    title = title.substring(0, 92) + "...";
  }
  return title || "Suv ta'minoti bo'yicha xabar";
}


export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentIncidents, setRecentIncidents] = useState<IncidentListItem[]>([]);
  const [recentMessages, setRecentMessages] = useState<MessageOut[]>([]);
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Tanlangan sana (kunlik ma'lumotlar uchun)
  const [selectedDate, setSelectedDate] = useState<string>("");

  // 3 ta asosiy bo'lim / Tab (Bosh sahifada faqat zayavkalar, yangiliklar esa boshqa tabda):
  const [activeTab, setActiveTab] = useState<"ZAYAVKA" | "NEWS" | "ANNOUNCEMENT">("ZAYAVKA");
  // Arizalar ichki filtri: "ALL" | "OPEN" | "RESOLVED"
  const [zayavkaFilter, setZayavkaFilter] = useState<"ALL" | "OPEN" | "RESOLVED">("ALL");

  // Avariyani / arizani hal qilingan deb tasdiqlash modali
  const [resolveModalIncident, setResolveModalIncident] = useState<IncidentListItem | null>(null);
  const [resolutionNote, setResolutionNote] = useState("");
  const [resolving, setResolving] = useState(false);

  const handleOpenResolveModal = (inc: IncidentListItem) => {
    setResolveModalIncident(inc);
    setResolutionNote("Avariya brigadasi tomonidan to'liq bartaraf etildi, suv ta'minoti me'yorida tiklandi.");
  };

  const handleConfirmResolve = async () => {
    if (!resolveModalIncident) return;
    setResolving(true);
    try {
      const note = resolutionNote.trim() || "Avariya brigadasi tomonidan to'liq bartaraf etildi.";
      await api.patchIncident(resolveModalIncident.id, {
        status: "RESOLVED" as const,
        resolution_notes: note,
      });

      // Mahalliy ro'yxatni darhol yangilash
      setRecentIncidents((prev) =>
        prev.map((item) =>
          item.id === resolveModalIncident.id
            ? {
                ...item,
                status: "RESOLVED" as const,
                resolution_notes: note,
                resolved_at: new Date().toISOString(),
              }
            : item
        )
      );

      // Statistika kartochkalarini yangilash
      api.getDashboardStats().then((s) => setStats(s)).catch(() => {});
      setResolveModalIncident(null);
    } catch {
      alert("Arizani hal qilishda xatolik yuz berdi.");
    } finally {
      setResolving(false);
    }
  };

  const handleReopen = async (inc: IncidentListItem) => {
    if (!confirm("Ushbu arizani qayta ochmoqchimisiz?")) return;
    try {
      await api.patchIncident(inc.id, {
        status: "OPEN" as const,
        comment: "Dispetcher tomonidan qayta ochildi.",
      });
      setRecentIncidents((prev) =>
        prev.map((item) =>
          item.id === inc.id
            ? { ...item, status: "OPEN" as const, resolution_notes: null, resolved_at: null }
            : item
        )
      );
      api.getDashboardStats().then((s) => setStats(s)).catch(() => {});
    } catch {
      alert("Arizani qayta ochishda xatolik yuz berdi.");
    }
  };

  const fetchData = useCallback(async (isManual = false) => {
    if (isManual) setRefreshing(true);
    try {
      const fetchRules = isManual || rules.length === 0;
      const [statsData, incidentsData, messagesData, rulesData] = await Promise.all([
        api.getDashboardStats(),
        api.getRecentIncidents(50),
        api.getRecentMessages(6),
        fetchRules
          ? api.listRules({ is_active: true, page_size: 100 }).catch(() => ({ items: [] }))
          : Promise.resolve(null),
      ]);
      setStats(statsData);
      setRecentIncidents(incidentsData);
      setRecentMessages(messagesData);
      if (rulesData && (rulesData as any).items) {
        setRules((rulesData as any).items || []);
      }
      setError(null);
    } catch (err: any) {
      setError("Dashboard ma'lumotlarini yuklashda xatolik yuz berdi.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [rules.length]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Faol kalit so'zlar ro'yxati (matnlarda tagiga chizish uchun)
  const activeKeywords = useMemo(() => {
    const list: string[] = [];
    rules
      .filter((r) => r.is_active)
      .forEach((r) => {
        if (!r.keyword) return;
        const parts = r.keyword.split(/[,;\n\r]+/);
        parts.forEach((p) => {
          const trimmed = p.trim();
          if (trimmed.length >= 2) {
            list.push(trimmed);
          }
        });
      });
    return Array.from(new Set(list));
  }, [rules]);

  // Qoidalar xaritasi va har bir hodisa uchun kalit so'zni topish
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

  // Jonli yangilanish (15s polling)
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchData();
    }, 15000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchData]);

  // Bugungi sana
  const todayFormatted = useMemo(() => {
    const now = new Date();
    const months = [
      "Yanvar", "Fevral", "Mart", "Aprel", "May", "Iyun",
      "Iyul", "Avgust", "Sentyabr", "Oktabr", "Noyabr", "Dekabr",
    ];
    return `${now.getDate()}-${months[now.getMonth()]}, ${now.getFullYear()}`;
  }, []);

  // Tanlangan sana bo'yicha hodisalar to'plami
  const dateScopedIncidents = useMemo(() => {
    if (!selectedDate) {
      return recentIncidents;
    }
    return recentIncidents.filter((inc) => {
      const itemDate = inc.first_seen_at ? inc.first_seen_at.substring(0, 10) : "";
      return itemDate === selectedDate;
    });
  }, [recentIncidents, selectedDate]);

  // 4 ta asosiy KPI kartochka ko'rsatkichlari (Jami zayavkalar, Hal qilinmagan zayavkalar, Hal qilingan zayavkalar, Kanallar va yangiliklar)
  const displayedCards = useMemo(() => {
    const totalSources =
      stats?.cards?.channels_and_groups_count ?? (stats?.sources?.length || 53);

    if (selectedDate) {
      const zayavkas = dateScopedIncidents.filter((i) => i.report_type === "ZAYAVKA" || i.report_type === "MUROJAAT");
      const open = zayavkas.filter((i) => i.status === "OPEN" || i.status === "IN_PROGRESS").length;
      const resolved = zayavkas.filter((i) => i.status === "RESOLVED").length;
      const newsCount = dateScopedIncidents.filter((i) => i.report_type === "NEWS" || i.report_type === "YANGILIK").length;
      return {
        total: open + resolved,
        open,
        resolved,
        totalSources,
        newsCount,
      };
    }

    // Barcha vaqt bo'yicha:
    // Jami zayavkalar = Hal qilinmagan + Hal qilingan (qat'iy matematika!)
    const open = stats?.cards?.open_incidents ?? 0;
    const resolved = stats?.cards?.resolved_incidents ?? 0;
    const newsCount = stats?.cards?.news_count ?? 135;
    const total = open + resolved;

    return {
      total,
      open,
      resolved,
      totalSources,
      newsCount,
    };
  }, [selectedDate, dateScopedIncidents, stats]);

  // Filtrlangan hodisalar (activeTab va zayavkaFilter bo'yicha)
  const filteredIncidents = useMemo(() => {
    const list = dateScopedIncidents.filter((inc) => {
      const isNews = inc.report_type === "NEWS" || inc.report_type === "YANGILIK";
      const isGratitude = inc.report_type === "GRATITUDE" || inc.report_type === "TASHAKKUR" || inc.report_type === "MINNATDORCHILIK";
      const isAnnouncement = inc.report_type === "ANNOUNCEMENT" || inc.report_type === "RASMIY_ELON";
      const isZayavka = !isNews && !isGratitude && !isAnnouncement && inc.report_type !== "IRRELEVANT";

      if (activeTab === "ZAYAVKA") {
        if (!isZayavka) return false;
        if (zayavkaFilter === "OPEN" && inc.status !== "OPEN" && inc.status !== "IN_PROGRESS") return false;
        if (zayavkaFilter === "RESOLVED" && inc.status !== "RESOLVED") return false;
        return true;
      }

      if (activeTab === "NEWS") {
        return isNews;
      }

      if (activeTab === "ANNOUNCEMENT") {
        return isAnnouncement || isGratitude;
      }

      return true;
    });

    // Eng oxirgi kelgan hodisalar birinchi ko'rsatiladi
    return list.sort((a, b) => {
      const timeA = new Date(a.last_seen_at || a.first_seen_at || 0).getTime();
      const timeB = new Date(b.last_seen_at || b.first_seen_at || 0).getTime();
      if (timeB !== timeA) {
        return timeB - timeA;
      }
      return b.id - a.id;
    });
  }, [dateScopedIncidents, activeTab, zayavkaFilter]);

  return (
    <AppShell
      title="Bosh sahifa"
      subtitle="Real vaqt monitoringi va shahar suv ta'minoti tezkor boshqaruvi"
      onRefresh={() => fetchData(true)}
      isRefreshing={refreshing}
    >
      <div className="space-y-6">
        {/* Yuqori boshqaruv va filtrlar paneli */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 rounded-2xl bg-white p-3.5 px-4 border border-slate-200/80 shadow-xs dark:bg-slate-900/90 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="flex h-2.5 w-2.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
              Jonli Monitoring Rejimi
            </span>
            <span className="text-xs text-slate-400 hidden md:inline">
              • Aholi murojaatlari va suv tarmog&apos;i holati
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Sana tanlash */}
            <div className="flex items-center gap-2 rounded-xl bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:bg-slate-800 dark:text-slate-300 border border-slate-200 dark:border-slate-700 shadow-xs">
              <Calendar className="h-3.5 w-3.5 text-brand-600 dark:text-brand-400 shrink-0" />
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                className="bg-transparent border-none text-xs font-semibold text-slate-800 dark:text-slate-200 focus:outline-none cursor-pointer"
                title="Kunlik ma'lumotlarni ko'rish uchun sanani tanlang"
              />
              {selectedDate ? (
                <button
                  onClick={() => setSelectedDate("")}
                  className="text-[11px] font-bold text-brand-600 dark:text-brand-400 hover:underline ml-1"
                  title="Bugungi kunga qaytish"
                >
                  Bugun
                </button>
              ) : (
                <span className="text-[11px] text-slate-400 hidden sm:inline">({todayFormatted})</span>
              )}
            </div>

            {/* Jonli yangilash switchi */}
            <label className="relative inline-flex cursor-pointer items-center text-xs text-slate-600 dark:text-slate-400">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="peer sr-only"
              />
              <div className="peer h-5 w-9 rounded-full bg-slate-200 after:absolute after:top-[2px] after:left-[2px] after:h-4 after:w-4 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-brand-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none dark:bg-slate-700 dark:border-gray-600"></div>
              <span className="ml-2 font-medium hidden md:inline">Jonli yangilash</span>
            </label>

            {/* Yangilash tugmasi */}
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="rounded-xl p-2 text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 transition-colors"
              title="Qayta yuklash"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin text-brand-600" : ""}`} />
            </button>
          </div>
        </div>

        {error && (
          <Alert type="error">
            {error}{" "}
            <Button size="sm" variant="outline" className="ml-3" onClick={() => fetchData(true)}>
              Qayta urinish
            </Button>
          </Alert>
        )}

        {/* 1. Asosiy 4 ta KPI kartochka (Image 1 dizayni va talabi asosida) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Jami zayavkalar (Deep Teal) */}
          <div
            onClick={() => {
              setActiveTab("ZAYAVKA");
              setZayavkaFilter("ALL");
            }}
            className={`rounded-2xl p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer flex flex-col justify-between ${
              activeTab === "ZAYAVKA" && zayavkaFilter === "ALL"
                ? "bg-[#0b2d34] text-white ring-2 ring-teal-400"
                : "bg-[#0e3b43] text-white border border-[#144f5a]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-teal-200/80">
                Aholi arizalari (Zayavkalar)
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white shadow-xs backdrop-blur-xs">
                <Droplet className="h-4 w-4 text-teal-200" />
              </div>
            </div>
            <div className="my-2.5">
              <span className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                {loading ? "..." : displayedCards.total}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2.5 border-t border-white/10 text-xs">
              <span className="text-teal-200/70 font-medium">Baza bo&apos;yicha zayavkalar</span>
              <span className="font-bold text-teal-300">→</span>
            </div>
          </div>

          {/* Card 2: Hal qilinmagan zayavkalar (QIZIL RANGDA - Foydalanuvchi talabi) */}
          <div
            onClick={() => {
              setActiveTab("ZAYAVKA");
              setZayavkaFilter("OPEN");
            }}
            className={`rounded-2xl p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer flex flex-col justify-between ${
              activeTab === "ZAYAVKA" && zayavkaFilter === "OPEN"
                ? "bg-[#991b1b] text-white ring-2 ring-white"
                : "bg-[#b91c1c] text-white border border-[#dc2626]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-rose-100">
                Hal qilinmagan arizalar
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-white shadow-xs">
                <AlertTriangle className="h-4 w-4 text-white" />
              </div>
            </div>
            <div className="my-2.5">
              <span className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                {loading ? "..." : displayedCards.open}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2.5 border-t border-white/20 text-xs">
              <span className="text-rose-100/90 font-semibold">Zudlik bilan choralar</span>
              <span className="font-bold text-white">→</span>
            </div>
          </div>

          {/* Card 3: Hal qilingan arizalar (YASHIL RANGDA - Foydalanuvchi talabi) */}
          <div
            onClick={() => {
              setActiveTab("ZAYAVKA");
              setZayavkaFilter("RESOLVED");
            }}
            className={`rounded-2xl p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer flex flex-col justify-between ${
              activeTab === "ZAYAVKA" && zayavkaFilter === "RESOLVED"
                ? "bg-[#14532d] text-white ring-2 ring-white"
                : "bg-[#15803d] text-white border border-[#22c55e]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-100">
                Hal qilingan
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/20 text-white shadow-xs">
                <CheckCircle2 className="h-4 w-4 text-white" />
              </div>
            </div>
            <div className="my-2.5">
              <span className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                {loading ? "..." : displayedCards.resolved}
              </span>
            </div>
            <div className="flex items-center justify-between pt-2.5 border-t border-white/20 text-xs">
              <span className="text-emerald-100/90 font-medium">Bartaraf etilgan</span>
              <span className="font-bold text-white">→</span>
            </div>
          </div>

          {/* Card 4: Kanallar va OAV Yangiliklari (Deep Navy) */}
          <div
            onClick={() => setActiveTab("NEWS")}
            className={`rounded-2xl p-5 shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1 cursor-pointer flex flex-col justify-between bg-[#192238] text-white border border-[#263456] block group ${
              activeTab === "NEWS" ? "ring-2 ring-indigo-400" : ""
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-200/80">
                Kanallar va OAV xabarlari
              </span>
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-white shadow-xs backdrop-blur-xs">
                <Radio className="h-4 w-4 text-indigo-300" />
              </div>
            </div>
            <div className="my-2.5">
              <span className="text-3xl sm:text-4xl font-black text-white tracking-tight">
                {displayedCards.totalSources} ta
              </span>
            </div>
            <div className="flex items-center justify-between pt-2.5 border-t border-white/10 text-xs">
              <span className="text-indigo-200/70 font-medium">{displayedCards.newsCount} ta yangilik monitoringda</span>
              <span className="font-bold text-indigo-300 group-hover:translate-x-1 transition-transform">
                →
              </span>
            </div>
          </div>
        </div>

        {/* 2. Asosiy Bo'limlar / Tablar (Bosh sahifada faqat zayavkalar, yangiliklar esa boshqa tabda) */}
        <div className="flex flex-wrap items-center justify-between gap-3 bg-white dark:bg-slate-900 p-2.5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => {
                setActiveTab("ZAYAVKA");
                setZayavkaFilter("ALL");
              }}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                activeTab === "ZAYAVKA"
                  ? "bg-teal-700 text-white shadow-xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
              }`}
            >
              <span>📋</span> Aholi arizalari (Zayavkalar)
              <span className={`px-2 py-0.5 rounded-full text-[11px] font-black ${
                activeTab === "ZAYAVKA" ? "bg-white/20 text-white" : "bg-teal-100 text-teal-800 dark:bg-teal-950 dark:text-teal-300"
              }`}>
                {displayedCards.total} ta
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("NEWS")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                activeTab === "NEWS"
                  ? "bg-sky-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
              }`}
            >
              <span>🔵</span> OAV Yangiliklari
              <span className={`px-2 py-0.5 rounded-full text-[11px] font-black ${
                activeTab === "NEWS" ? "bg-white/20 text-white" : "bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-300"
              }`}>
                {displayedCards.newsCount} ta
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab("ANNOUNCEMENT")}
              className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                activeTab === "ANNOUNCEMENT"
                  ? "bg-amber-600 text-white shadow-xs"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300"
              }`}
            >
              <span>📢</span> Rasmiy e&apos;lonlar va Minnatdorchilik
            </button>
          </div>

          {/* Agar Arizalar tabi bo'lsa: Hal qilinmagan / Hal qilingan ichki filtri */}
          {activeTab === "ZAYAVKA" && (
            <div className="flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800/80 p-1 rounded-xl">
              <button
                type="button"
                onClick={() => setZayavkaFilter("ALL")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  zayavkaFilter === "ALL"
                    ? "bg-white text-slate-900 shadow-2xs dark:bg-slate-900 dark:text-white"
                    : "text-slate-600 hover:text-slate-900 dark:text-slate-400"
                }`}
              >
                Barchasi ({displayedCards.total})
              </button>
              <button
                type="button"
                onClick={() => setZayavkaFilter("OPEN")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                  zayavkaFilter === "OPEN"
                    ? "bg-rose-600 text-white shadow-2xs"
                    : "text-rose-700 hover:bg-rose-50 dark:text-rose-400"
                }`}
              >
                <span>🔴</span> Hal qilinmagan ({displayedCards.open})
              </button>
              <button
                type="button"
                onClick={() => setZayavkaFilter("RESOLVED")}
                className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1 ${
                  zayavkaFilter === "RESOLVED"
                    ? "bg-emerald-600 text-white shadow-2xs"
                    : "text-emerald-700 hover:bg-emerald-50 dark:text-emerald-400"
                }`}
              >
                <span>🟢</span> Hal qilingan ({displayedCards.resolved})
              </button>
            </div>
          )}
        </div>

        {/* 3. Asosiy Hodisalar Ro'yxati */}
        <div className="rounded-2xl border border-slate-200/90 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 overflow-hidden">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-5 border-b border-slate-100 dark:border-slate-800">
            <div>
              <h3 className="text-base font-bold text-slate-900 dark:text-white">
                {activeTab === "ZAYAVKA" && "Aholi murojaatlari va arizalari (Zayavkalar)"}
                {activeTab === "NEWS" && "Telegram kanallari va OAV Yangiliklari"}
                {activeTab === "ANNOUNCEMENT" && "Rasmiy e'lonlar va Minnatdorchilik xabarlari"}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {activeTab === "ZAYAVKA" && "Aholining suv ta'minoti bo'yicha aniq muammolari va ularning bartaraf etilishi"}
                {activeTab === "NEWS" && "OAV va kanallardagi umumiy axborotlar (Faqat ma'lumot uchun, avariya emas)"}
                {activeTab === "ANNOUNCEMENT" && "Rejaviy ta'mirlash ogohlantirishlari va fuqarolar tashakkurnomalari"}
              </p>
            </div>
          </div>

          {loading ? (
            <div className="py-16 text-center text-sm text-slate-400">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-sky-500 opacity-70" />
              Hodisalar yuklanmoqda...
            </div>
          ) : filteredIncidents.length === 0 ? (
            activeKeywords.length === 0 ? (
              <div className="py-16 px-4 text-center max-w-md mx-auto space-y-4">
                <div className="h-16 w-16 mx-auto rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-200 dark:border-amber-900 shadow-sm">
                  <Sparkles className="h-8 w-8" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                    Bosh sahifa toza — Kalit so&apos;zlar kutilmoqda
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    Hozircha tizimda kalit so&apos;zlar (qoidalar) mavjud emas. Xabarlarni avtomatik aniqlash uchun kalit so&apos;z kiritishingiz mumkin.
                  </p>
                </div>
                <div>
                  <Link
                    href="/detection-rules"
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-md transition-all hover:scale-105 active:scale-95"
                  >
                    <span>Kalit so&apos;zlar bo&apos;limiga o&apos;tish</span>
                    <ChevronRight className="h-4 w-4" />
                  </Link>
                </div>
              </div>
            ) : (
              <div className="py-16 px-4 text-center max-w-md mx-auto space-y-4">
                <div className="h-16 w-16 mx-auto rounded-2xl bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400 flex items-center justify-center border border-sky-200 dark:border-sky-900 shadow-sm">
                  <Radio className="h-8 w-8 text-sky-500 animate-pulse" />
                </div>
                <div className="space-y-1.5">
                  <h3 className="text-base font-bold text-slate-800 dark:text-slate-100">
                    {selectedDate
                      ? `${selectedDate} sanasida hodisa topilmadi`
                      : "Hozircha mos keluvchi hodisalar yo'q"}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                    Faol {activeKeywords.length} ta kalit so&apos;z bo&apos;yicha Telegram kanallari va botdan xabarlar real vaqtda kuzatilmoqda.
                  </p>
                </div>
                <div className="flex items-center justify-center gap-3 pt-1">
                  <Link
                    href="/detection-rules"
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 font-bold text-xs transition-colors"
                  >
                    <span>Qoidalar ({activeKeywords.length})</span>
                  </Link>
                  <button
                    onClick={() => fetchData(true)}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-sm transition-all hover:scale-105 active:scale-95"
                  >
                    <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin" : ""}`} />
                    <span>Yangilash</span>
                  </button>
                </div>
              </div>
            )
          ) : (
            <div className="p-4 sm:p-5 space-y-4">
              {filteredIncidents.map((inc) => {
                const citizen = parseCitizenDetails(inc.description);
                const sourceInfo = getIncidentSourceInfo(inc);
                const isCitizenCard = sourceInfo.isCitizen || Boolean(citizen);
                const cleanTitle = formatIncidentTitle(inc, citizen, isCitizenCard);
                const isResolved = inc.status === "RESOLVED";
                const matchedRule = getMatchedRule(inc);

                const isNews = inc.report_type === "NEWS" || inc.report_type === "YANGILIK";
                const isGratitude = inc.report_type === "GRATITUDE" || inc.report_type === "TASHAKKUR" || inc.report_type === "MINNATDORCHILIK";
                const isAnnouncement = inc.report_type === "ANNOUNCEMENT" || inc.report_type === "RASMIY_ELON";
                const isZayavka = !isNews && !isGratitude && !isAnnouncement;

                let borderLeftClass = "border-l-sky-500";
                if (isZayavka) {
                  borderLeftClass = isResolved ? "border-l-emerald-500" : "border-l-rose-500";
                } else if (isGratitude) {
                  borderLeftClass = "border-l-emerald-500";
                } else if (isAnnouncement) {
                  borderLeftClass = "border-l-amber-500";
                }

                return (
                  <div
                    key={inc.id}
                    className={`rounded-2xl border border-slate-200/90 bg-white p-4 sm:p-5 shadow-xs hover:shadow-lg dark:border-slate-800 dark:bg-slate-900 transition-all duration-300 hover:-translate-y-0.5 border-l-4 ${borderLeftClass} relative overflow-hidden group`}
                  >
                    <div className="flex flex-col gap-3">
                      {/* 1. Yuqori qator: Nishonlar va Harakat tugmalari */}
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        {/* Nishonlar guruhi */}
                        <div className="flex flex-wrap items-center gap-2">
                          {isZayavka ? (
                            <span
                              className={`px-3 py-1 rounded-full text-xs font-bold border transition-colors flex items-center gap-1.5 ${
                                isResolved
                                  ? "bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900"
                                  : "bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-900"
                              }`}
                            >
                              <span>{isResolved ? "🟢" : "🔴"}</span>
                              <span>{isResolved ? "Ariza: Hal qilingan" : "Ariza: Hal qilinmagan"}</span>
                            </span>
                          ) : isGratitude ? (
                            <span className="px-3 py-1 rounded-full text-xs font-bold border bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900 flex items-center gap-1.5">
                              <span>🙏</span> Minnatdorchilik (Hal etilgan)
                            </span>
                          ) : isAnnouncement ? (
                            <span className="px-3 py-1 rounded-full text-xs font-bold border bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900 flex items-center gap-1.5">
                              <span>📢</span> Rasmiy e&apos;lon (Rejali)
                            </span>
                          ) : (
                            <span className="px-3 py-1 rounded-full text-xs font-bold border bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-900 flex items-center gap-1.5">
                              <span>🔵</span> OAV Yangiligi (Ma&apos;lumot uchun)
                            </span>
                          )}

                          {inc.district && (
                            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-50 text-sky-700 border border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-900">
                              <MapPin className="h-3 w-3 text-sky-600 dark:text-sky-400" />
                              {inc.district}
                            </span>
                          )}
                        </div>

                        {/* Harakat tugmalari: Hal qilish, Telegramda ochish va Tafsilotlar */}
                        <div className="flex flex-wrap items-center gap-2">
                          {isZayavka && (
                            !isResolved ? (
                              <button
                                type="button"
                                onClick={() => handleOpenResolveModal(inc)}
                                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all shadow-xs hover:scale-105 active:scale-95 cursor-pointer"
                                title="Arizani hal qilingan deb tasdiqlash"
                              >
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                <span>Hal qilindi deb belgilash</span>
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleReopen(inc)}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300 text-xs font-semibold transition-all border border-slate-200 dark:border-slate-700 cursor-pointer"
                                title="Arizani qayta ochish"
                              >
                                <RotateCcw className="h-3 w-3 text-slate-500" />
                                <span>Qayta ochish</span>
                              </button>
                            )
                          )}

                          <a
                            href={sourceInfo.messageUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1.5 rounded-full bg-sky-50 hover:bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:hover:bg-sky-900/60 dark:text-sky-300 border border-sky-200 dark:border-sky-800/80 px-3.5 py-1.5 text-xs font-bold transition-all shadow-2xs hover:scale-105 active:scale-95"
                            title={sourceInfo.sourceUsername ? `@${sourceInfo.sourceUsername} da ochish` : "Telegramda ochish"}
                          >
                            <Send className="h-3.5 w-3.5" />
                            <span>Telegramda ochish</span>
                            <ExternalLink className="h-3 w-3 opacity-60" />
                          </a>

                          <Link
                            href={`/incidents/${inc.id}`}
                            className="inline-flex items-center gap-1 px-4 py-1.5 rounded-full bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:text-slate-900 dark:hover:bg-slate-100 text-xs font-bold transition-all shadow-2xs hover:scale-105 active:scale-95"
                          >
                            <span>Tafsilotlar</span>
                            <ChevronRight className="h-3.5 w-3.5" />
                          </Link>
                        </div>
                      </div>

                      {/* 2. Sarlavha va Kalit so'z */}
                      <div className="space-y-1">
                        <Link
                          href={`/incidents/${inc.id}`}
                          className="text-base font-bold text-slate-900 hover:text-sky-600 dark:text-white dark:hover:text-sky-400 transition-colors tracking-tight block"
                        >
                          <HighlightedText
                            text={cleanTitle}
                            keywords={matchedRule?.keyword ? [matchedRule.keyword, ...activeKeywords] : activeKeywords}
                          />
                        </Link>

                        {/* Qaysi kalit so'z bo'yicha aniqlanganligi (faqat 1 ta asosiy nishon) */}
                        {matchedRule && (
                          <div className="flex items-center gap-1.5 pt-0.5">
                            <span className="inline-flex items-center gap-1 rounded bg-amber-50 px-2 py-0.5 text-[11px] font-bold text-amber-900 border border-amber-300 dark:bg-amber-950/70 dark:border-amber-800 dark:text-amber-200 shadow-2xs">
                              <span className="text-[10px] text-amber-600 dark:text-amber-400 font-extrabold uppercase mr-0.5">Kalit so'z:</span>
                              <span className="underline decoration-amber-500 decoration-[2px] underline-offset-2 font-black">
                                «{matchedRule.keyword?.replace(/\.$/, "")}»
                              </span>
                            </span>
                          </div>
                        )}

                        {/* AI Qisqa Mazmuni */}
                        {inc.ai_summary && (
                          <div className="mt-2 p-2.5 rounded-xl bg-purple-50/70 dark:bg-purple-950/30 border border-purple-200/50 dark:border-purple-800/40 text-xs text-purple-950 dark:text-purple-200 flex items-start gap-2">
                            <span className="font-bold text-purple-700 dark:text-purple-400 shrink-0">✨ AI xulosa:</span>
                            <span className="leading-relaxed">{inc.ai_summary}</span>
                          </div>
                        )}

                        {/* Hal etilganlik tafsilotlari (Resolution info) */}
                        {isResolved && inc.resolution_notes && (
                          <div className="mt-2 p-2.5 rounded-xl bg-emerald-50/80 dark:bg-emerald-950/30 border border-emerald-200/60 dark:border-emerald-800/50 text-xs text-emerald-950 dark:text-emerald-200 flex items-start gap-2">
                            <CheckCircle2 className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0 mt-0.5" />
                            <div className="space-y-0.5">
                              <span className="font-bold text-emerald-800 dark:text-emerald-300">Yechim / Bartaraf etildi:</span>
                              <p className="leading-relaxed">{inc.resolution_notes}</p>
                              {inc.resolved_at && (
                                <span className="text-[10px] text-emerald-600/80 dark:text-emerald-400/80 block">
                                  Hal etilgan vaqti: {formatDateTime(inc.resolved_at)}
                                </span>
                              )}
                            </div>
                          </div>
                        )}
                      </div>

                      {/* 3. Asosiy Mazmun Bloki */}
                      {isCitizenCard ? (
                        /* === 3-RASMDEK: Fuqaro Murojaati Bloki === */
                        <div className="rounded-2xl bg-slate-50/80 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/80 p-3.5">
                          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                            {/* Murojaatchi */}
                            <div className="flex items-center gap-2.5">
                              <div className="h-8 w-8 rounded-full bg-sky-100 text-sky-600 dark:bg-sky-950/80 dark:text-sky-400 flex items-center justify-center shrink-0 shadow-2xs">
                                <User className="h-4 w-4" />
                              </div>
                              <div className="min-w-0">
                                <span className="text-[10px] text-slate-400 font-bold block uppercase tracking-wider">
                                  MUROJAATCHI
                                </span>
                                <span className="font-bold text-slate-800 dark:text-slate-100 truncate block">
                                  {citizen?.name || "Telegram foydalanuvchisi"}
                                </span>
                              </div>
                            </div>

                            {/* Telefon */}
                            <div className="flex items-center gap-2.5">
                              <div className="h-8 w-8 rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/80 dark:text-emerald-400 flex items-center justify-center shrink-0 shadow-2xs">
                                <Phone className="h-4 w-4" />
                              </div>
                              <div className="min-w-0">
                                <span className="text-[10px] text-slate-400 font-bold block uppercase tracking-wider">
                                  TELEFON
                                </span>
                                {citizen?.phone ? (
                                  <a
                                    href={`tel:${citizen.phone}`}
                                    className="font-bold text-emerald-700 dark:text-emerald-400 hover:underline truncate block font-mono"
                                  >
                                    {formatPhoneNumber(citizen.phone)}
                                  </a>
                                ) : (
                                  <span className="font-bold text-slate-600 dark:text-slate-400">—</span>
                                )}
                              </div>
                            </div>

                            {/* GPS Lokatsiya */}
                            <div className="flex items-center gap-2.5">
                              <div className="h-8 w-8 rounded-full bg-indigo-100 text-indigo-600 dark:bg-indigo-950/80 dark:text-indigo-400 flex items-center justify-center shrink-0 shadow-2xs">
                                <MapPin className="h-4 w-4" />
                              </div>
                              <div className="min-w-0">
                                <span className="text-[10px] text-slate-400 font-bold block uppercase tracking-wider">
                                  GPS LOKATSIYA
                                </span>
                                {citizen?.gps || inc.location_url ? (
                                  <a
                                    href={
                                      citizen?.mapUrl ||
                                      inc.location_url ||
                                      `https://maps.google.com/?q=${citizen?.gps}`
                                    }
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-1 font-bold text-sky-600 dark:text-sky-400 hover:underline truncate"
                                  >
                                    <span className="truncate">
                                      {citizen?.gps ? `GPS: ${citizen.gps}` : "Xaritada ochish"}
                                    </span>
                                    <ExternalLink className="h-3 w-3 shrink-0" />
                                  </a>
                                ) : (
                                  <span className="font-medium text-slate-400 italic">Mavjud emas</span>
                                )}
                              </div>
                            </div>

                            {/* Manzil */}
                            <div className="flex items-center gap-2.5">
                              <div className="h-8 w-8 rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950/80 dark:text-rose-400 flex items-center justify-center shrink-0 shadow-2xs">
                                <MapPin className="h-4 w-4" />
                              </div>
                              <div className="min-w-0">
                                <span className="text-[10px] text-slate-400 font-bold block uppercase tracking-wider">
                                  MANZIL
                                </span>
                                <span
                                  className="font-semibold text-slate-800 dark:text-slate-100 truncate block"
                                  title={citizen?.address || inc.address || ""}
                                >
                                  {citizen?.address || inc.address || "Toshkent shahri"}
                                </span>
                              </div>
                            </div>
                          </div>

                          {citizen?.userNote && (
                            <div className="mt-2.5 pt-2.5 border-t border-slate-200/60 dark:border-slate-700/60 text-xs text-slate-700 dark:text-slate-300">
                              <span className="font-bold text-slate-500 mr-1.5">Murojaat matni:</span>
                              &ldquo;<HighlightedText
                                text={citizen.userNote}
                                keywords={matchedRule?.keyword ? [matchedRule.keyword, ...activeKeywords] : activeKeywords}
                              />&rdquo;
                            </div>
                          )}
                        </div>
                      ) : (
                        /* === 4-RASMDEK: Telegram Kanal / Guruh Posti Bloki === */
                        inc.description && (
                          <div className="rounded-2xl bg-slate-50/70 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800/80 p-4 border-l-4 border-l-sky-500">
                            <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                              {sourceInfo.sourceType === "GROUP" ? "GURUHDAGI XABAR:" : "TELEGRAMDAGI XABAR:"}
                            </span>
                            <div className="whitespace-pre-line font-medium text-xs leading-relaxed text-slate-800 dark:text-slate-200">
                              &ldquo;<HighlightedText
                                text={inc.description.replace(/^\*+|\*+$/g, "").trim()}
                                keywords={matchedRule?.keyword ? [matchedRule.keyword, ...activeKeywords] : activeKeywords}
                              />&rdquo;
                            </div>
                          </div>
                        )
                      )}

                      {/* Rasm yoki Video ilovasi bo'lsa */}
                      {inc.media_type === "photo" && inc.media_url && (
                        <div className="pt-0.5">
                          <div className="relative inline-block rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700 bg-slate-900 group/img shadow-xs max-w-sm">
                            <img
                              src={inc.media_url}
                              alt="Hodisa rasmi"
                              className="max-h-48 w-auto object-cover group-hover/img:scale-105 transition-transform duration-300 cursor-pointer"
                              onClick={() => window.open(inc.media_url!, "_blank")}
                            />
                            <div className="absolute bottom-2 left-2 bg-black/70 backdrop-blur-xs text-white text-[11px] px-2.5 py-1 rounded-lg flex items-center gap-1.5 font-semibold">
                              <Camera className="h-3.5 w-3.5 text-sky-400" />
                              <span>📷 Rasm biriktirilgan</span>
                            </div>
                          </div>
                        </div>
                      )}

                      {inc.media_type === "video" && (
                        <div className="pt-0.5">
                          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-purple-50 dark:bg-purple-950/40 border border-purple-200 dark:border-purple-800 text-purple-800 dark:text-purple-300 text-xs font-semibold">
                            <Video className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                            <span>🎥 Video xabar biriktirilgan</span>
                            {inc.media_url && (
                              <a
                                href={inc.media_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="underline ml-1 font-bold"
                              >
                                Ochish
                              </a>
                            )}
                          </div>
                        </div>
                      )}

                      {/* 4. Pastki qator: Manba va vaqt ma'lumotlari */}
                      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-xs text-slate-500 dark:text-slate-400">
                        <div className="flex items-center gap-1.5">
                          {isCitizenCard ? (
                            <span className="inline-flex items-center gap-1.5 text-emerald-700 dark:text-emerald-400 font-semibold">
                              <Bot className="h-3.5 w-3.5" />
                              <span>Telegram Bot: Telegram Bot (Murojaatlar) (@hokimyatsuvnazorati_bot)</span>
                            </span>
                          ) : sourceInfo.sourceType === "GROUP" ? (
                            <span className="inline-flex items-center gap-1.5 text-indigo-700 dark:text-indigo-400 font-semibold">
                              <Radio className="h-3.5 w-3.5 text-indigo-500" />
                              <span>Guruh: {sourceInfo.sourceName} {sourceInfo.sourceUsername ? `(@${sourceInfo.sourceUsername})` : ""}</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1.5 text-sky-700 dark:text-sky-400 font-semibold">
                              <Radio className="h-3.5 w-3.5 text-sky-500" />
                              <span>Kanal: {sourceInfo.sourceName} {sourceInfo.sourceUsername ? `(@${sourceInfo.sourceUsername})` : ""}</span>
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-1 text-slate-400">
                          <Clock className="h-3.5 w-3.5" />
                          <span>{formatDateTime(inc.first_seen_at || inc.last_seen_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Arizani hal qilingan deb tasdiqlash modali */}
      <Modal
        isOpen={Boolean(resolveModalIncident)}
        onClose={() => setResolveModalIncident(null)}
        title={`Arizani hal qilingan deb tasdiqlash (#${resolveModalIncident?.id || ""})`}
        description="Avariya yoki muammo to'liq bartaraf etilganligini tasdiqlash va ko'rilgan choralarni qayd etish."
      >
        <div className="space-y-4 pt-2">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700 text-xs">
            <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">Ariza sarlavhasi:</span>
            <p className="text-slate-900 dark:text-white font-medium">{resolveModalIncident?.title}</p>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
              Ko&apos;rilgan choralar va Yechim izohi: <span className="text-rose-500">*</span>
            </label>
            <textarea
              value={resolutionNote}
              onChange={(e) => setResolutionNote(e.target.value)}
              placeholder="Avariya brigadasi tomonidan nosozlik bartaraf etildi, quvur almashtirildi va suv ta'minoti tiklandi..."
              rows={3}
              className="w-full rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-3 text-xs text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-brand-500/20"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setResolveModalIncident(null)}
              disabled={resolving}
            >
              Bekor qilish
            </Button>
            <Button
              type="button"
              size="sm"
              className="bg-emerald-600 hover:bg-emerald-500 text-white font-bold"
              onClick={handleConfirmResolve}
              disabled={resolving || !resolutionNote.trim()}
            >
              {resolving ? "Saqlanmoqda..." : "Tasdiqlash va Hal qilindi deb belgilash"}
            </Button>
          </div>
        </div>
      </Modal>
    </AppShell>
  );
}
