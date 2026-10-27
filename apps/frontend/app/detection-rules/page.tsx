"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  KeyRound,
  Plus,
  Search,
  Check,
  X,
  Edit2,
  CheckCircle2,
  XCircle,
  Trash2,
  Radio,
  Sparkles,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import { Alert } from "@/components/ui/alert";
import { api } from "@/lib/api";
import { DetectionRule, Page } from "@/types";
import { formatDateTime } from "@/lib/utils";

export default function DetectionRulesPage() {
  const [data, setData] = useState<Page<DetectionRule> | null>(null);
  const [loading, setLoading] = useState(true);

  // Qidiruv filtri
  const [query, setQuery] = useState("");
  const [debouncedQuery, setDebouncedQuery] = useState("");
  const [page, setPage] = useState(1);

  // Xabarlar bo'yicha tahlil bildirishnomasi
  const [banner, setBanner] = useState<{
    type: "success" | "info" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedQuery(query);
    }, 250);
    return () => clearTimeout(handler);
  }, [query]);

  // Modal (Faqat kalit so'z kiritiladi)
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<DetectionRule | null>(null);
  const [formKeyword, setFormKeyword] = useState("");
  const [formIsActive, setFormIsActive] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchRules = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.listRules({
        q: debouncedQuery.trim() || undefined,
        page,
        page_size: 50,
      });
      setData(res);
    } catch {
      // xatolik
    } finally {
      setLoading(false);
    }
  }, [debouncedQuery, page]);

  useEffect(() => {
    fetchRules();
  }, [fetchRules]);

  const openAddModal = () => {
    setEditingRule(null);
    setFormKeyword("");
    setFormIsActive(true);
    setFormError(null);
    setModalOpen(true);
  };

  const openEditModal = (rule: DetectionRule) => {
    setEditingRule(rule);
    setFormKeyword(rule.keyword);
    setFormIsActive(rule.is_active);
    setFormError(null);
    setModalOpen(true);
  };

  const handleSaveRule = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalKeyword = formKeyword.trim();
    if (!finalKeyword) {
      setFormError("Kalit so'zni kiriting.");
      return;
    }

    setSubmitting(true);
    setFormError(null);

    try {
      if (editingRule) {
        await api.updateRule(editingRule.id, {
          name: finalKeyword,
          keyword: finalKeyword,
          category: editingRule.category || "PIPE_BURST",
          match_type: "PHRASE",
          priority: 50,
          is_active: formIsActive,
        });
      } else {
        await api.createRule({
          name: finalKeyword,
          keyword: finalKeyword,
          category: "PIPE_BURST",
          match_type: "PHRASE",
          priority: 50,
          is_active: true,
        });
      }
      setModalOpen(false);
      await fetchRules();

      // Kalit so'z kiritilgach, avtomatik ravishda barcha xabarlar tahlil qilinadi
      api
        .rescanRules()
        .then((res) => {
          if (res && typeof res.rescanned_incidents === "number" && res.rescanned_incidents > 0) {
            setBanner({
              type: "success",
              message: `«${finalKeyword}» bo'yicha ${res.rescanned_incidents} ta mos hodisa avtomatik aniqlanib, tizimga kiritildi!`,
            });
          }
        })
        .catch(() => {});
    } catch (err: any) {
      setFormError(err.message || "Kalit so'zni saqlashda xatolik yuz berdi.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteRule = async (rule: DetectionRule) => {
    if (!confirm(`«${rule.keyword}» kalit so'zini o'chirishni xohlaysizmi?`)) return;
    try {
      await api.deleteRule(rule.id);
      await fetchRules();
    } catch (err: any) {
      alert(err.message || "Kalit so'zni o'chirishda xatolik yuz berdi.");
    }
  };

  const handleToggleActive = async (rule: DetectionRule) => {
    try {
      await api.updateRule(rule.id, {
        is_active: !rule.is_active,
      });
      await fetchRules();
      if (!rule.is_active) {
        api.rescanRules().catch(() => {});
      }
    } catch (err: any) {
      alert(err.message || "Holatni o'zgartirishda xatolik yuz berdi.");
    }
  };

  const totalPages = data ? Math.max(1, Math.ceil(data.total / 50)) : 1;

  return (
    <AppShell
      title="Kalit So'zlar Monitoringi"
      subtitle="Kiritilgan kalit so'zlar bo'yicha Telegram kanallar va guruhlar doimiy avtomatik tahlil qilinadi"
      onRefresh={fetchRules}
      isRefreshing={loading}
    >
      <div className="space-y-6">
        {/* Avtomatik tahlil bildirishnomasi */}
        {banner && (
          <div
            className={`rounded-2xl p-4 text-sm flex items-start justify-between gap-3 shadow-xs transition-all duration-300 animate-in fade-in slide-in-from-top-2 ${
              banner.type === "success"
                ? "bg-emerald-50/90 border border-emerald-200 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-200"
                : "bg-rose-50/90 border border-rose-200 text-rose-900 dark:bg-rose-950/40 dark:border-rose-900 dark:text-rose-200"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
              <span className="font-semibold">{banner.message}</span>
            </div>
            <button
              onClick={() => setBanner(null)}
              className="text-xs font-semibold opacity-70 hover:opacity-100 transition-opacity"
            >
              Yopish
            </button>
          </div>
        )}

        {/* Yuqori qidiruv va Amallar paneli */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white dark:bg-slate-900/60 p-3.5 rounded-2xl border border-slate-200/80 dark:border-slate-800 shadow-xs">
          {/* Chap tomon: Qidiruv */}
          <div className="relative w-full sm:w-80">
            <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Kalit so'zni qidirish..."
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2 pl-9 pr-3 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-100"
            />
          </div>

          {/* O'ng tomon: Avtomatik rejim belgisi + Yangi kalit so'z qo'shish */}
          <div className="flex flex-wrap items-center gap-2.5">
            <div className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900 text-emerald-800 dark:text-emerald-300 text-xs font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <span>Avtomatik doimiy monitoring faol (53 ta kanal va guruh)</span>
            </div>

            <Button
              onClick={openAddModal}
              className="gap-2 rounded-xl text-xs font-bold shadow-xs hover:scale-105 active:scale-95 transition-all"
            >
              <Plus className="h-4 w-4" />
              <span>Kalit so&apos;z kiritish</span>
            </Button>
          </div>
        </div>

        {/* Kalit So'zlar Jadvali */}
        <Card className="overflow-hidden p-0 rounded-2xl border border-slate-200/90 dark:border-slate-800 shadow-xs">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500 dark:bg-slate-800/60 dark:text-slate-400">
                <tr>
                  <th className="py-3.5 px-4 w-12 text-center">#</th>
                  <th className="py-3.5 px-4">Kalit so&apos;z yoki ibora</th>
                  <th className="py-3.5 px-4 w-36">Holati</th>
                  <th className="py-3.5 px-4 w-48">Oxirgi yangilanish</th>
                  <th className="py-3.5 px-4 w-48 text-right">Amallar</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {loading ? (
                  <tr>
                    <td colSpan={5} className="py-12 text-center text-slate-400">
                      Yuklanmoqda...
                    </td>
                  </tr>
                ) : !data || data.items.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-14 text-center text-slate-400 space-y-3">
                      <div className="h-12 w-12 mx-auto rounded-2xl bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 flex items-center justify-center border border-amber-200 dark:border-amber-900">
                        <Sparkles className="h-6 w-6" />
                      </div>
                      <p className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                        Hozircha hech qanday kalit so&apos;z kiritilmagan.
                      </p>
                      <p className="text-xs text-slate-400 max-w-sm mx-auto">
                        Telegram kanallardagi xabarlarni avtomatik topish va bosh sahifada ko&apos;rish uchun kalit so&apos;z kiriting.
                      </p>
                    </td>
                  </tr>
                ) : (
                  data.items.map((rule, idx) => (
                    <tr
                      key={rule.id}
                      className={`transition-colors hover:bg-slate-50/80 dark:hover:bg-slate-800/40 ${
                        !rule.is_active ? "opacity-60 bg-slate-50/40 dark:bg-slate-900/40" : ""
                      }`}
                    >
                      <td className="py-3.5 px-4 text-xs font-mono text-slate-400 text-center">
                        {(page - 1) * 50 + idx + 1}
                      </td>
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl font-bold text-sm bg-amber-50 text-amber-950 border border-amber-200 dark:bg-amber-950/50 dark:text-amber-200 dark:border-amber-800 shadow-2xs">
                            <KeyRound className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400" />
                            {rule.keyword}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-4">
                        <button
                          onClick={() => handleToggleActive(rule)}
                          title={rule.is_active ? "O'chirib qo'yish" : "Faollashtirish"}
                          className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border transition-all ${
                            rule.is_active
                              ? "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900"
                              : "bg-slate-100 text-slate-600 border-slate-200 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-400 dark:border-slate-700"
                          }`}
                        >
                          {rule.is_active ? (
                            <>
                              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                              <span>Faol</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-3.5 w-3.5" />
                              <span>Nofaol</span>
                            </>
                          )}
                        </button>
                      </td>
                      <td className="py-3.5 px-4 text-xs text-slate-500 dark:text-slate-400">
                        {formatDateTime(rule.updated_at || rule.created_at)}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => openEditModal(rule)}
                            title="Tahrirlash"
                          >
                            <Edit2 className="h-3.5 w-3.5 mr-1" /> Tahrirlash
                          </Button>

                          <Button
                            size="sm"
                            variant="outline"
                            className="text-rose-600 hover:bg-rose-50 hover:text-rose-700 border-rose-200 dark:border-rose-900/50 dark:text-rose-400 dark:hover:bg-rose-950/40 p-2"
                            onClick={() => handleDeleteRule(rule)}
                            title="Kalit so'zni o'chirish"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Sahifalash */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-xs text-slate-500 dark:border-slate-800">
              <div>
                Jami: <span className="font-semibold">{data?.total || 0}</span> ta kalit so&apos;z
              </div>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="h-8 px-2.5"
                >
                  <ChevronLeft className="h-3.5 w-3.5 mr-1" /> Oldingi
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
            </div>
          )}
        </Card>
      </div>

      {/* Faqat Kalit So'z Kiritish Modali */}
      <Modal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        title={editingRule ? "Kalit so'zni tahrirlash" : "Yangi kalit so'z kiritish"}
      >
        <form onSubmit={handleSaveRule} className="space-y-4">
          {formError && <Alert type="error">{formError}</Alert>}

          {/* Kalit so'z yoki ibora */}
          <div>
            <label className="mb-1.5 block text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Kalit so&apos;z yoki ibora <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              placeholder="Masalan: quvur, suv toshdi, уриб юборди..."
              value={formKeyword}
              onChange={(e) => setFormKeyword(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 font-medium"
              required
              autoFocus
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
            <Button type="submit" size="md" loading={submitting}>
              {editingRule ? "O'zgarishlarni saqlash" : "Kalit so'zni saqlash"}
            </Button>
          </div>
        </form>
      </Modal>
    </AppShell>
  );
}
