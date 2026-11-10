import { api } from "./client";
import type {
  AvailabilityResponse,
  Booking,
  BookingListParams,
  BookingStatusInput,
  Review,
  ReviewInput,
} from "./types";

export async function listBusinessBookings(
  businessId: string,
  params: BookingListParams = {},
): Promise<Booking[]> {
  const { data } = await api.get<Booking[]>(
    `/businesses/${businessId}/bookings`,
    { params },
  );
  return data;
}

export async function getBooking(
  businessId: string,
  bookingId: string,
): Promise<Booking> {
  const { data } = await api.get<Booking>(
    `/businesses/${businessId}/bookings/${bookingId}`,
  );
  return data;
}

export async function updateBookingStatus(
  businessId: string,
  bookingId: string,
  input: BookingStatusInput,
): Promise<Booking> {
  const { data } = await api.patch<Booking>(
    `/businesses/${businessId}/bookings/${bookingId}/status`,
    input,
  );
  return data;
}

export async function deleteBooking(
  businessId: string,
  bookingId: string,
): Promise<void> {
  await api.delete(`/businesses/${businessId}/bookings/${bookingId}`);
}

export async function getAvailability(
  businessId: string,
  params: { service_id: string; staff_id: string; date: string },
): Promise<AvailabilityResponse> {
  const { data } = await api.get<AvailabilityResponse>(
    `/businesses/${businessId}/availability`,
    { params },
  );
  return data;
}

export async function listMyBookings(): Promise<Booking[]> {
  const { data } = await api.get<Booking[]>("/bookings/mine");
  return data;
}

export async function createBooking(
  businessId: string,
  input: { service_id: string; staff_id: string; start_at: string; notes?: string },
): Promise<Booking> {
  const { data } = await api.post<Booking>(
    `/businesses/${businessId}/bookings`,
    input,
  );
  return data;
}

export async function createReview(
  bookingId: string,
  input: ReviewInput,
): Promise<Review> {
  const { data } = await api.post<Review>(
    `/bookings/${bookingId}/review`,
    input,
  );
  return data;
}
