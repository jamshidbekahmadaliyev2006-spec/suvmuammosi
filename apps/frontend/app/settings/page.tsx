"use client";

import React, { useEffect, useState } from "react";
import {
  User as UserIcon,
  KeyRound,
  CheckCircle2,
  AlertCircle,
  Save,
  Shield,
  Smartphone,
  Bot,
  Eye,
  EyeOff,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/alert";
import { useAuth } from "@/context/auth-context";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();

  const [username, setUsername] = useState(user?.username || "");
  const [email, setEmail] = useState(user?.email || "");

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Telegram bot admin telefon raqamlari sozlamasi
  const [adminPhones, setAdminPhones] = useState<string>("");
  const [savingPhones, setSavingPhones] = useState(false);
  const [phonesSuccessMsg, setPhonesSuccessMsg] = useState<string | null>(null);
  const [phonesErrorMsg, setPhonesErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    async function loadAdminPhones() {
      try {
        const res = await api.getAdminPhones();
        if (res && res.phones) {
          setAdminPhones(res.phones.join(", "));
        }
      } catch {}
    }
    loadAdminPhones();
  }, []);

  const handleSaveAdminPhones = async (e: React.FormEvent) => {
    e.preventDefault();
    setPhonesSuccessMsg(null);
    setPhonesErrorMsg(null);
    setSavingPhones(true);
    try {
      const list = adminPhones
        .split(",")
        .map((p) => p.trim())
        .filter(Boolean);
      await api.setAdminPhones(list);
      setPhonesSuccessMsg("Telegram bot administrator telefon raqamlari saqlandi!");
    } catch (err: any) {
      setPhonesErrorMsg(err.message || "Telefon raqamlarni saqlashda xatolik yuz berdi.");
    } finally {
      setSavingPhones(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccessMsg(null);
    setErrorMsg(null);

    if (newPassword) {
      if (newPassword.length < 8) {
        setErrorMsg("Yangi parol kamida 8 ta belgidan iborat bo'lishi kerak.");
        return;
      }
      if (newPassword !== confirmPassword) {
        setErrorMsg("Yangi parol va tasdiqlash paroli mos kelmadi.");
        return;
      }
      if (!currentPassword) {
        setErrorMsg("Parolni yangilash uchun joriy parolingizni kiriting.");
        return;
      }
    }

    setSaving(true);
    try {
      await api.updateProfile({
        username: username.trim() || undefined,
        email: email.trim() || undefined,
        current_password: currentPassword || undefined,
        new_password: newPassword || undefined,
      });

      setSuccessMsg("Ma'lumotlar muvaffaqiyatli yangilandi!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");

      if (refreshUser) {
        await refreshUser();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Profilni yangilashda xatolik yuz berdi.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell
      title="Profil va Xavfsizlik Sozlamalari"
      subtitle="Foydalanuvchi nomi, elektron pochta va tizimga kirish parolini boshqarish"
    >
      <div className="space-y-6 max-w-2xl">
        {successMsg && (
          <Alert type="success">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>{successMsg}</span>
            </div>
          </Alert>
        )}

        {errorMsg && (
          <Alert type="error">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-500" />
              <span>{errorMsg}</span>
            </div>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 1. Asosiy Profil ma'lumotlari */}
          <Card className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <CardHeader className="p-0 mb-5">
              <CardTitle className="text-base font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <UserIcon className="h-5 w-5 text-brand-600 dark:text-brand-400" />
                Foydalanuvchi ma'lumotlarini tahrirlash
              </CardTitle>
            </CardHeader>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Foydalanuvchi nomi (Login):
                </label>
                <Input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  required
                  className="rounded-xl"
                />
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Tizimga kirish uchun foydalaniladigan login.
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Elektron pochta (Email):
                </label>
                <Input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@suvnazorat.uz"
                  className="rounded-xl"
                />
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                <span className="text-slate-500">Tizimdagi rol:</span>
                <Badge variant="default">{user?.role || "USER"}</Badge>
              </div>
            </div>
          </Card>

          {/* 2. Parolni o'zgartirish */}
          <Card className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
            <CardHeader className="p-0 mb-5">
              <CardTitle className="text-base font-bold flex items-center gap-2 text-slate-900 dark:text-white">
                <KeyRound className="h-5 w-5 text-amber-500" />
                Parolni o'zgartirish
              </CardTitle>
            </CardHeader>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                  Joriy parol:
                </label>
                <div className="relative">
                  <Input
                    type={showCurrent ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Joriy parolni kiriting"
                    className="rounded-xl pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowCurrent((prev) => !prev)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                    tabIndex={-1}
                  >
                    {showCurrent ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Yangi parol:
                  </label>
                  <div className="relative">
                    <Input
                      type={showNew ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Kamida 8 belgi"
                      className="rounded-xl pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNew((prev) => !prev)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      tabIndex={-1}
                    >
                      {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">
                    Yangi parolni tasdiqlash:
                  </label>
                  <div className="relative">
                    <Input
                      type={showConfirm ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Parolni qayta kiriting"
                      className="rounded-xl pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirm((prev) => !prev)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
                      tabIndex={-1}
                    >
                      {showConfirm ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              </div>

              <span className="text-[11px] text-slate-400 block">
                Agar parolni o'zgartirmoqchi bo'lmasangiz, bu maydonlarni bo'sh qoldiring.
              </span>
            </div>
          </Card>

          {/* Saqlash tugmasi */}
          <div className="flex justify-end">
            <Button type="submit" disabled={saving} className="rounded-xl px-6 py-2.5 gap-2 font-bold shadow-md">
              <Save className="h-4 w-4" />
              {saving ? "Saqlanmoqda..." : "Profilni saqlash"}
            </Button>
          </div>
        </form>

        {/* 3. Telegram Bot Admin Sozlamalari (Telefon raqam orqali avtorizatsiya) */}
        <Card className="rounded-2xl border border-slate-200/90 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-sm">
          <CardHeader className="p-0 mb-4">
            <CardTitle className="text-base font-bold flex items-center gap-2 text-slate-900 dark:text-white">
              <Bot className="h-5 w-5 text-sky-500" />
              <span>Telegram Bot Administratorlari</span>
            </CardTitle>
          </CardHeader>

          {phonesSuccessMsg && (
            <Alert type="success" className="mb-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                <span>{phonesSuccessMsg}</span>
              </div>
            </Alert>
          )}

          {phonesErrorMsg && (
            <Alert type="error" className="mb-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-rose-500" />
                <span>{phonesErrorMsg}</span>
              </div>
            </Alert>
          )}

          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
                <Smartphone className="h-4 w-4 text-slate-400" />
                Admin telefon raqamlari (vergul bilan ajrating):
              </label>
              <Input
                type="text"
                value={adminPhones}
                onChange={(e) => setAdminPhones(e.target.value)}
                placeholder="+998901234567, +998991234567"
                className="rounded-xl font-mono text-sm"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                type="button"
                onClick={handleSaveAdminPhones}
                disabled={savingPhones}
                variant="secondary"
                className="rounded-xl px-4 py-2 gap-2 text-xs font-semibold"
              >
                <Save className="h-3.5 w-3.5" />
                {savingPhones ? "Saqlanmoqda..." : "Admin raqamlarini saqlash"}
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </AppShell>
  );
}
