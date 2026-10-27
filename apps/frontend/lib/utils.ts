import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { IncidentCategory, IncidentStatus, Priority, ProcessingStatus, SourceType } from "@/types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(isoString?: string | null): string {
  if (!isoString) return "-";
  try {
    const d = new Date(isoString);
    return new Intl.DateTimeFormat("uz-UZ", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    }).format(d);
  } catch {
    return isoString;
  }
}

export function statusLabel(status: IncidentStatus): string {
  if (status === "RESOLVED") {
    return "Hal qilingan";
  }
  return "Hal qilinmagan";
}

export function statusBadgeClass(status: IncidentStatus): string {
  if (status === "RESOLVED") {
    return "bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800";
  }
  return "bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300 border border-rose-200 dark:border-rose-800";
}

export function categoryLabel(category: IncidentCategory): string {
  const map: Record<IncidentCategory, string> = {
    PIPE_BURST: "Quvur yorilishi",
    SUPPLY_OUTAGE: "Suv ta'minoti uzilishi",
    LOW_PRESSURE: "Suv bosimi pasayishi",
    LEAK: "Suv sizib chiqishi",
    FLOODING: "Suv bosishi",
    PLANNED_REPAIR: "Rejali ta'mirlash",
    SEWAGE: "Kanalizatsiya avariyasi",
    OTHER: "Boshqa muammo",
    UNCLEAR: "Aniqlashtirilishi kerak",
  };
  return map[category] || category;
}

export function priorityLabel(priority: Priority): string {
  switch (priority) {
    case "HIGH":
      return "Yuqori";
    case "MEDIUM":
      return "O'rta";
    case "LOW":
      return "Past";
    default:
      return priority;
  }
}

export function priorityBadgeClass(priority: Priority): string {
  switch (priority) {
    case "HIGH":
      return "text-red-700 bg-red-50 border-red-200 dark:bg-red-950/50 dark:text-red-300 dark:border-red-900";
    case "MEDIUM":
      return "text-amber-700 bg-amber-50 border-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:border-amber-900";
    case "LOW":
      return "text-blue-700 bg-blue-50 border-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:border-blue-900";
  }
}

export function processingStatusLabel(status: ProcessingStatus): string {
  switch (status) {
    case "INCIDENT_CREATED":
      return "Hodisa yaratildi";
    case "LINKED":
      return "Bog'landi";
    case "REVIEW_REQUIRED":
      return "Tekshiruv zarur";
    case "NO_MATCH":
      return "Moslik yo'q";
    case "RECEIVED":
      return "Qabul qilindi";
    default:
      return status;
  }
}

export function sourceTypeLabel(type: SourceType | string): string {
  if (type === "BOT") return "Telegram Bot";
  if (type === "CHANNEL") return "Kanal";
  return "Guruh";
}

