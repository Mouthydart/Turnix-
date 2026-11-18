import { api } from "./client";
import type { CatalogBusiness, CatalogBusinessDetail } from "./types";

export interface CatalogListParams {
  q?: string;
  skip?: number;
  limit?: number;
}

export async function listCatalogBusinesses(
  params: CatalogListParams = {},
): Promise<CatalogBusiness[]> {
  const { data } = await api.get<CatalogBusiness[]>(
    "/catalog/businesses",
    { params },
  );
  return data;
}

export async function getCatalogBusiness(
  businessId: string,
): Promise<CatalogBusinessDetail> {
  const { data } = await api.get<CatalogBusinessDetail>(
    `/catalog/businesses/${businessId}`,
  );
  return data;
}
