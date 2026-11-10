import { api } from "./client";
import type {
  Service,
  ServiceCreateInput,
  ServiceUpdateInput,
} from "./types";

export async function listServices(businessId: string): Promise<Service[]> {
  const { data } = await api.get<Service[]>(
    `/businesses/${businessId}/services`,
  );
  return data;
}

export async function createService(
  businessId: string,
  input: ServiceCreateInput,
): Promise<Service> {
  const { data } = await api.post<Service>(
    `/businesses/${businessId}/services`,
    input,
  );
  return data;
}

export async function updateService(
  businessId: string,
  serviceId: string,
  input: ServiceUpdateInput,
): Promise<Service> {
  const { data } = await api.patch<Service>(
    `/businesses/${businessId}/services/${serviceId}`,
    input,
  );
  return data;
}

export async function deleteService(
  businessId: string,
  serviceId: string,
): Promise<void> {
  await api.delete(`/businesses/${businessId}/services/${serviceId}`);
}
