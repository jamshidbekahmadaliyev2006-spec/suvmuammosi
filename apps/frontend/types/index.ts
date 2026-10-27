export type IncidentStatus =
  | "OPEN"
  | "IN_PROGRESS"
  | "RESOLVED"
  | "ARCHIVED"
  | "INVALID"
  | "DUPLICATE";

export type IncidentCategory =
  | "PIPE_BURST"
  | "SUPPLY_OUTAGE"
  | "LOW_PRESSURE"
  | "LEAK"
  | "FLOODING"
  | "PLANNED_REPAIR"
  | "SEWAGE"
  | "OTHER"
  | "UNCLEAR";

export type Priority = "LOW" | "MEDIUM" | "HIGH";

export type MatchType = "CONTAINS" | "WHOLE_WORD" | "PHRASE";

export type ProcessingStatus =
  | "RECEIVED"
  | "NO_MATCH"
  | "INCIDENT_CREATED"
  | "LINKED"
  | "REVIEW_REQUIRED";

export type SourceType = "CHANNEL" | "GROUP" | "BOT";

export interface User {
  id: number;
  username: string;
  email?: string | null;
  role: "USER";
  is_active: boolean;
  last_login_at?: string | null;
}

export interface SessionData {
  user: User;
  csrf_token: string;
}

export interface MessageOut {
  id: number;
  source_id: number;
  source_name: string;
  telegram_message_id: number;
  message_text: string;
  message_url?: string | null;
  telegram_timestamp: string;
  received_at: string;
  processing_status: ProcessingStatus;
  matched_rule_ids: number[];
}

export interface IncidentListItem {
  id: number;
  title: string;
  description?: string | null;
  category: IncidentCategory;
  status: IncidentStatus;
  priority: Priority;
  source_id: number;
  source_name: string;
  source_type?: string | null;
  source_username?: string | null;
  message_url?: string | null;
  district?: string | null;
  address?: string | null;
  first_seen_at: string;
  last_seen_at: string;
  media_type?: string | null;
  file_id?: string | null;
  media_url?: string | null;
  location_url?: string | null;
  matched_rule_ids?: number[];
  report_type?: "MUROJAAT" | "YANGILIK" | "RASMIY_ELON" | string | null;
  ai_summary?: string | null;
  resolution_notes?: string | null;
  resolved_at?: string | null;
}

export interface CommentItem {
  id: number;
  user_id: number;
  username: string;
  comment: string;
  created_at: string;
}

export interface HistoryItem {
  id: number;
  old_status?: IncidentStatus | null;
  new_status: IncidentStatus;
  changed_by_user_id?: number | null;
  changed_by_username?: string | null;
  comment?: string | null;
  created_at: string;
}

export interface IncidentDetail extends IncidentListItem {
  description: string;
  resolution_notes?: string | null;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
  first_message?: MessageOut | null;
  comments: CommentItem[];
}

export interface DetectionRule {
  id: number;
  name: string;
  keyword: string;
  category: IncidentCategory;
  match_type: MatchType;
  priority: number;
  is_active: boolean;
  description?: string | null;
  created_at: string;
  updated_at: string;
  created_by_username?: string | null;
  updated_by_username?: string | null;
}

export interface MonitoringSource {
  id: number;
  name: string;
  telegram_chat_id: number;
  telegram_username?: string | null;
  source_type: SourceType;
  is_active: boolean;
  last_message_at?: string | null;
  last_received_at?: string | null;
  created_at: string;
}

export interface BotStatus {
  status: "ONLINE" | "DEGRADED" | "OFFLINE" | "UNKNOWN";
  last_heartbeat_at?: string | null;
  rules_version?: number | null;
  rules_loaded?: boolean | null;
  detail: string;
}

export interface StatsCards {
  total_incidents: number;
  open_incidents: number;
  in_progress_incidents: number;
  resolved_incidents: number;
  messages_today: number;
  unreviewed_incidents: number;
  review_required_messages: number;
  channels_and_groups_count?: number;
  news_count?: number;
  total_zayavkas?: number;
}

export interface SourceActivity {
  source_id: number;
  name: string;
  is_active: boolean;
  messages_24h: number;
  last_message_at?: string | null;
}

export interface DashboardStats {
  cards: StatsCards;
  by_status: Record<IncidentStatus, number>;
  by_category: Record<IncidentCategory, number>;
  sources: SourceActivity[];
  bot: BotStatus;
  last_sync_at?: string | null;
  day_start_utc: string;
  day_end_utc: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
