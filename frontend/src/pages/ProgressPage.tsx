import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { CheckCircle, Circle, Loader } from 'lucide-react';
import { useJobStore } from '../stores/jobStore';
import { useWebSocket } from '../hooks/useWebSocket';
import { api } from '../api/client';

export default function ProgressPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const { currentJob, setCurrentJob, updateJobStatus, updateStructure, setEditing } = useJobStore();

  // Fetch initial job status
  useEffect(() => {
    if (jobId) {
      api.getJobStatus(jobId).then(setCurrentJob).catch(console.error);
    }
  }, [jobId, setCurrentJob]);

  // WebSocket for real-time updates
  useWebSocket(jobId || null, {
    onMessage: (message) => {
      if (message.type === 'progress') {
        updateJobStatus(
          message.status || 'pending',
          message.progress_percentage || 0,
          message.current_step
        );
      } else if (message.type === 'structure_ready') {
        if (message.structure) {
          updateStructure(message.structure);
          setEditing(true);
          navigate(`/job/${jobId}/edit`);
        }
      } else if (message.type === 'completed') {
        navigate(`/job/${jobId}/result`);
      } else if (message.type === 'error') {
        console.error('Job error:', message.error_message);
      }
    },
  });

  if (!currentJob) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader className="animate-spin h-8 w-8 text-blue-500" />
      </div>
    );
  }

  const steps = [
    { name: 'Audio uploaded', status: 'completed' },
    { name: 'Transcription', status: currentJob.progress_percentage >= 25 ? 'completed' : currentJob.progress_percentage >= 10 ? 'in_progress' : 'pending' },
    { name: 'Structure analysis', status: currentJob.progress_percentage >= 35 ? 'completed' : currentJob.progress_percentage >= 25 ? 'in_progress' : 'pending' },
    { name: 'Generating slides', status: currentJob.progress_percentage >= 80 ? 'completed' : currentJob.progress_percentage >= 40 ? 'in_progress' : 'pending' },
    { name: 'Rendering images', status: currentJob.progress_percentage >= 90 ? 'completed' : currentJob.progress_percentage >= 80 ? 'in_progress' : 'pending' },
    { name: 'Assembling PPTX', status: currentJob.progress_percentage === 100 ? 'completed' : currentJob.progress_percentage >= 90 ? 'in_progress' : 'pending' },
  ];

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-3xl w-full bg-white rounded-lg shadow-xl p-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-6">
          Generating Presentation...
        </h1>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>{currentJob.progress_percentage}%</span>
            <span>{currentJob.current_step}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-500"
              style={{ width: `${currentJob.progress_percentage}%` }}
            />
          </div>
        </div>

        {/* Timeline */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Progress Timeline</h2>
          {steps.map((step, index) => (
            <div key={index} className="flex items-center">
              {step.status === 'completed' ? (
                <CheckCircle className="h-6 w-6 text-green-500 mr-3" />
              ) : step.status === 'in_progress' ? (
                <Loader className="h-6 w-6 text-blue-500 animate-spin mr-3" />
              ) : (
                <Circle className="h-6 w-6 text-gray-300 mr-3" />
              )}
              <span
                className={
                  step.status === 'completed'
                    ? 'text-gray-900 font-medium'
                    : step.status === 'in_progress'
                    ? 'text-blue-600 font-medium'
                    : 'text-gray-400'
                }
              >
                {step.name}
              </span>
            </div>
          ))}
        </div>

        {currentJob.error_message && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <strong>Error:</strong> {currentJob.error_message}
          </div>
        )}
      </div>
    </div>
  );
}
