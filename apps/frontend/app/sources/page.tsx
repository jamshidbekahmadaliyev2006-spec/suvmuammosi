"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Radio,
  Plus,
  Search,
  CheckCircle2,
  XCircle,
  Edit2,
  Trash2,
  ExternalLink,
  Sparkles,
  Loader2,
  RefreshCw,
  Clock,
  Layers,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Check,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import { Alert } from "@/components/ui/alert";
import { api } from "@/lib/api";
import { MonitoringSource, Page, SourceType } from "@/types";
import { formatDateTime, sourceTypeLabel } from "@/lib/utils";

const SOURCE_TYPE_OPTIONS: { value: SourceType; label: string }[] = [
  { value: "CHANNEL", label: "Telegram Kanal" },
  { value: "GROUP", label: "Telegram Guruh" },
];

const PAGE_SIZE_OPTIONS = [
  { value: "20", label: "20 tadan" },
  { value: "50", label: "50 tadan" },
  { value: "100", label: "100 tadan (Barchasi)" },
];

export default function SourcesPage() {
  const [data, setData] = useState<Page<MonitoringSource> | null>(null);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(100);

  // Sinxronizatsiya holati (10 kunlik arxivni barcha kanallardan tortib kelish)
  const [syncingAll, setSyncingAll] = useState(false);
  const [syncingSourceId, setSyncingSourceId] = useState<number | null>(null);
  const [syncBanner, setSyncBanner] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  // Modal (Qo'shish / Tahrirlash)
  const [modalOpen, setModalOpen] = useState(false);
  const [editingSource, setEditingSource] = useState<MonitoringSource | null>(null);

  // Forma maydonlari
  const [formName, setFormName] = useState("");
  const [formChatId, setFormChatId] = useState("");
  const [formUsername, setFormUsername] = useState("");
  const [formType, setFormType] = useState<SourceType>("CHANNEL");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [resolvedStatus, setResolvedStatus] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listSources({
        q: query.trim() || undefined,
        page,
        page_size: pageSize,
      });
      setData(res);
    } catch {
      // xatolik
    } finally {
      setLoading(false);
    }
  }, [query, page, pageSize]);

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  // 10 kunlik barcha kanallarni sinxronlash
  const handleSyncAllHistory = async (daysBack: number = 10) => {
    setSyncingAll(true);
    setSyncBanner({
      type: "info",
      message: `Barcha ${data?.total || 50}+ ta kanaldan so'nggi ${daysBack} kunlik xabarlar tortilmoqda va kalit so'zlar bo'yicha tahlil qilinmoqda...`,
    });

    try {
      const res = await api.syncSourcesHistory(daysBack);
      setSyncBanner({
        type: "success",
        message: `Muvaffaqiyatli yakunlandi! ${res.synced_sources} ta kanal skanerlandi, ${res.total_messages_synced} ta xabar tekshirildi va ${res.rescanned_incidents} ta yangi hodisa aniqlandi.`,
      });
      await fetchSources();
    } catch (err: any) {
      setSyncBanner({
        type: "error",
        message: err.message || "Xabarlarni sinxronlashda xatolik yuz berdi.",
      });
    } finally {
      setSyncingAll(false);
    }
  };

  // Alohida bitta kanalni sinxronlash
  const handleSyncSingleSource = async (source: MonitoringSource) => {
    setSyncingSourceId(source.id);
    try {
      const res = await api.syncSingleSource(source.id, 10);
      setSyncBanner({
        type: "success",
        message: `«${source.name}» kanali yangilandi: ${res.messages_synced} ta yangi xabar, ${res.rescanned_incidents} ta yangi hodisa!`,
      });
      await fetchSources();
    } catch (err: any) {
      alert(err.message || "Kanalni yangilashda xatolik yuz berdi.");
    } finally {
      setSyncingSourceId(null);
    }
  };

  const openAddModal = () => {
    setEditingSource(null);
    setFormName("");
    setFormChatId("");
    setFormUsername("");
    setFormType("CHANNEL");
    setFormError(null);
    setResolvedStatus(null);
    setModalOpen(true);
  };

  const openEditModal = (source: MonitoringSource) => {
    setEditingSource(source);
    setFormName(source.name);
    setFormChatId(String(source.telegram_chat_id));
    setFormUsername(source.telegram_username || "");
    setFormType(source.source_type);
    setFormError(null);
    setResolvedStatus(null);
    setModalOpen(true);
  };

  const handleAutoResolve = async (inputVal: string) => {
    const raw = inputVal.trim();
    if (!raw) return;

    setResolving(true);
    setResolvedStatus(null);
    setFormError(null);

    try {
      const res = await api.resolveSource(raw);
      if (res) {
        if (!formName || formName === formUsername || formName.startsWith("http")) {
          setFormName(res.name);
        }
        setFormUsername(res.telegram_username);
        setFormChatId(String(res.telegram_chat_id));
        setFormType(res.source_type);

        if (res.resolved) {
          setResolvedStatus(`✓ Topildi: «${res.name}»`);
        } else {
          setResolvedStatus(`✓ @${res.telegram_username}`);
        }
      }
    } catch {
      const clean = raw
        .replace(/^https?:\/\/(t\.me|telegram\.me)\//i, "")
        .replace(/^@/, "")
        .split("/")[0]
        .split("?")[0];
      setFormUsername(clean);
      if (!formName) setFormName(clean);
    } finally {
      setResolving(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanUser = formUsername
      .trim()
      .replace(/^https?:\/\/(t\.me|telegram\.me)\//i, "")
      .replace(/^@/, "")
      .split("/")[0]
      .split("?")[0];

    const finalName = formName.trim() || cleanUser || "Telegram Kanal";

    setSubmitting(true);
    setFormError(null);

    try {
      if (editingSource) {
        await api.updateSource(editingSource.id, {
          name: finalName,
          telegram_username: cleanUser || undefined,
          telegram_chat_id: formChatId ? parseInt(formChatId, 10) : undefined,
          source_type: formType,
        });
      } else {
        await api.createSource({
          name: finalName,
          telegram_username: cleanUser,
          telegram_chat_id: formChatId ? parseInt(formChatId, 10) : undefined,
          source_type: formType,
          is_active: true,
        });
      }
      setModalOpen(false);
      setSyncBanner({
        type: "success",
        message: `«${finalName}» manbasi muvaffaqiyatli qo'shildi va uning 10 kunlik xabarlari avtomatik tahlil qilindi!`,
      });
      await fetchSources();
    } catch (err: any) {
      setFormError(err.message || "Manbani saqlashda xatolik yuz berdi.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggleActive = async (source: MonitoringSource) => {
    try {
      await api.updateSource(source.id, {
        is_active: !source.is_active,
      });
      await fetchSources();
    } catch (err: any) {
      alert(err.message || "Holatni o'zgartirishda xatolik yuz berdi.");
    }
  };

  const handleDeleteSource = async (source: MonitoringSource) => {
    if (!confirm(`«${source.name}» manbasini ro'yxatdan butunlay o'chirmoqchimisiz?`)) {
      return;
    }
    try {
      await api.deleteSource(source.id);
      await fetchSources();
    } catch (err: any) {
      alert(err.message || "Manbani o'chirishda xatolik yuz berdi.");
    }
  };

  const activeCount = data?.items.filter((s) => s.is_active).length ?? 0;
  const totalPages = data ? Math.max(1, Math.ceil(data.total / pageSize)) : 1;

  return (
    <AppShell
      title="Telegram monitoring manbalari"
      subtitle="Kuzatilayotgan barcha ommaviy kanallar, guruhlar va tizim murojaat boti"
      onRefresh={fetchSources}
      isRefreshing={loading}
    >
      <div className="space-y-6">
        {/* Yuqori axborot va monitoring statistikasi paneli */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="rounded-2xl border border-blue-100 bg-gradient-to-br from-blue-50/70 to-indigo-50/40 p-4 dark:border-blue-900/40 dark:from-blue-950/20 dark:to-indigo-950/10 flex items-center gap-3.5 shadow-sm">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white shadow-md shadow-blue-500/25">
              <Radio className="h-6 w-6" />
            </div>
            <div>
              <div className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {data?.total ?? 0} ta
              </div>
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Ulangan jami Telegram manbalari
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50/70 to-teal-50/40 p-4 dark:border-emerald-900/40 dark:from-emerald-950/20 dark:to-teal-950/10 flex items-center gap-3.5 shadow-sm">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-md shadow-emerald-500/25">
              <ShieldCheck className="h-6 w-6" />
            </div>
            <div>
              <div className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
                {activeCount} ta faol
              </div>
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Doimiy monitoring va qidiruvda
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-amber-100 bg-gradient-to-br from-amber-50/70 to-orange-50/40 p-4 dark:border-amber-900/40 dark:from-amber-950/20 dark:to-orange-950/10 flex items-center gap-3.5 shadow-sm">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-amber-500 text-white shadow-md shadow-amber-500/25">
              <Sparkles className="h-6 w-6" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-tight text-slate-900 dark:text-white">
                Jonli Monitoring
              </div>
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Xabarlar tushishi bilan avto-aniqlanadi
              </div>
            </div>
          </div>
        </div>

        {/* Xabarnoma / Natija banneri */}
        {syncBanner && (
          <div
            className={`rounded-2xl p-4 text-sm flex items-start justify-between gap-3 shadow-sm transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${
              syncBanner.type === "success"
                ? "bg-emerald-50/90 border border-emerald-200 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-200"
                : syncBanner.type === "info"
                ? "bg-blue-50/90 border border-blue-200 text-blue-900 dark:bg-blue-950/40 dark:border-blue-900 dark:text-blue-200"
                : "bg-rose-50/90 border border-rose-200 text-rose-900 dark:bg-rose-950/40 dark:border-rose-900 dark:text-rose-200"
            }`}
          >
            <div className="flex items-center gap-2.5">
              {syncBanner.type === "info" ? (
                <Loader2 className="h-5 w-5 animate-spin text-blue-600 shrink-0" />
              ) : syncBanner.type === "success" ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              ) : (
                <XCircle className="h-5 w-5 text-rose-600 shrink-0" />
              )}
              <span className="font-medium">{syncBanner.message}</span>
            </div>
            <button
              onClick={() => setSyncBanner(null)}
              className="text-xs font-semibold opacity-70 hover:opacity-100 transition-opacity"
            >
              Yopish
            </button>
          </div>
        )}

        {/* Boshqaruv paneli (Qidiruv va Qo'shish) */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900/60 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-sm">
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
            <Input
              type="search"
              placeholder="Kanal nomi yoki username..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              className="pl-9 bg-slate-50 dark:bg-slate-800/60 rounded-xl"
            />
          </div>

          <div className="flex items-center gap-2.5">
            <Button onClick={openAddModal} className="flex items-center gap-1.5 shadow-sm">
              <Plus className="h-4 w-4" />
              Yangi manba qo'shish
            </Button>
          </div>
        </div>

        {/* Manbalar ro'yxati jadvali */}
        <Card className="overflow-hidden border border-slate-200/80 dark:border-slate-800 shadow-sm rounded-2xl">
          <CardHeader className="border-b border-slate-100 bg-slate-50/70 p-4 dark:border-slate-800 dark:bg-slate-900/70">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Radio className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                <CardTitle className="text-sm font-semibold">
                  Barcha monitoring manbalari ({data?.total ?? 0})
                </CardTitle>
                <Badge variant="outline" className="text-xs bg-brand-50 text-brand-700 border-brand-200 dark:bg-brand-950/40 dark:text-brand-300 dark:border-brand-900">
                  {data?.items.length ?? 0} ta ko'rsatilmoqda
                </Badge>
              </div>
            </div>
          </CardHeader>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
              <thead className="border-b border-slate-100 bg-slate-50/90 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:border-slate-800 dark:bg-slate-900/90 dark:text-slate-400">
                <tr>
                  <th className="py-3.5 px-4">#</th>
                  <th className="py-3.5 px-4">Manba nomi</th>
                  <th className="py-3.5 px-4">Turi</th>
                  <th className="py-3.5 px-4">Username / Havola</th>
                  <th className="py-3.5 px-4">Holati</th>
                  <th className="py-3.5 px-4">Oxirgi xabar</th>
                  <th className="py-3.5 px-4 text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {loading ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-400">
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="h-5 w-5 animate-spin text-brand-600" />
                        <span>Manbalar yuklanmoqda...</span>
                      </div>
                    </td>
                  </tr>
                ) : !data || data.items.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="py-12 text-center text-slate-400">
                      Hech qanday manba topilmadi.
                    </td>
                  </tr>
                ) : (
                  data.items.map((src, index) => {
                    const rowNumber = (page - 1) * pageSize + index + 1;
                    const isRowSyncing = syncingSourceId === src.id;

                    return (
                      <tr
                        key={src.id}
                        className={`transition-colors hover:bg-slate-50/80 dark:hover:bg-slate-800/40 ${
                          !src.is_active ? "opacity-60 bg-slate-50/40 dark:bg-slate-900/40" : ""
                        }`}
                      >
                        <td className="py-3.5 px-4 text-xs font-mono text-slate-400">
                          {rowNumber}
                        </td>
                        <td className="py-3.5 px-4 font-semibold text-slate-900 dark:text-slate-100">
                          <div className="flex items-center gap-2">
                            <span>{src.name}</span>
                            {src.telegram_username && (
                              <span className="text-xs font-normal text-slate-400">
                                (@{src.telegram_username})
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <Badge variant="outline">{sourceTypeLabel(src.source_type)}</Badge>
                        </td>
                        <td className="py-3.5 px-4">
                          {src.telegram_username ? (
                            <a
                              href={`https://t.me/${src.telegram_username}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-brand-600 hover:underline dark:text-brand-400 font-medium"
                            >
                              t.me/{src.telegram_username}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          ) : (
                            <span className="text-xs text-slate-400">—</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4">
                          <button
                            onClick={() => handleToggleActive(src)}
                            title={src.is_active ? "O'chirib qo'yish" : "Faollashtirish"}
                            className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border transition-colors ${
                              src.is_active
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-400 dark:border-emerald-900"
                                : "bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
                            }`}
                          >
                            {src.is_active ? (
                              <>
                                <CheckCircle2 className="h-3.5 w-3.5" /> Faol
                              </>
                            ) : (
                              <>
                                <XCircle className="h-3.5 w-3.5" /> Nofaol
                              </>
                            )}
                          </button>
                        </td>
                        <td className="py-3.5 px-4 text-xs text-slate-400">
                          {src.last_message_at ? (
                            formatDateTime(src.last_message_at)
                          ) : (
                            <span className="text-slate-400 italic">Kutilmoqda</span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => openEditModal(src)}
                              title="Tahrirlash"
                            >
                              <Edit2 className="h-3.5 w-3.5 mr-1" /> Tahrirlash
                            </Button>

                            <Button
                              size="sm"
                              variant="outline"
                              className="text-rose-600 hover:bg-rose-50 hover:text-rose-700 border-rose-200 dark:border-rose-900/50 dark:text-rose-400 dark:hover:bg-rose-950/40 p-2"
                              onClick={() => handleDeleteSource(src)}
                              title="Manbani o'chirish"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Pastki sahifalash (Pagination) paneli */}
          {data && data.total > 0 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100 bg-slate-50/60 p-4 dark:border-slate-800 dark:bg-slate-900/60 text-xs text-slate-500 dark:text-slate-400">
              <div>
                Jami <span className="font-semibold text-slate-800 dark:text-slate-200">{data.total}</span> ta manbadan{" "}
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {Math.min((page - 1) * pageSize + 1, data.total)}-
                  {Math.min(page * pageSize, data.total)}
                </span>{" "}
                ko'rsatilmoqda
              </div>

              {totalPages > 1 && (
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page <= 1}
                    className="h-8 px-2.5"
                  >
                    <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Avvalgi
                  </Button>

                  <span className="px-2 font-medium">
                    {page} / {totalPages}
                  </span>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page >= totalPages}
                    className="h-8 px-2.5"
                  >
                    Keyingi <ChevronRight className="h-3.5 w-3.5 ml-1" />
                  </Button>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Yangi Manba qo'shish modali */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingSource ? "Manbani tahrirlash" : "Yangi Telegram manbasi qo'shish"}
      >
        <form onSubmit={handleSave} className="space-y-4">
          {formError && <Alert type="error">{formError}</Alert>}

          {/* 1. Kanal yoki Guruh havolasi */}
          <div>
            <label className="mb-1 block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Kanal yoki Guruh havolasi <span className="text-rose-500">*</span>
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="https://t.me/yangiliklar yoki @yangiliklar"
                value={formUsername}
                onChange={(e) => {
                  setFormUsername(e.target.value);
                  setResolvedStatus(null);
                }}
                onBlur={() => {
                  if (formUsername.trim() && !resolvedStatus && !editingSource) {
                    handleAutoResolve(formUsername);
                  }
                }}
                className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
                required
              />
              <Button
                type="button"
                variant="outline"
                size="md"
                onClick={() => handleAutoResolve(formUsername)}
                disabled={resolving || !formUsername.trim()}
                className="shrink-0 gap-1.5"
                title="Telegramdan avtomatik aniqlash"
              >
                {resolving ? (
                  <Loader2 className="h-4 w-4 animate-spin text-brand-600" />
                ) : (
                  <Sparkles className="h-4 w-4 text-brand-600 dark:text-brand-400" />
                )}
                <span>{resolving ? "..." : "Aniqlash"}</span>
              </Button>
            </div>
          </div>

          {/* Aniqlangan status */}
          {resolvedStatus && (
            <div className="rounded-xl border border-emerald-200 bg-emerald-50/90 py-2.5 px-3.5 text-xs text-emerald-800 dark:border-emerald-900/50 dark:bg-emerald-950/40 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
              <span className="font-semibold">{resolvedStatus}</span>
            </div>
          )}

          {/* 2. Manba nomi */}
          <Input
            label="Manba nomi"
            placeholder="Avtomatik to'ldiriladi (masalan: Gazeta.uz)"
            value={formName}
            onChange={(e) => setFormName(e.target.value)}
          />

          {/* 3. Manba turi */}
          <Select
            label="Manba turi"
            options={SOURCE_TYPE_OPTIONS}
            value={formType}
            onChange={(e) => setFormType(e.target.value as SourceType)}
          />

          <div className="flex justify-end gap-2.5 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="outline"
              size="md"
              onClick={() => setModalOpen(false)}
            >
              Bekor qilish
            </Button>
            <Button type="submit" size="md" loading={submitting}>
              {editingSource ? "Saqlash" : "Qo'shish"}
            </Button>
          </div>
        </form>
      </Modal>
    </AppShell>
  );
}
