import { api } from "./client";
import type { Staff, StaffCreateInput, StaffUpdateInput } from "./types";

export async function listStaff(businessId: string): Promise<Staff[]> {
  const { data } = await api.get<Staff[]>(
    `/businesses/${businessId}/staff`,
  );
  return data;
}

export async function createStaff(
  businessId: string,
  input: StaffCreateInput,
): Promise<Staff> {
  const { data } = await api.post<Staff>(
    `/businesses/${businessId}/staff`,
    input,
  );
  return data;
}

export async function updateStaff(
  businessId: string,
  staffId: string,
  input: StaffUpdateInput,
): Promise<Staff> {
  const { data } = await api.patch<Staff>(
    `/businesses/${businessId}/staff/${staffId}`,
    input,
  );
  return data;
}

export async function deleteStaff(
  businessId: string,
  staffId: string,
): Promise<void> {
  await api.delete(`/businesses/${businessId}/staff/${staffId}`);
}
