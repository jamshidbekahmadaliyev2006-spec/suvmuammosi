"use client";

import React, { useState } from "react";
import { Droplets, Lock, User as UserIcon, AlertCircle, Eye, EyeOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Alert } from "@/components/ui/alert";
import { useAuth } from "@/context/auth-context";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryAfter, setRetryAfter] = useState<number | null>(null);

  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!identifier.trim() || !password) {
      setError("Iltimos, login va parolni kiriting.");
      return;
    }

    setLoading(true);
    setError(null);
    setRetryAfter(null);

    try {
      await login(identifier.trim(), password);
    } catch (err: any) {
      if (err instanceof ApiError) {
        if (err.status === 429 && err.details?.retry_after_seconds) {
          setRetryAfter(err.details.retry_after_seconds);
          setError(
            `Ko'p urinish amalga oshirildi. Iltimos, ${err.details.retry_after_seconds} soniyadan so'ng qayta urinib ko'ring.`
          );
        } else {
          setError(err.message || "Login yoki parol noto'g'ri.");
        }
      } else {
        setError("Tizimga ulanishda xatolik yuz berdi. Backend ishlayotganini tekshiring.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="relative flex min-h-screen items-center justify-center p-4 bg-cover bg-center bg-no-repeat"
      style={{
        backgroundImage: "url('/images/hokimiyat_bg.png')",
      }}
    >
      {/* Toshkent Hokimiyati fonidagi tumanli qoramtir pardoz qatlami */}
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/95 via-slate-900/75 to-slate-950/80 backdrop-blur-[2px]" />

      {/* Markaziy Frosted Glassmorphism Kartochkasi */}
      <div className="relative z-10 w-full max-w-md rounded-3xl border border-white/30 bg-white/95 p-8 sm:p-10 shadow-2xl backdrop-blur-xl dark:border-white/10 dark:bg-slate-900/95 transition-all">
        {/* Yuqori Hokimiyat yorlig'i */}
        <div className="mb-6 flex items-center justify-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50/90 px-3.5 py-1 text-[11px] font-bold text-sky-800 dark:border-sky-800/60 dark:bg-sky-950/60 dark:text-sky-300 shadow-xs">
            <span className="h-2 w-2 rounded-full bg-sky-500 animate-pulse" />
            <span>Toshkent Shahar Hokimiyati</span>
          </div>
        </div>

        {/* Brand Logotipi va Sarlavha */}
        <div className="mb-7 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-brand-600 to-sky-400 text-white shadow-lg shadow-brand-500/30">
            <Droplets className="h-7 w-7" />
          </div>
          <h1 className="text-2xl font-black tracking-tight text-slate-900 dark:text-white">
            Suv<span className="text-brand-600 dark:text-brand-400">Nazorati</span>
          </h1>
        </div>

        {error && (
          <Alert type="error" className="mb-5 rounded-xl border-rose-200 bg-rose-50 text-xs dark:bg-rose-950/50">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-rose-500 flex-shrink-0" />
              <span>{error}</span>
            </div>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <UserIcon className="h-3.5 w-3.5 text-slate-400" />
              Login yoki Elektron pochta
            </label>
            <Input
              type="text"
              placeholder="Masalan: admin yoki admin@suvnazorat.uz"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              disabled={loading || Boolean(retryAfter)}
              className="rounded-xl h-11 text-sm bg-white/80 dark:bg-slate-800/80 focus:bg-white"
              autoFocus
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5 flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5 text-slate-400" />
              Xavfsizlik Paroli
            </label>
            <div className="relative">
              <Input
                type={showPassword ? "text" : "password"}
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading || Boolean(retryAfter)}
                className="rounded-xl h-11 text-sm bg-white/80 dark:bg-slate-800/80 focus:bg-white pr-11"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword((prev) => !prev)}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors focus:outline-hidden"
                tabIndex={-1}
                title={showPassword ? "Parolni yashirish" : "Parolni ko'rsatish"}
                aria-label={showPassword ? "Parolni yashirish" : "Parolni ko'rsatish"}
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full mt-3 h-11 rounded-xl text-sm font-bold shadow-md shadow-brand-500/20 bg-brand-600 hover:bg-brand-700 text-white transition-all"
            loading={loading}
            disabled={Boolean(retryAfter)}
          >
            {loading ? "Tekshirilmoqda..." : "Tizimga kirish"}
          </Button>
        </form>
      </div>
    </div>
  );
}
