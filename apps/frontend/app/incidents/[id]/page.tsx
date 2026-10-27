"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  AlertTriangle,
  Building2,
  Clock,
  CheckCircle2,
  MapPin,
  ExternalLink,
  MessageSquare,
  History,
  Send,
  Edit3,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Select } from "@/components/ui/select";
import { Alert } from "@/components/ui/alert";
import { api, ApiError } from "@/lib/api";
import {
  HistoryItem,
  IncidentCategory,
  IncidentDetail,
  IncidentStatus,
  Priority,
  DetectionRule,
} from "@/types";
import {
  categoryLabel,
  formatDateTime,
  priorityBadgeClass,
  priorityLabel,
  statusBadgeClass,
  statusLabel,
} from "@/lib/utils";
import { HighlightedText } from "@/components/ui/highlighted-text";

const STATUS_SELECT_OPTIONS: { value: IncidentStatus; label: string }[] = [
  { value: "OPEN", label: "Hal qilinmagan" },
  { value: "RESOLVED", label: "Hal qilingan" },
];

export default function IncidentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const incidentId = Number(params.id);

  const [incident, setIncident] = useState<IncidentDetail | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [rules, setRules] = useState<DetectionRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status o'zgartirish modali
  const [modalOpen, setModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState<IncidentStatus>("IN_PROGRESS");
  const [statusComment, setStatusComment] = useState("");
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [submittingStatus, setSubmittingStatus] = useState(false);

  // Yangi izoh qo'shish
  const [commentText, setCommentText] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

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

  // Qoidalar xaritasi va aynan qaysi kalit so'zdan ekanligini aniqlash
  const rulesMap = useMemo(() => {
    const map = new Map<number, DetectionRule>();
    rules.forEach((r) => map.set(r.id, r));
    return map;
  }, [rules]);

  const matchedRule = useMemo((): DetectionRule | null => {
    if (!incident) return null;
    if (incident.matched_rule_ids && incident.matched_rule_ids.length > 0) {
      for (const id of incident.matched_rule_ids) {
        const rule = rulesMap.get(id);
        if (rule) return rule;
      }
    }
    if (incident.first_message?.matched_rule_ids && incident.first_message.matched_rule_ids.length > 0) {
      for (const id of incident.first_message.matched_rule_ids) {
        const rule = rulesMap.get(id);
        if (rule) return rule;
      }
    }
    // Agar bazada matched_rule_ids bo'sh bo'lsa, qoidalar matni bo'yicha mosini topamiz
    const text = `${incident.title || ""} ${incident.description || ""} ${incident.first_message?.message_text || ""}`.toLowerCase();
    for (const rule of rules) {
      if (!rule.keyword) continue;
      const cleanKw = rule.keyword.replace(/[.,!?:;\"'()\[\]{}]/g, " ").trim().toLowerCase();
      if (cleanKw && text.includes(cleanKw)) {
        return rule;
      }
    }
    return null;
  }, [incident, rulesMap, rules]);

  const loadData = useCallback(async () => {
    if (!incidentId || isNaN(incidentId)) return;
    setLoading(true);
    try {
      const [incData, histData, rulesData] = await Promise.all([
        api.getIncident(incidentId),
        api.getIncidentHistory(incidentId),
        api.listRules({ is_active: true, page_size: 100 }).catch(() => ({ items: [] })),
      ]);
      setIncident(incData);
      setHistory(histData);
      setRules((rulesData as any).items || []);
      setNewStatus(incData.status);
      setResolutionNotes(incData.resolution_notes || "");
      setError(null);
    } catch {
      setError("Hodisa topilmadi yoki yuklashda xatolik yuz berdi.");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleStatusChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingStatus(true);
    try {
      await api.updateIncident(incidentId, {
        status: newStatus,
        comment: statusComment.trim() || undefined,
        resolution_notes:
          newStatus === "RESOLVED" ? resolutionNotes.trim() || undefined : undefined,
      });
      setModalOpen(false);
      setStatusComment("");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Statusni o'zgartirishda xatolik yuz berdi.");
    } finally {
      setSubmittingStatus(false);
    }
  };

  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setSubmittingComment(true);
    try {
      await api.addComment(incidentId, commentText.trim());
      setCommentText("");
      await loadData();
    } catch (err: any) {
      alert(err.message || "Izoh qo'shishda xatolik yuz berdi.");
    } finally {
      setSubmittingComment(false);
    }
  };

  if (loading) {
    return (
      <AppShell title="Hodisa tafsilotlari">
        <div className="flex h-64 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-500 border-t-transparent" />
        </div>
      </AppShell>
    );
  }

  if (error || !incident) {
    return (
      <AppShell title="Xatolik">
        <Alert type="error" className="mb-4">
          {error || "Hodisa ma'lumotlari mavjud emas."}
        </Alert>
        <Link href="/incidents">
          <Button variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" /> Hodisalar ro'yxatiga qaytish
          </Button>
        </Link>
      </AppShell>
    );
  }

  return (
    <AppShell
      title={`Hodisa #${incident.id}: ${incident.title}`}
      subtitle="Batafsil ma'lumot, Telegram asosi va statuslar tarixi"
      onRefresh={loadData}
    >
      <div className="space-y-6">
        {/* Yuqori orqaga qaytish va boshqaruv */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/incidents"
            className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
          >
            <ArrowLeft className="h-4 w-4" /> Barcha hodisalarga qaytish
          </Link>

          <Button onClick={() => setModalOpen(true)} className="gap-2">
            <Edit3 className="h-4 w-4" /> Holatni o'zgartirish
          </Button>
        </div>

        {/* 1. Asosiy Hodisa Kartasi */}
        <Card className="p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                {/* AI Tahlil guruhi va holati */}
                {(incident.report_type === "NEWS" || incident.report_type === "YANGILIK") ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sky-50 text-sky-700 border border-sky-300 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-800 shadow-2xs">
                    <span>🔵</span> OAV Yangiligi (Ma&apos;lumot uchun)
                  </span>
                ) : (incident.report_type === "GRATITUDE" || incident.report_type === "MINNATDORCHILIK" || incident.report_type === "TASHAKKUR") ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-300 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800 shadow-2xs">
                    <span>🙏</span> Minnatdorchilik (Hal etilgan)
                  </span>
                ) : (incident.report_type === "ANNOUNCEMENT" || incident.report_type === "RASMIY_ELON") ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800 shadow-2xs">
                    <span>📢</span> Rasmiy e&apos;lon (Rejali)
                  </span>
                ) : (incident.report_type === "IRRELEVANT" || incident.status === "INVALID") ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-300 dark:bg-slate-800 dark:text-slate-400">
                    <span>⚪</span> Noto&apos;g&apos;ri / Reklama
                  </span>
                ) : incident.status === "RESOLVED" ? (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 dark:bg-emerald-950/60 dark:text-emerald-300 dark:border-emerald-800 shadow-2xs">
                    <span>🟢</span> Ariza: Hal qilingan
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-100 text-rose-800 border border-rose-300 dark:bg-rose-950/60 dark:text-rose-300 dark:border-rose-800 shadow-2xs">
                    <span>🔴</span> Ariza: Hal qilinmagan
                  </span>
                )}

                {/* Qaysi kalit so'z bo'yicha aniqlanganligi (faqat 1 ta asosiy nishon) */}
                {matchedRule && (
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-bold text-amber-900 border border-amber-300 dark:bg-amber-950/70 dark:border-amber-800 dark:text-amber-200 shadow-2xs">
                    <span className="text-[10px] text-amber-600 dark:text-amber-400 font-extrabold uppercase">Kalit so'z:</span>
                    <span className="underline decoration-amber-500 decoration-[2px] underline-offset-2 font-black">
                      «{matchedRule.keyword?.replace(/\.$/, "")}»
                    </span>
                  </span>
                )}
              </div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">
                {incident.title}
              </h2>

              {incident.ai_summary && (
                <div className="mt-2.5 rounded-xl border border-purple-200/80 bg-purple-50/70 p-3 text-xs text-purple-950 dark:border-purple-800/60 dark:bg-purple-950/30 dark:text-purple-200 shadow-2xs flex items-start gap-2">
                  <span className="font-bold text-purple-700 dark:text-purple-400 shrink-0">✨ Groq AI Xulosasi:</span>
                  <span className="leading-relaxed">{incident.ai_summary}</span>
                </div>
              )}
            </div>

            <div className="text-right text-xs text-slate-400 space-y-1">
              <div>Birinchi qayd: {formatDateTime(incident.first_seen_at)}</div>
              <div>Oxirgi yangilanish: {formatDateTime(incident.updated_at)}</div>
            </div>
          </div>

          {incident.description && (
            <div className="mt-4 text-sm text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 p-4 rounded-xl dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800">
              <HighlightedText
                text={incident.description}
                keywords={matchedRule?.keyword ? [matchedRule.keyword, ...activeKeywords] : activeKeywords}
              />
            </div>
          )}

          {/* Manzil / Hudud (Hokimiyat darajasida) */}
          <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50/60 p-4 text-sm dark:border-amber-900/50 dark:bg-amber-950/20">
            <h4 className="font-bold text-amber-900 dark:text-amber-300 flex items-center gap-2 mb-2">
              <MapPin className="h-4 w-4 text-rose-500" />
              Hodisa aniqlangan hudud va manzil:
            </h4>
            <div className="flex flex-wrap items-center gap-3">
              {incident.district && (
                <div className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 font-bold text-amber-950 border border-amber-200 dark:bg-slate-900 dark:text-amber-200 shadow-sm text-xs">
                  <Building2 className="h-3.5 w-3.5 text-amber-600" />
                  Shahar / Tuman: <span className="text-amber-700 dark:text-amber-400">{incident.district}</span>
                </div>
              )}
              {incident.address && (
                <div className="inline-flex items-center gap-1.5 rounded-lg bg-white px-3 py-1.5 font-semibold text-rose-950 border border-rose-200 dark:bg-slate-900 dark:text-rose-200 shadow-sm text-xs">
                  <MapPin className="h-3.5 w-3.5 text-rose-600" />
                  Aniq Manzil: <span className="text-rose-700 dark:text-rose-400">{incident.address}</span>
                </div>
              )}
              {!incident.district && !incident.address && (
                <span className="text-xs text-slate-500 italic">Xabar matnida aniq shahar yoki tuman ko'rsatilmagan.</span>
              )}
            </div>
          </div>

          {/* Hal qilish bo'yicha qaydlar */}
          {incident.resolution_notes && (
            <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 text-sm dark:border-emerald-900/50 dark:bg-emerald-950/20">
              <h4 className="font-semibold text-emerald-800 dark:text-emerald-300 flex items-center gap-1.5 mb-1">
                <CheckCircle2 className="h-4 w-4" /> Hal qilish bo'yicha qayd:
              </h4>
              <p className="text-emerald-900 dark:text-emerald-200 text-xs">
                {incident.resolution_notes}
              </p>
              {incident.resolved_at && (
                <span className="block mt-2 text-[11px] text-emerald-600 dark:text-emerald-400">
                  Hal qilingan vaqti: {formatDateTime(incident.resolved_at)}
                </span>
              )}
            </div>
          )}
        </Card>

        {/* 2. Ikki ustun: Telegram Asl Xabari va Statuslar Tarixi */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Asl Telegram xabari */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-sky-600" />
                Telegramdagi asl xabar
              </CardTitle>
            </CardHeader>

            {incident.first_message ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-xs text-slate-500 pb-2 border-b border-slate-100 dark:border-slate-800">
                  <div>
                    <span className="font-semibold text-slate-700 dark:text-slate-300">
                      Manba:
                    </span>{" "}
                    {incident.source_name}
                    {incident.source_username && (
                      <a
                        href={`https://t.me/${incident.source_username}`}
                        target="_blank"
                        rel="noreferrer"
                        className="ml-1 font-semibold text-sky-600 hover:underline dark:text-sky-400"
                      >
                        (@{incident.source_username})
                      </a>
                    )}
                  </div>
                  <div>
                    {formatDateTime(incident.first_seen_at)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4 text-xs font-mono text-slate-800 dark:bg-slate-800/60 dark:text-slate-200 whitespace-pre-wrap leading-relaxed">
                  <HighlightedText
                    text={incident.first_message.message_text}
                    keywords={matchedRule?.keyword ? [matchedRule.keyword, ...activeKeywords] : activeKeywords}
                  />
                </div>

                <div className="pt-2">
                  {(() => {
                    const descUrl = incident.description?.match(/https:\/\/t\.me\/(?:c\/\d+|\w+)(?:\/\d+)+/)?.[0];
                    const directUrl =
                      incident.message_url ||
                      incident.first_message?.message_url ||
                      descUrl ||
                      (incident.source_username ? `https://t.me/${incident.source_username}` : "");
                    if (!directUrl) return null;
                    return (
                      <a
                        href={directUrl}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white px-4 py-2 text-xs font-bold shadow transition-colors"
                        title={incident.source_type === "GROUP" ? "Guruhdagi xabarni ochish" : (directUrl.includes("/") ? "Telegramdagi xabarni ochish" : "Telegramda ochish")}
                      >
                        <Send className="h-3.5 w-3.5" />
                        Telegramda ochish <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    );
                  })()}
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 py-4">
                Asl Telegram xabari topilmadi.
              </p>
            )}
          </Card>

          {/* Statuslar tarixi */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <History className="h-4 w-4 text-amber-600" />
                Statuslar o'zgarish tarixi
              </CardTitle>
            </CardHeader>

            {history.length === 0 ? (
              <p className="text-xs text-slate-400 py-4">
                Hozircha status o'zgarishlari qayd etilmagan.
              </p>
            ) : (
              <div className="relative border-l-2 border-slate-200 pl-4 space-y-4 dark:border-slate-800">
                {history.map((h) => (
                  <div key={h.id} className="relative">
                    <div className="absolute -left-[21px] top-1 h-2.5 w-2.5 rounded-full bg-brand-500 border-2 border-white dark:border-slate-900" />
                    <div className="flex items-center gap-2 text-xs">
                      <span className="font-semibold text-slate-900 dark:text-slate-100">
                        {statusLabel(h.new_status)}
                      </span>
                      {h.old_status && (
                        <span className="text-slate-400">
                          (avval: {statusLabel(h.old_status)})
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {h.changed_by_username || "Tizim"} tomonidan •{" "}
                      {formatDateTime(h.created_at)}
                    </div>
                    {h.comment && (
                      <p className="mt-1 text-xs text-slate-600 dark:text-slate-300 italic">
                        "{h.comment}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* 3. Izohlar Bo'limi */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-brand-600" />
              Izohlar va tezkor qaydlar ({incident.comments.length})
            </CardTitle>
          </CardHeader>

          {/* Izohlar ro'yxati */}
          <div className="space-y-3 mb-6">
            {incident.comments.length === 0 ? (
              <p className="text-xs text-slate-400 py-2">
                Ushbu hodisaga hali hech qanday izoh qoldirilmagan.
              </p>
            ) : (
              incident.comments.map((c) => (
                <div
                  key={c.id}
                  className="rounded-xl border border-slate-100 bg-slate-50/50 p-3.5 text-xs dark:border-slate-800 dark:bg-slate-800/30"
                >
                  <div className="flex items-center justify-between text-slate-500 mb-1">
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {c.username}
                    </span>
                    <span className="text-[11px]">
                      {formatDateTime(c.created_at)}
                    </span>
                  </div>
                  <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                    {c.comment}
                  </p>
                </div>
              ))
            )}
          </div>

          {/* Yangi izoh yozish formasi */}
          <form onSubmit={handleAddComment} className="flex gap-2">
            <input
              type="text"
              placeholder="Hodisa yuzasidan izoh yoki qayd yozing..."
              value={commentText}
              onChange={(e) => setCommentText(e.target.value)}
              disabled={submittingComment}
              className="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-xs text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
            <Button
              type="submit"
              size="md"
              loading={submittingComment}
              disabled={!commentText.trim()}
              className="gap-1.5"
            >
              <Send className="h-3.5 w-3.5" /> Yuborish
            </Button>
          </form>
        </Card>
      </div>

      {/* Statusni o'zgartirish modali */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title="Hodisa holatini o'zgartirish"
        description="Foydalanuvchi tekshiruvi natijasida yangi status belgilash."
      >
        <form onSubmit={handleStatusChange} className="space-y-4">
          <Select
            label="Yangi holat"
            options={STATUS_SELECT_OPTIONS}
            value={newStatus}
            onChange={(e) => setNewStatus(e.target.value as IncidentStatus)}
          />

          {newStatus === "RESOLVED" && (
            <div>
              <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                Hal qilish bo'yicha qayd (Resolution Notes)
              </label>
              <textarea
                rows={3}
                placeholder="Muammo qanday bartaraf etildi? Masalan: Quvur payvandlandi, suv uzatish tiklandi."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white p-3 text-xs text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              />
            </div>
          )}

          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              O'zgarish sababi / Tarix uchun izoh
            </label>
            <input
              type="text"
              placeholder="Masalan: Tezkor brigada jo'natildi"
              value={statusComment}
              onChange={(e) => setStatusComment(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white p-2.5 text-xs text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={() => setModalOpen(false)}
            >
              Bekor qilish
            </Button>
            <Button type="submit" size="md" loading={submittingStatus}>
              Tasdiqlash va Saqlash
            </Button>
          </div>
        </form>
      </Modal>
    </AppShell>
  );
}
