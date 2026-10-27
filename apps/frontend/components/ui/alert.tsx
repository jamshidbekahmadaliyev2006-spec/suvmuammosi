import React from "react";
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface AlertProps {
  type?: "info" | "success" | "warning" | "error";
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export function Alert({
  type = "info",
  title,
  children,
  className,
}: AlertProps) {
  const styles = {
    info: "bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-950/40 dark:border-blue-900 dark:text-blue-200",
    success:
      "bg-emerald-50 border-emerald-200 text-emerald-900 dark:bg-emerald-950/40 dark:border-emerald-900 dark:text-emerald-200",
    warning:
      "bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-950/40 dark:border-amber-900 dark:text-amber-200",
    error:
      "bg-rose-50 border-rose-200 text-rose-900 dark:bg-rose-950/40 dark:border-rose-900 dark:text-rose-200",
  };

  const icons = {
    info: <Info className="h-5 w-5 text-blue-600 dark:text-blue-400" />,
    success: (
      <CheckCircle2 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
    ),
    warning: (
      <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />
    ),
    error: (
      <AlertCircle className="h-5 w-5 text-rose-600 dark:text-rose-400" />
    ),
  };

  return (
    <div
      className={cn(
        "flex gap-3 rounded-xl border p-4 text-sm",
        styles[type],
        className
      )}
    >
      <div className="shrink-0">{icons[type]}</div>
      <div className="flex-1">
        {title && <h4 className="font-semibold mb-0.5">{title}</h4>}
        <div>{children}</div>
      </div>
    </div>
  );
}
