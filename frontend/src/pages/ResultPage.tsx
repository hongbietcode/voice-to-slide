import { useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Download, Home } from 'lucide-react';
import { useJobStore } from '../stores/jobStore';
import { api } from '../api/client';

export default function ResultPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { currentJob, setCurrentJob } = useJobStore();

  useEffect(() => {
    if (jobId) {
      api.getJobStatus(jobId).then(setCurrentJob).catch(console.error);
    }
  }, [jobId, setCurrentJob]);

  if (!currentJob || currentJob.status !== 'completed') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div>Loading result...</div>
      </div>
    );
  }

  const downloadUrl = api.getDownloadUrl(jobId!);

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
            <svg
              className="w-8 h-8 text-green-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Presentation Ready!
          </h1>
          <p className="text-gray-600">
            Your presentation has been generated successfully
          </p>
        </div>

        {/* Download Section */}
        <div className="bg-blue-50 rounded-lg p-6 mb-6">
          <a
            href={downloadUrl}
            download
            className="flex items-center justify-center w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Download className="mr-2 h-5 w-5" />
            Download PPTX
          </a>
        </div>

        {/* Statistics */}
        <div className="space-y-3 mb-6">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Slides:</span>
            <span className="font-medium">{currentJob.total_slides}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Images Fetched:</span>
            <span className="font-medium">{currentJob.images_fetched}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Processing Time:</span>
            <span className="font-medium">
              {Math.floor((currentJob.processing_time_seconds || 0) / 60)} min{' '}
              {(currentJob.processing_time_seconds || 0) % 60} sec
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="pt-6 border-t">
          <Link
            to="/"
            className="flex items-center justify-center w-full py-2 text-blue-600 hover:text-blue-700"
          >
            <Home className="mr-2 h-5 w-5" />
            Create Another Presentation
          </Link>
        </div>
      </div>
    </div>
  );
}
