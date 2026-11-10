import { api } from "./client";
import type { BusinessStats, StatsParams } from "./types";

export async function getBusinessStats(
  businessId: string,
  params: StatsParams = {},
): Promise<BusinessStats> {
  const { data } = await api.get<BusinessStats>(
    `/businesses/${businessId}/stats`,
    { params },
  );
  return data;
}
