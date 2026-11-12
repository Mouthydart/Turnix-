import { api } from "./client";
import type { BusinessReports, ReportsParams } from "./types";

export async function getBusinessReports(
  businessId: string,
  params: ReportsParams = {},
): Promise<BusinessReports> {
  const { data } = await api.get<BusinessReports>(
    `/businesses/${businessId}/reports`,
    { params },
  );
  return data;
}
