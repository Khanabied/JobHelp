import React, { useState, useEffect } from 'react';
import { 
  LogOut, Upload, FileText, Link, User, Briefcase, MessageSquare, 
  Linkedin, HelpCircle, Download, Star, TrendingUp, Zap, 
  CheckCircle, Clock, Play, Settings, Eye, BarChart3
} from 'lucide-react';
import toast from 'react-hot-toast';

// Import components
import FileUpload from './FileUpload';
import JobDescriptionForm from './JobDescriptionForm';
import LoadingSpinner from './LoadingSpinner';
import ProgressTracker from './ProgressTracker';
import ResultsDisplay from './ResultsDisplay';
import DownloadCenter from './DownloadCenter';

// Import services
import { fileService, analysisService, apiService } from '../services/api';

const Dashboard = ({ user, onLogout }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);
  const [progressSession, setProgressSession] = useState(null);
  const [analysisType, setAnalysisType] = useState('extended'); // 'basic', 'extended', 'individual'

  const steps = [
    { id: 1, title: 'Upload Resume', icon: Upload, description: 'Upload your PDF resume' },
    { id: 2, title: 'Job Details', icon: Briefcase, description: 'Provide job description' },
    { id: 3, title: 'AI Processing', icon: Zap, description: 'AI agents analyzing' },
    { id: 4, title: 'Results & Downloads', icon: Download, description: 'Get optimized documents' }
  ];

  // Check if user is admin
  const isAdmin = user && (user.email.endsWith('@admin.jobsasa.com') || user.email === 'admin@example.com');

  const handleFileUpload = async (file) => {
    try {
      const response = await fileService.uploadResume(file);
      setUploadedFile(response);
      toast.success('Resume uploaded successfully!');
      setCurrentStep(2);
    } catch (error) {
      toast.error('Upload failed. Please try again.');
      console.error('Upload error:', error);
    }
  };

  const handleJobSubmit = async (data) => {
    setJobData(data);
    setCurrentStep(3);
    setIsProcessing(true);
    
    try {
      console.log(`🔄 Starting ${analysisType} analysis with data:`, data);
      
      let response;
      if (analysisType === 'basic') {
        response = await analysisService.analyzeJob(data);
      } else if (analysisType === 'extended') {
        response = await analysisService.analyzeJobExtended(data);
        
        // Set up progress tracking for extended analysis
        if (response.session_id) {
          setProgressSession(response.session_id);
          // Start polling for progress
          const pollProgress = async () => {
            try {
              const progressData = await apiService.get(`/api/progress/${response.session_id}`);
              
              if (progressData.status === 'completed') {
                // Analysis completed, get results
                const detailedResults = await analysisService.getExtendedAnalysisResults(progressData.result?.analysis_id);
                setResults({
                  analysis_id: progressData.result?.analysis_id,
                  job_input: progressData.result?.job_input,
                  company_name: progressData.result?.company_name,
                  detailed_results: detailedResults.results,
                  status: 'completed',
                  analysis_type: 'extended'
                });
                setIsProcessing(false);
                setCurrentStep(4);
                return;
              } else if (progressData.status === 'failed') {
                throw new Error(progressData.error || 'Analysis failed');
              }
              
              // Continue polling if still running
              setTimeout(pollProgress, 3000);
            } catch (error) {
              console.error('Progress polling error:', error);
              setIsProcessing(false);
              setCurrentStep(2);
              toast.error('Failed to track progress');
            }
          };
          
          // Start polling after a delay
          setTimeout(pollProgress, 3000);
        }
        return;
      }
      
      console.log('✅ Analysis response:', response);
      
      if (response.status === 'success') {
        // Wait a moment for processing to complete
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Fetch detailed results
        const detailedResults = await analysisService.getAnalysisResults(response.analysis_id);
        console.log('📊 Detailed results:', detailedResults);
        
        setIsProcessing(false);
        setCurrentStep(4);
        setResults({
          analysis_id: response.analysis_id,
          job_input: response.job_input,
          company_name: response.company_name,
          detailed_results: detailedResults.results,
          status: 'completed',
          analysis_type: analysisType
        });
      } else {
        throw new Error(response.message || 'Analysis failed');
      }
      
    } catch (error) {
      console.error('❌ Analysis error:', error);
      toast.error(`Analysis failed: ${error.response?.data?.detail || error.message}`);
      setIsProcessing(false);
      setCurrentStep(2);
      setProgressSession(null);
    }
  };

  const handleStartOver = () => {
    setCurrentStep(1);
    setUploadedFile(null);
    setJobData(null);
    setResults(null);
    setIsProcessing(false);
    setProgressSession(null);
    
    // Cleanup uploaded file
    if (uploadedFile?.file_id) {
      fileService.cleanupFile(uploadedFile.file_id).catch(console.error);
    }
  };

  const handleRunIndividualAgent = async (agentType) => {
    if (!jobData) {
      toast.error('Please provide job details first');
      return;
    }

    try {
      setIsProcessing(true);
      toast.success(`Starting ${agentType} generation...`);

      let response;
      switch (agentType) {
        case 'cover_letter':
          response = await analysisService.generateCoverLetter(jobData);
          break;
        case 'linkedin':
          response = await analysisService.optimizeLinkedIn(jobData);
          break;
        case 'interview':
          response = await analysisService.prepareInterview(jobData);
          break;
        case 'basic_resume':
          response = await apiService.post('/api/agents/basic-resume', jobData);
          break;
        default:
          throw new Error('Unknown agent type');
      }

      if (response.status === 'success') {
        toast.success(`${agentType.replace('_', ' ')} completed!`);
        // You can handle the individual result here
        console.log(`${agentType} result:`, response.result);
      } else {
        throw new Error(response.message || 'Generation failed');
      }
    } catch (error) {
      console.error(`${agentType} error:`, error);
      toast.error(`${agentType} failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="animate-slide-up">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold gradient-text mb-4">
                Welcome to JobSasa
              </h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Your AI-powered career optimization platform. Upload your resume to get started 
                with personalized job matching, resume optimization, and career guidance.
              </p>
            </div>
            <FileUpload onFileUpload={handleFileUpload} />
          </div>
        );
      case 2:
        return (
          <div className="animate-slide-up">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Choose Your Analysis Type</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div
                  className={`card-hover p-4 cursor-pointer ${
                    analysisType === 'basic' ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                  }`}
                  onClick={() => setAnalysisType('basic')}
                >
                  <FileText className="w-8 h-8 text-blue-600 mb-3" />
                  <h3 className="font-semibold mb-2">Basic Resume Optimization</h3>
                  <p className="text-sm text-gray-600">Quick resume optimization and job matching</p>
                </div>

                <div
                  className={`card-hover p-4 cursor-pointer ${
                    analysisType === 'extended' ? 'ring-2 ring-purple-500 bg-purple-50' : ''
                  }`}
                  onClick={() => setAnalysisType('extended')}
                >
                  <Star className="w-8 h-8 text-purple-600 mb-3" />
                  <h3 className="font-semibold mb-2">Complete Career Package</h3>
                  <p className="text-sm text-gray-600">All 8 AI agents: Resume, Cover Letter, LinkedIn, Interview Prep</p>
                </div>

                <div
                  className={`card-hover p-4 cursor-pointer ${
                    analysisType === 'individual' ? 'ring-2 ring-green-500 bg-green-50' : ''
                  }`}
                  onClick={() => setAnalysisType('individual')}
                >
                  <Settings className="w-8 h-8 text-green-600 mb-3" />
                  <h3 className="font-semibold mb-2">Individual Agents</h3>
                  <p className="text-sm text-gray-600">Run specific agents as needed</p>
                </div>
              </div>
            </div>
            
            {analysisType === 'individual' ? (
              <div className="space-y-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { type: 'basic_resume', label: 'Resume Only', icon: FileText },
                    { type: 'cover_letter', label: 'Cover Letter', icon: MessageSquare },
                    { type: 'linkedin', label: 'LinkedIn', icon: Linkedin },
                    { type: 'interview', label: 'Interview Prep', icon: HelpCircle }
                  ].map((agent) => (
                    <button
                      key={agent.type}
                      onClick={() => handleRunIndividualAgent(agent.type)}
                      disabled={isProcessing}
                      className="card-hover p-4 text-center border-2 border-dashed border-gray-300 hover:border-blue-500 transition-colors"
                    >
                      <agent.icon className="w-6 h-6 mx-auto mb-2 text-gray-600" />
                      <span className="text-sm font-medium">{agent.label}</span>
                    </button>
                  ))}
                </div>
                <JobDescriptionForm 
                  onSubmit={handleJobSubmit}
                  onBack={() => setCurrentStep(1)}
                  submitLabel="Provide Job Details"
                  showAnalysisType={false}
                />
              </div>
            ) : (
              <JobDescriptionForm 
                onSubmit={handleJobSubmit}
                onBack={() => setCurrentStep(1)}
                submitLabel={`Start ${analysisType === 'extended' ? 'Complete' : 'Basic'} Analysis`}
                analysisType={analysisType}
              />
            )}
          </div>
        );
      case 3:
        return (
          <div className="text-center py-12 animate-fade-in">
            <div className="mb-8">
              <Zap className="w-16 h-16 text-yellow-500 mx-auto mb-4 animate-pulse" />
              <h2 className="text-2xl font-bold text-gray-900 mb-4">AI Agents at Work</h2>
              <p className="text-gray-600 mb-6">
                {analysisType === 'extended' ? 
                  'Our 8 AI agents are analyzing your profile and generating comprehensive career documents...' :
                  'Optimizing your resume for the target position...'
                }
              </p>
            </div>

            {progressSession && (
              <div className="mb-6">
                <ProgressTracker sessionId={progressSession} />
              </div>
            )}

            <LoadingSpinner size="large" message="This may take a few minutes..." />
            
            <div className="mt-8 max-w-md mx-auto">
              <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-6">
                <p className="text-sm text-gray-700 mb-4">
                  <strong>What's happening:</strong>
                </p>
                {analysisType === 'extended' ? (
                  <ul className="text-sm text-gray-600 space-y-2 text-left">
                    <li>• Analyzing job requirements</li>
                    <li>• Optimizing your resume</li>
                    <li>• Researching company culture</li>
                    <li>• Writing personalized cover letter</li>
                    <li>• Optimizing LinkedIn profile</li>
                    <li>• Preparing interview questions</li>
                    <li>• Generating final report</li>
                  </ul>
                ) : (
                  <ul className="text-sm text-gray-600 space-y-2 text-left">
                    <li>• Analyzing job requirements</li>
                    <li>• Scoring resume fit</li>
                    <li>• Generating optimizations</li>
                    <li>• Creating final report</li>
                  </ul>
                )}
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="animate-slide-up">
            <ResultsDisplay 
              results={results}
              onStartOver={handleStartOver}
              analysisType={analysisType}
            />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50">
      {/* Header */}
      <header className="glassmorphism shadow-sm border-b border-white/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="h-10 w-10 bg-gradient-to-r from-indigo-500 to-cyan-500 rounded-lg flex items-center justify-center">
                <FileText className="h-6 w-6 text-white" />
              </div>
              <div className="ml-3">
                <h1 className="text-xl font-bold gradient-text">JobSasa</h1>
                <p className="text-sm text-gray-600">AI Career Optimization</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {isAdmin && (
                <a
                  href="/admin"
                  className="flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors"
                >
                  <BarChart3 className="h-4 w-4 mr-1" />
                  Admin
                </a>
              )}
              <div className="flex items-center text-sm text-gray-600">
                <User className="h-4 w-4 mr-1" />
                {user.full_name}
              </div>
              <button
                onClick={onLogout}
                className="flex items-center text-sm text-gray-600 hover:text-gray-900 transition-colors"
              >
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Progress Steps */}
      <div className="glassmorphism border-b border-white/20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center progress-step">
                <div className={`flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}`}>
                  <div className={`
                    flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all duration-300
                    ${currentStep >= step.id 
                      ? 'bg-gradient-to-r from-indigo-500 to-cyan-500 border-indigo-500 text-white shadow-lg transform scale-105' 
                      : 'bg-white border-gray-300 text-gray-400'}
                  `}>
                    <step.icon className="w-5 h-5" />
                  </div>
                  <div className="ml-4 hidden sm:block">
                    <p className={`text-sm font-medium transition-colors ${
                      currentStep >= step.id ? 'text-indigo-600' : 'text-gray-400'
                    }`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-gray-500">{step.description}</p>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`
                    hidden sm:block flex-1 h-0.5 mx-6 transition-colors
                    ${currentStep > step.id ? 'bg-gradient-to-r from-indigo-500 to-cyan-500' : 'bg-gray-200'}
                  `} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="glassmorphism rounded-2xl shadow-xl border border-white/20">
          <div className="p-6 md:p-8">
            {renderStepContent()}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;