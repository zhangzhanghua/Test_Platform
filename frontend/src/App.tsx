import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from '@/layouts/MainLayout';
import LoginPage from '@/pages/LoginPage';
import Dashboard from '@/pages/Dashboard';
import ProjectsPage from '@/pages/ProjectsPage';
import TestCasesPage from '@/pages/TestCasesPage';
import ExecutionsPage from '@/pages/ExecutionsPage';
import EnvironmentsPage from '@/pages/EnvironmentsPage';
import ReportsPage from '@/pages/ReportsPage';
import SystemPage from '@/pages/SystemPage';
import NotifyPage from '@/pages/NotifyPage';
import WebhooksPage from '@/pages/WebhooksPage';
import BugsPage from '@/pages/BugsPage';

const PrivateRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return localStorage.getItem('token') ? <>{children}</> : <Navigate to="/login" />;
};

const App: React.FC = () => (
  <BrowserRouter>
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<PrivateRoute><MainLayout /></PrivateRoute>}>
        <Route index element={<Dashboard />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="testcases" element={<TestCasesPage />} />
        <Route path="executions" element={<ExecutionsPage />} />
        <Route path="environments" element={<EnvironmentsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="system" element={<SystemPage />} />
        <Route path="notify" element={<NotifyPage />} />
        <Route path="webhooks" element={<WebhooksPage />} />
        <Route path="bugs" element={<BugsPage />} />
      </Route>
    </Routes>
  </BrowserRouter>
);

export default App;
