import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';

const Dashboard = lazy(() => import('./pages/Dashboard'));
const ComplaintsList = lazy(() => import('./pages/ComplaintsList'));
const ComplaintDetail = lazy(() => import('./pages/ComplaintDetail'));
const Analytics = lazy(() => import('./pages/Analytics'));
const Escalations = lazy(() => import('./pages/Escalations'));
const SubmitComplaint = lazy(() => import('./pages/SubmitComplaint'));
const IngestionSimulator = lazy(() => import('./pages/IngestionSimulator'));

// Modern loading spinner for Suspense fallback
const PageLoader = () => (
  <div className="flex h-[80vh] w-full items-center justify-center">
    <div className="relative flex h-16 w-16">
      <div className="absolute inline-flex h-full w-full animate-ping rounded-full bg-indigo-400 opacity-20"></div>
      <div className="relative inline-flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-white border-t-transparent"></div>
      </div>
    </div>
  </div>
);

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <Router>
          <Layout>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/complaints" element={<ComplaintsList />} />
                <Route path="/complaints/:id" element={<ComplaintDetail />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/escalations" element={<Escalations />} />
                <Route path="/submit" element={<SubmitComplaint />} />
                <Route path="/simulator" element={<IngestionSimulator />} />
              </Routes>
            </Suspense>
          </Layout>
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
