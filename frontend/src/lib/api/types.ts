export type UserRole = "owner" | "staff" | "customer" | "admin";
export type PlanName = "freemium" | "pro";
export type BookingStatus =
  | "pending"
  | "confirmed"
  | "cancelled"
  | "completed"
  | "no_show";
export type WaitlistStatus =
  | "waiting"
  | "offered"
  | "booked"
  | "expired"
  | "cancelled";
export type Weekday = 0 | 1 | 2 | 3 | 4 | 5 | 6;

/** Los importes llegan como string o número según cómo los serialice la API. */
export type Money = string | number;

export interface User {
  id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  role: UserRole;
  business_id: string | null;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  full_name: string;
  email: string;
  password: string;
  phone?: string | null;
  role: "customer" | "owner";
}

export interface TimeRange {
  open: string;
  close: string;
}

export interface DaySchedule {
  weekday: Weekday;
  is_closed: boolean;
  intervals: TimeRange[];
}

export interface WeeklySchedule {
  days: DaySchedule[];
}

export interface Business {
  id: string;
  name: string;
  slug: string;
  owner_id: string;
  plan: PlanName;
  timezone: string;
  currency: string;
  phone: string | null;
  address: string | null;
  description: string | null;
  is_active: boolean;
  schedule: WeeklySchedule;
  rating_avg: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

export interface BusinessCreateInput {
  name: string;
  slug?: string | null;
  timezone?: string;
  currency?: string;
  phone?: string | null;
  address?: string | null;
  description?: string | null;
}

export type BusinessUpdateInput = Partial<BusinessCreateInput> & {
  is_active?: boolean;
};

export interface Service {
  id: string;
  business_id: string;
  name: string;
  description: string | null;
  duration_minutes: number;
  buffer_minutes: number;
  price: Money;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ServiceCreateInput {
  name: string;
  description?: string | null;
  duration_minutes: number;
  buffer_minutes?: number;
  price?: number;
  is_active?: boolean;
}

export type ServiceUpdateInput = Partial<ServiceCreateInput>;

export interface Staff {
  id: string;
  business_id: string;
  user_id: string | null;
  display_name: string;
  title: string | null;
  color: string | null;
  services: string[];
  schedule: WeeklySchedule | null;
  is_active: boolean;
  rating_avg: number;
  rating_count: number;
  created_at: string;
  updated_at: string;
}

export interface StaffCreateInput {
  display_name: string;
  title?: string | null;
  color?: string | null;
  user_id?: string | null;
  services?: string[];
  is_active?: boolean;
}

export type StaffUpdateInput = Partial<StaffCreateInput>;

export interface Booking {
  id: string;
  business_id: string;
  staff_id: string;
  service_id: string;
  customer_id: string;
  start_at: string;
  end_at: string;
  status: BookingStatus;
  price: Money;
  currency: string;
  customer_name: string | null;
  customer_phone: string | null;
  notes: string | null;
  cancellation_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface BookingCreateInput {
  service_id: string;
  staff_id: string;
  start_at: string;
  notes?: string | null;
}

export interface BookingListParams {
  status?: BookingStatus;
  staff_id?: string;
  service_id?: string;
  date_from?: string;
  date_to?: string;
  skip?: number;
  limit?: number;
}

export interface BookingStatusInput {
  status: BookingStatus;
  cancellation_reason?: string | null;
}

export interface AvailabilitySlot {
  start_at: string;
  end_at: string;
}

export interface AvailabilityResponse {
  date: string;
  timezone: string;
  service_id: string;
  staff_id: string;
  slots: AvailabilitySlot[];
}

export interface Review {
  id: string;
  booking_id: string;
  business_id: string;
  staff_id: string;
  service_id: string;
  customer_id: string;
  rating: number;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReviewInput {
  rating: number;
  comment?: string | null;
}

export interface StatsItem {
  id: string;
  name: string;
  count: number;
}

export interface BusinessStats {
  total_bookings: number;
  bookings_by_status: Record<string, number>;
  revenue_completed: Money;
  currency: string;
  top_services: StatsItem[];
  top_staff: StatsItem[];
}

export interface StatsParams {
  date_from?: string;
  date_to?: string;
}
