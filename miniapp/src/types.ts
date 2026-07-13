export interface Me {
  telegram_id: number;
  first_name: string;
  username?: string;
  is_admin: boolean;
  gift_balance_gb: number;
  wallet_balance_toman: number;
  reward_credit_toman: number;
  phone_verified: boolean;
  onboarding_seen: boolean;
}

export interface ServiceSummary {
  id: string;
  label: string;
  status: string;
  traffic_limit_gb: number;
  traffic_used_gb: number;
  expires_at: string | null;
  created_at: string;
}

export interface ServiceDetail extends ServiceSummary {
  subscription_url: string | null;
  links: string[];
}

export interface NetworkPerson {
  name: string | null;
  username: string | null;
  verified: boolean;
}

export interface LevelMeta {
  reward_percent: number;
  monthly_cap_gb: number;
  earned_this_month_gb: number;
}

export interface NetworkData {
  level1: NetworkPerson[];
  level2: NetworkPerson[];
  level3: NetworkPerson[];
  levels_meta: Record<string, LevelMeta>;
}

export interface Stats {
  accounts: { total: number; active: number; inactive: number };
  volume: { total_allocated_gb: number; total_used_gb: number };
  sales: { total_sales: number; today_sales: number; week_sales: number; month_sales: number };
  trend: { day: string; total: number; count: number }[];
}

export interface Receipt {
  id: string;
  telegram_id: number;
  telegram_username: string | null;
  full_name: string | null;
  package_name: string | null;
  price_toman: number;
  payment_status: string;
  service_label: string | null;
  purchased_at: string;
  receipt_file_id: string | null;
}

export interface Package {
  id: number;
  name: string;
  volume_gb: number;
  retail_price_toman: number;
  is_key_panel: boolean;
  is_active: boolean;
  badge: string | null;
}

export interface AdminEntry {
  telegram_id: number;
  added_by: number | null;
  is_active: boolean;
  added_at: string;
}

export interface AgencyTierConfig {
  tier: "silver" | "gold" | "diamond";
  activation_fee_toman: number;
  purchase_rate_toman_per_gb: number;
  min_wallet_balance_toman: number;
  updated_at: string;
}

export interface WalletTopup {
  id: string;
  amount_toman: number;
  status: "pending" | "confirmed" | "rejected";
  created_at: string;
  confirmed_at: string | null;
  telegram_id?: number;
  telegram_username?: string | null;
  full_name?: string | null;
}

export interface PurchaseCreateResponse {
  id: string;
  status: "auto_approved" | "awaiting_receipt";
  final_price: number;
  discount_amount?: number;
  wallet_used?: number;
  card_number?: string;
  card_holder?: string;
  payment_notice?: string;
  reward_credit_used?: number;
}

export interface AgencyDownlineEntry {
  agent_id: string;
  tier: "silver" | "gold" | "diamond";
  level: number;
}

export interface AgencyStatus {
  is_agent: boolean;
  tier?: "silver" | "gold" | "diamond";
  is_panel_active?: boolean;
  purchase_rate_toman_per_gb?: number;
  min_wallet_balance_toman?: number;
  wallet_balance_toman?: number;
  activated_at?: string;
  downline_count?: number;
  downline?: AgencyDownlineEntry[];
  agent_slug?: string | null;
  custom_pricing_enabled?: boolean;
}

export interface AgentPlanPrice {
  package_id: number;
  name: string;
  volume_gb: number;
  default_price_toman: number;
  agent_price_toman: number | null;
}

export interface AgencyCustomer {
  id: string;
  telegram_id: number;
  telegram_username: string | null;
  full_name: string | null;
  volume_gb: number;
  price_toman: number;
  is_gift_resale: boolean;
  service_label: string | null;
  purchased_at: string;
}

export interface AgencyActivationResponse {
  id: string;
  tier: string;
  activation_fee_toman: number;
  is_upgrade: boolean;
  card_number?: string;
  card_holder?: string;
  payment_notice?: string;
}

export interface PaymentCard {
  id: number;
  card_number: string;
  card_holder: string;
  is_active: boolean;
  created_at: string;
}

export interface Expense {
  id: string;
  amount_toman: number;
  description: string;
  category: string | null;
  created_at: string;
}

export interface SalesStatsDetailed {
  total_count: number;
  total_sales: number;
  today_count: number;
  today_sales: number;
  week_count: number;
  week_sales: number;
  month_count: number;
  month_sales: number;
}

export interface AccountingSummary {
  total_sales: number;
  agency_activation_total: number;
  wallet_topup_total: number;
  total_revenue: number;
  total_expenses: number;
  net_profit: number;
}

export interface RevenueBreakdown {
  total: number;
  today: number;
  week: number;
  month: number;
}

export interface OtherRevenue {
  agency_activation: RevenueBreakdown;
  wallet_topup: RevenueBreakdown;
}

export interface WalletCostStats {
  total_cost: number;
  today_cost: number;
  week_cost: number;
  month_cost: number;
}

export interface AgentAccounting {
  sales: SalesStatsDetailed;
  cost: WalletCostStats;
  expenses: Expense[];
  expense_total: number;
  net_profit: number;
}

export interface ActivityLogEntry {
  id: string;
  admin_telegram_id: number;
  action_type: string;
  target_description: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}
