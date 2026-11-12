import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/layout/app-layout";
import {
  CustomerOnly,
  OwnerOnly,
  PublicOnly,
  RequireAuth,
} from "@/features/auth/require-auth";
import { BusinessProvider } from "@/features/business/business-context";
import { BookingsPage } from "@/pages/bookings-page";
import { CustomerHomePage } from "@/pages/customer-home-page";
import { DashboardPage } from "@/pages/dashboard-page";
import { LoginPage } from "@/pages/login-page";
import { NewBusinessPage } from "@/pages/new-business-page";
import { NotFoundPage } from "@/pages/not-found-page";
import { RegisterPage } from "@/pages/register-page";
import { ReportsPage } from "@/pages/reports-page";
import { ServicesPage } from "@/pages/services-page";
import { SettingsPage } from "@/pages/settings-page";
import { StaffPage } from "@/pages/staff-page";

function AppShell() {
  return (
    <BusinessProvider>
      <AppLayout />
    </BusinessProvider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<PublicOnly />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>

        <Route element={<RequireAuth />}>
          <Route element={<OwnerOnly />}>
            <Route path="/app" element={<AppShell />}>
              <Route index element={<DashboardPage />} />
              <Route path="bookings" element={<BookingsPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="services" element={<ServicesPage />} />
              <Route path="staff" element={<StaffPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="new-business" element={<NewBusinessPage />} />
            </Route>
          </Route>

          <Route element={<CustomerOnly />}>
            <Route path="/cliente" element={<AppShell />}>
              <Route index element={<CustomerHomePage />} />
            </Route>
          </Route>
        </Route>

        <Route path="/" element={<Navigate to="/app" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
}
