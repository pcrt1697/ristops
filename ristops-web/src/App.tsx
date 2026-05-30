import { BrowserRouter, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/routing/ProtectedRoute.tsx';
import LoginPage from './pages/LoginPage.tsx';
import HomePage from './pages/HomePage.tsx';
import UserProfilePage from './pages/UserProfilePage.tsx';
import GlobalQueryErrorHandler from './components/routing/GlobalQueryErrorHandler.tsx';
import AdminLayout from './components/layout/AdminLayout.tsx';
import VenueLayout from './components/layout/VenueLayout.tsx';
import AppLayout from './components/layout/AppLayout.tsx';
import RegisterPage from './pages/RegisterPage.tsx';

export default function App() {
  return (
    <BrowserRouter>
      <GlobalQueryErrorHandler />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/profile" element={<UserProfilePage />} />
            <Route path="/admin" element={<AdminLayout />}>
              <Route path="venues" element={<div>Venues</div>} />
              <Route path="users" element={<div>Users</div>} />
            </Route>
            <Route path="/venues/:venueId" element={<VenueLayout />}>
              <Route path="orders" element={<div>Orders</div>} />
              <Route path="reservations" element={<div>Reservations</div>} />
            </Route>
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
