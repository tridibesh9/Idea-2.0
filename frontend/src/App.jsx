import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import ComplaintsList from './pages/ComplaintsList';
import ComplaintDetail from './pages/ComplaintDetail';
import Analytics from './pages/Analytics';
import Escalations from './pages/Escalations';
import SubmitComplaint from './pages/SubmitComplaint';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/complaints" element={<ComplaintsList />} />
          <Route path="/complaints/:id" element={<ComplaintDetail />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/escalations" element={<Escalations />} />
          <Route path="/submit" element={<SubmitComplaint />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
