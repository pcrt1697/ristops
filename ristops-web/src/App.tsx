import { BrowserRouter, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/routing/ProtectedRoute.tsx';
import UserLoginPage from './pages/user/UserLoginPage.tsx';
import HomePage from './pages/HomePage.tsx';
import UserProfilePage from './pages/user/UserProfilePage.tsx';
import GlobalQueryErrorHandler from './components/routing/GlobalQueryErrorHandler.tsx';
import ErrorBoundaryWithReset from './components/routing/ErrorBoundary.tsx';
import VenueLayout from './components/layout/VenueLayout.tsx';
import AppLayout from './components/layout/AppLayout.tsx';
import UserRegisterPage from './pages/user/UserRegisterPage.tsx';
import NotFoundPage from './pages/NotFoundPage.tsx';
import { GlobalErrorProvider } from './context/error.provider.tsx';
import AdminVenuePage from './pages/admin/AdminVenuePage.tsx';
import AdminAclPage from './pages/admin/AdminAclPage.tsx';

export default function App() {
  return (
    <BrowserRouter>
      <GlobalErrorProvider>
        <GlobalQueryErrorHandler />
        <ErrorBoundaryWithReset>
          <Routes>
            <Route path="/login" element={<UserLoginPage />} />
            <Route path="/register" element={<UserRegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/profile" element={<UserProfilePage />} />
                <Route path="/admin/venues" element={<AdminVenuePage />} />
                <Route
                  path="/admin/access-control"
                  element={<AdminAclPage />}
                />
                <Route path="/venues/:venueId" element={<VenueLayout />}>
                  <Route path="orders" element={<div>Orders</div>} />
                  <Route
                    path="reservations"
                    element={<div>Reservations</div>}
                  />
                </Route>
              </Route>
              <Route path="*" element={<NotFoundPage />} />
            </Route>
          </Routes>
        </ErrorBoundaryWithReset>
      </GlobalErrorProvider>
    </BrowserRouter>
  );
}
