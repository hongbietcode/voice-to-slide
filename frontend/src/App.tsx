import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import UploadPage from './pages/UploadPage';
import ProgressPage from './pages/ProgressPage';
import EditorPage from './pages/EditorPage';
import ResultPage from './pages/ResultPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/job/:jobId" element={<ProgressPage />} />
          <Route path="/job/:jobId/edit" element={<EditorPage />} />
          <Route path="/job/:jobId/result" element={<ResultPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
