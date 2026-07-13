import { useEffect, useState } from "react";
import { Routes, Route, useNavigate, useLocation } from "react-router-dom";

import { api } from "./api";
import { Me } from "./types";
import BottomNav from "./components/BottomNav";

import Dashboard from "./pages/Dashboard";
import Services from "./pages/Services";
import ServiceDetail from "./pages/ServiceDetail";
import Network from "./pages/Network";
import Support from "./pages/Support";
import Legal from "./pages/Legal";
import Guide from "./pages/Guide";
import Onboarding from "./pages/Onboarding";
import Agency from "./pages/Agency";
import Purchase from "./pages/Purchase";
import WalletPage from "./pages/Wallet";
import AdminHome from "./pages/admin/AdminHome";
import AdminWalletTopups from "./pages/admin/AdminWalletTopups";
import AdminServices from "./pages/admin/AdminServices";
import AdminReceipts from "./pages/admin/AdminReceipts";
import AdminPricing from "./pages/admin/AdminPricing";
import AdminAgencyTiers from "./pages/admin/AdminAgencyTiers";
import AdminBroadcast from "./pages/admin/AdminBroadcast";
import AdminAdmins from "./pages/admin/AdminAdmins";
import AdminActivityLog from "./pages/admin/AdminActivityLog";
import AdminReferralConfig from "./pages/admin/AdminReferralConfig";
import AdminUsers from "./pages/admin/AdminUsers";
import AdminPaymentCards from "./pages/admin/AdminPaymentCards";
import AdminAgencyRequests from "./pages/admin/AdminAgencyRequests";
import AdminAccounting from "./pages/admin/AdminAccounting";

export default function App() {
  const [me, setMe] = useState<Me | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    api.get<Me>("/me").then(setMe).catch(() => {});
  }, []);

  useEffect(() => {
    if (me && !me.onboarding_seen && location.pathname !== "/onboarding") {
      navigate("/onboarding");
    }
  }, [me]);

  return (
    <div className="min-h-screen">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/services" element={<Services />} />
        <Route path="/services/:id" element={<ServiceDetail />} />
        <Route path="/network" element={<Network />} />
        <Route path="/support" element={<Support />} />
        <Route path="/legal" element={<Legal />} />
        <Route path="/guide" element={<Guide />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/purchase" element={<Purchase />} />
        <Route path="/wallet" element={<WalletPage />} />
        <Route path="/agency" element={<Agency />} />
        {me?.is_admin && (
          <>
            <Route path="/admin" element={<AdminHome />} />
            <Route path="/admin/services" element={<AdminServices />} />
            <Route path="/admin/receipts" element={<AdminReceipts />} />
            <Route path="/admin/pricing" element={<AdminPricing />} />
            <Route path="/admin/agency-tiers" element={<AdminAgencyTiers />} />
            <Route path="/admin/broadcast" element={<AdminBroadcast />} />
            <Route path="/admin/admins" element={<AdminAdmins />} />
            <Route path="/admin/activity" element={<AdminActivityLog />} />
            <Route path="/admin/wallet-topups" element={<AdminWalletTopups />} />
            <Route path="/admin/referral-config" element={<AdminReferralConfig />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/payment-cards" element={<AdminPaymentCards />} />
            <Route path="/admin/agency-requests" element={<AdminAgencyRequests />} />
            <Route path="/admin/accounting" element={<AdminAccounting />} />
          </>
        )}
      </Routes>
      <BottomNav isAdmin={!!me?.is_admin} />
    </div>
  );
}
