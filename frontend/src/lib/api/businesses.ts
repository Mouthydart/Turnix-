import { api } from "./client";
import type {
  Business,
  BusinessCreateInput,
  BusinessUpdateInput,
} from "./types";

export async function listBusinesses(): Promise<Business[]> {
  const { data } = await api.get<Business[]>("/businesses");
  return data;
}

export async function getBusiness(businessId: string): Promise<Business> {
  const { data } = await api.get<Business>(`/businesses/${businessId}`);
  return data;
}

export async function createBusiness(
  input: BusinessCreateInput,
): Promise<Business> {
  const { data } = await api.post<Business>("/businesses", input);
  return data;
}

export async function updateBusiness(
  businessId: string,
  input: BusinessUpdateInput,
): Promise<Business> {
  const { data } = await api.patch<Business>(
    `/businesses/${businessId}`,
    input,
  );
  return data;
}

export async function deleteBusiness(businessId: string): Promise<void> {
  await api.delete(`/businesses/${businessId}`);
}
