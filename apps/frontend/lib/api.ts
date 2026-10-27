import {
  CommentItem,
  DashboardStats,
  DetectionRule,
  HistoryItem,
  IncidentCategory,
  IncidentDetail,
  IncidentListItem,
  IncidentStatus,
  MessageOut,
  MonitoringSource,
  Page,
  Priority,
  SessionData,
  SourceType,
  User,
} from "@/types";

const BACKEND_URL =
  typeof window !== "undefined"
    ? ""
    : process.env.NEXT_PUBLIC_BACKEND_URL || "http://127.0.0.1:8000";

let cachedCsrfToken: string | null = null;

export function setCsrfToken(token: string | null) {
  cachedCsrfToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem("sn_csrf_token", token);
    } else {
      localStorage.removeItem("sn_csrf_token");
    }
  }
}

export function getCsrfToken(): string | null {
  if (cachedCsrfToken) return cachedCsrfToken;
  if (typeof window !== "undefined") {
    cachedCsrfToken = localStorage.getItem("sn_csrf_token");
  }
  return cachedCsrfToken;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: any;

  constructor(status: number, code: string, message: string, details?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  const method = (options.method || "GET").toUpperCase();
  if (
    !headers.has("Content-Type") &&
    !(options.body instanceof FormData) &&
    method !== "GET" &&
    method !== "DELETE" &&
    options.body !== undefined
  ) {
    headers.set("Content-Type", "application/json");
  }

  if (["POST", "PATCH", "PUT", "DELETE"].includes(method)) {
    const csrf = getCsrfToken();
    if (csrf) {
      headers.set("x-csrf-token", csrf);
    }
  }

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // Session cookie'ni yuborish
  });

  if (!res.ok) {
    let errCode = "unknown_error";
    let errMsg = "Kutilmagan xatolik yuz berdi.";
    let errDetails: any = null;

    try {
      const errJson = await res.json();
      if (errJson.error) {
        errCode = errJson.error.code || errCode;
        errMsg = errJson.error.message || errMsg;
        errDetails = errJson.error.details;
      } else if (errJson.detail) {
        errMsg = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      errMsg = `Server xatoligi: ${res.statusText} (${res.status})`;
    }

    throw new ApiError(res.status, errCode, errMsg, errDetails);
  }

  // 204 No Content
  if (res.status === 204) {
    return {} as T;
  }

  return res.json();
}

export const api = {
  // --- Autentifikatsiya ---
  async login(identifier: string, password: string): Promise<SessionData> {
    const data = await request<SessionData>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ identifier, password }),
    });
    setCsrfToken(data.csrf_token);
    return data;
  },

  async logout(): Promise<void> {
    try {
      await request("/api/v1/auth/logout", { method: "POST" });
    } finally {
      setCsrfToken(null);
    }
  },

  async getMe(): Promise<SessionData> {
    const data = await request<SessionData>("/api/v1/auth/me");
    setCsrfToken(data.csrf_token);
    return data;
  },

  async updateProfile(data: {
    username?: string;
    email?: string;
    current_password?: string;
    new_password?: string;
  }): Promise<User> {
    return request<User>("/api/v1/auth/profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  // --- Dashboard ---
  async getDashboardStats(): Promise<DashboardStats> {
    return request<DashboardStats>("/api/v1/dashboard/stats");
  },

  async getRecentIncidents(limit = 50, reportType?: string): Promise<IncidentListItem[]> {
    const q = new URLSearchParams();
    q.set("limit", String(limit));
    if (reportType) q.set("report_type", reportType);
    return request<IncidentListItem[]>(`/api/v1/dashboard/recent-incidents?${q.toString()}`);
  },

  async getRecentMessages(limit = 10): Promise<MessageOut[]> {
    return request<MessageOut[]>(`/api/v1/dashboard/recent-messages?limit=${limit}`);
  },

  // --- Hodisalar ---
  async listIncidents(params: {
    q?: string;
    status?: IncidentStatus;
    category?: IncidentCategory;
    report_type?: string;
    source_id?: number;
    date_from?: string;
    date_to?: string;
    sort_by?: string;
    order?: "asc" | "desc";
    page?: number;
    page_size?: number;
  }): Promise<Page<IncidentListItem>> {
    const q = new URLSearchParams();
    if (params.q) q.set("q", params.q);
    if (params.status) q.set("status", params.status);
    if (params.category) q.set("category", params.category);
    if (params.report_type) q.set("report_type", params.report_type);
    if (params.source_id) q.set("source_id", String(params.source_id));
    if (params.date_from) q.set("date_from", params.date_from);
    if (params.date_to) q.set("date_to", params.date_to);
    if (params.sort_by) q.set("sort_by", params.sort_by);
    if (params.order) q.set("order", params.order);
    if (params.page) q.set("page", String(params.page));
    if (params.page_size) q.set("page_size", String(params.page_size));

    return request<Page<IncidentListItem>>(`/api/v1/incidents?${q.toString()}`);
  },

  async getIncident(id: number): Promise<IncidentDetail> {
    return request<IncidentDetail>(`/api/v1/incidents/${id}`);
  },

  async updateIncident(
    id: number,
    data: {
      status?: IncidentStatus;
      priority?: Priority;
      category?: IncidentCategory;
      resolution_notes?: string;
      district?: string;
      address?: string;
      comment?: string;
    }
  ): Promise<IncidentDetail> {
    return request<IncidentDetail>(`/api/v1/incidents/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async getIncidentHistory(id: number): Promise<HistoryItem[]> {
    return request<HistoryItem[]>(`/api/v1/incidents/${id}/history`);
  },

  async getIncidentMessages(id: number): Promise<MessageOut[]> {
    return request<MessageOut[]>(`/api/v1/incidents/${id}/messages`);
  },

  async addComment(id: number, comment: string): Promise<CommentItem> {
    return request<CommentItem>(`/api/v1/incidents/${id}/comments`, {
      method: "POST",
      body: JSON.stringify({ comment }),
    });
  },

  // --- Kalit so'zlar / Aniqlash qoidalari ---
  async listRules(params: {
    q?: string;
    category?: IncidentCategory;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<Page<DetectionRule>> {
    const q = new URLSearchParams();
    if (params.q) q.set("q", params.q);
    if (params.category) q.set("category", params.category);
    if (params.is_active !== undefined) q.set("is_active", String(params.is_active));
    if (params.page) q.set("page", String(params.page));
    if (params.page_size) q.set("page_size", String(params.page_size));

    return request<Page<DetectionRule>>(`/api/v1/detection-rules?${q.toString()}`);
  },

  async createRule(data: {
    name: string;
    keyword: string;
    category: IncidentCategory;
    match_type: string;
    priority: number;
    description?: string;
    is_active?: boolean;
  }): Promise<DetectionRule> {
    return request<DetectionRule>("/api/v1/detection-rules", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateRule(
    id: number,
    data: {
      name?: string;
      keyword?: string;
      category?: IncidentCategory;
      match_type?: string;
      priority?: number;
      description?: string;
      is_active?: boolean;
    }
  ): Promise<DetectionRule> {
    return request<DetectionRule>(`/api/v1/detection-rules/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteRule(id: number): Promise<void> {
    return request<void>(`/api/v1/detection-rules/${id}`, {
      method: "DELETE",
    });
  },

  async rescanRules(): Promise<{ status: string; rescanned_incidents: number }> {
    return request<{ status: string; rescanned_incidents: number }>("/api/v1/detection-rules/rescan", {
      method: "POST",
    });
  },


  // --- Monitoring manbalari ---
  async listSources(params: {
    q?: string;
    is_active?: boolean;
    page?: number;
    page_size?: number;
  }): Promise<Page<MonitoringSource>> {
    const q = new URLSearchParams();
    if (params.q) q.set("q", params.q);
    if (params.is_active !== undefined) q.set("is_active", String(params.is_active));
    if (params.page) q.set("page", String(params.page));
    if (params.page_size) q.set("page_size", String(params.page_size));

    return request<Page<MonitoringSource>>(`/api/v1/sources?${q.toString()}`);
  },

  async resolveSource(identifier: string): Promise<{
    telegram_chat_id: number;
    name: string;
    telegram_username: string;
    source_type: SourceType;
    resolved: boolean;
  }> {
    return request<{
      telegram_chat_id: number;
      name: string;
      telegram_username: string;
      source_type: SourceType;
      resolved: boolean;
    }>("/api/v1/sources/resolve", {
      method: "POST",
      body: JSON.stringify({ identifier }),
    });
  },

  async createSource(data: {
    name?: string;
    telegram_chat_id?: number;
    telegram_username?: string;
    source_type?: SourceType;
    is_active?: boolean;
  }): Promise<MonitoringSource> {
    return request<MonitoringSource>("/api/v1/sources", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async updateSource(
    id: number,
    data: {
      name?: string;
      telegram_chat_id?: number;
      telegram_username?: string;
      source_type?: SourceType;
      is_active?: boolean;
    }
  ): Promise<MonitoringSource> {
    return request<MonitoringSource>(`/api/v1/sources/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async deleteSource(id: number): Promise<void> {
    return request<void>(`/api/v1/sources/${id}`, {
      method: "DELETE",
    });
  },

  async syncSourcesHistory(daysBack: number = 10): Promise<{
    status: string;
    synced_sources: number;
    total_messages_synced: number;
    rescanned_incidents: number;
  }> {
    return request<{
      status: string;
      synced_sources: number;
      total_messages_synced: number;
      rescanned_incidents: number;
    }>("/api/v1/sources/sync-history", {
      method: "POST",
      body: JSON.stringify({ days_back: daysBack }),
    });
  },

  async syncSingleSource(
    sourceId: number,
    daysBack: number = 10
  ): Promise<{
    status: string;
    source_id: number;
    messages_synced: number;
    rescanned_incidents: number;
  }> {
    return request<{
      status: string;
      source_id: number;
      messages_synced: number;
      rescanned_incidents: number;
    }>(`/api/v1/sources/${sourceId}/sync?days_back=${daysBack}`, {
      method: "POST",
    });
  },

  // --- Tizim ---
  async checkHealth(): Promise<{ status: string; database: string }> {
    return request<{ status: string; database: string }>("/api/v1/system/health");
  },

  async getAdminPhones(): Promise<{ phones: string[] }> {
    return request<{ phones: string[] }>("/api/v1/system/admin-phones");
  },

  async setAdminPhones(phones: string[]): Promise<{ ok: boolean; phones: string[] }> {
    return request<{ ok: boolean; phones: string[] }>("/api/v1/system/admin-phones", {
      method: "POST",
      body: JSON.stringify({ phones }),
    });
  },
};
