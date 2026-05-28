import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { ToastProvider } from './components/Toast';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ComplaintsList from './pages/ComplaintsList';
import ComplaintDetail from './pages/ComplaintDetail';
import Analytics from './pages/Analytics';
import Escalations from './pages/Escalations';
import SubmitComplaint from './pages/SubmitComplaint';
import IngestionSimulator from './pages/IngestionSimulator';

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/complaints" element={<ComplaintsList />} />
              <Route path="/complaints/:id" element={<ComplaintDetail />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/escalations" element={<Escalations />} />
              <Route path="/submit" element={<SubmitComplaint />} />
              <Route path="/simulator" element={<IngestionSimulator />} />
            </Routes>
          </Layout>
        </Router>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
