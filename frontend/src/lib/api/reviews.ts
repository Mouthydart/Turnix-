import { api } from "./client";
import type { Review } from "./types";

export async function listBusinessReviews(
  businessId: string,
): Promise<Review[]> {
  const { data } = await api.get<Review[]>(
    `/businesses/${businessId}/reviews`,
  );
  return data;
}
