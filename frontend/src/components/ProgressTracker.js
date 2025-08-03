import React, { useState, useEffect } from 'react';
import { CheckCircle, Clock, AlertCircle, Zap } from 'lucide-react';
import { apiService } from '../services/api';

const ProgressTracker = ({ sessionId }) => {
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) return;

    const fetchProgress = async () => {
      try {
        const progressData = await apiService.get(`/api/progress/${sessionId}`);
        setProgress(progressData);
        setLoading(false);

        // Continue polling if not completed
        if (progressData.status === 'running' || progressData.status === 'initialized') {
          setTimeout(fetchProgress, 2000);
        }
      } catch (error) {
        console.error('Error fetching progress:', error);
        setLoading(false);
      }
    };

    fetchProgress();
  }, [sessionId]);

  if (loading || !progress) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-4"></div>
        <div className="h-2 bg-gray-200 rounded w-full mb-2"></div>
        <div className="h-2 bg-gray-200 rounded w-5/6 mx-auto"></div>
      </div>
    );
  }

  const getStepIcon = (step) => {
    switch (step.status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <Zap className="w-5 h-5 text-yellow-500 animate-pulse" />;
      case 'failed':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStepClass = (step) => {
    const baseClass = "flex items-center p-3 rounded-lg transition-all duration-300";
    switch (step.status) {
      case 'completed':
        return `${baseClass} bg-green-50 border border-green-200`;
      case 'running':
        return `${baseClass} bg-yellow-50 border border-yellow-200 shadow-md transform scale-105`;
      case 'failed':
        return `${baseClass} bg-red-50 border border-red-200`;
      default:
        return `${baseClass} bg-gray-50 border border-gray-200`;
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Overall Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">Overall Progress</span>
          <span className="text-sm font-bold text-gray-900">{progress.overall_progress}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className="progress-bar h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progress.overall_progress}%` }}
          ></div>
        </div>
        <div className="mt-2 text-center">
          <span className="text-sm text-gray-600">
            Step {progress.current_step} of {progress.total_steps}
          </span>
        </div>
      </div>

      {/* Step Details */}
      <div className="space-y-3">
        {progress.steps.map((step, index) => (
          <div key={step.step_id} className={getStepClass(step)}>
            <div className="flex items-center flex-1">
              <div className="mr-3">
                {getStepIcon(step)}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-900">{step.name}</span>
                  {step.progress_percent > 0 && (
                    <span className="text-xs font-medium text-gray-600">
                      {step.progress_percent}%
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{step.description}</p>
                {step.message && (
                  <p className="text-xs text-gray-500 mt-1 italic">{step.message}</p>
                )}
                {step.error && (
                  <p className="text-xs text-red-600 mt-1">{step.error}</p>
                )}
              </div>
            </div>
            {step.status === 'running' && step.progress_percent < 100 && (
              <div className="ml-8 mt-2">
                <div className="w-32 bg-gray-200 rounded-full h-1.5">
                  <div
                    className="bg-yellow-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${step.progress_percent}%` }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Status Message */}
      <div className="mt-6 text-center">
        <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium ${
          progress.status === 'completed' ? 'bg-green-100 text-green-800' :
          progress.status === 'failed' ? 'bg-red-100 text-red-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {progress.status === 'completed' && <CheckCircle className="w-4 h-4 mr-2" />}
          {progress.status === 'running' && <Zap className="w-4 h-4 mr-2 animate-pulse" />}
          {progress.status === 'failed' && <AlertCircle className="w-4 h-4 mr-2" />}
          {progress.status === 'completed' ? 'Analysis Complete!' :
           progress.status === 'failed' ? 'Analysis Failed' :
           'Processing...'}
        </div>
      </div>

      {/* Time Estimates */}
      {progress.start_time && (
        <div className="mt-4 text-center text-xs text-gray-500">
          Started: {new Date(progress.start_time).toLocaleTimeString()}
          {progress.end_time && (
            <> • Completed: {new Date(progress.end_time).toLocaleTimeString()}</>
          )}
        </div>
      )}
    </div>
  );
};

export default ProgressTracker;