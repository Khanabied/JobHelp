import React, { useState } from 'react';
import { LogOut, Upload, FileText, Link, User, Briefcase, MessageSquare, Linkedin, HelpCircle, Download } from 'lucide-react';
import toast from 'react-hot-toast';

// Import components
import FileUpload from './FileUpload';
import JobDescriptionForm from './JobDescriptionForm';
import LoadingSpinner from './LoadingSpinner';

// Import services
import { fileService, analysisService } from '../services/api';

const Dashboard = ({ user, onLogout }) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [jobData, setJobData] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState(null);

  const steps = [
    { id: 1, title: 'Upload Resume', icon: Upload, description: 'Upload your PDF resume' },
    { id: 2, title: 'Job Details', icon: Briefcase, description: 'Provide job description' },
    { id: 3, title: 'Processing', icon: FileText, description: 'AI analysis in progress' },
    { id: 4, title: 'Results', icon: Download, description: 'Download optimized documents' }
  ];

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
      console.log('🔄 Starting job analysis with data:', data);
      
      // Call the real analysis endpoint
      const response = await analysisService.analyzeJob(data);
      console.log('✅ Job analysis response:', response);
      
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
          status: 'completed'
        });
      } else {
        throw new Error(response.message || 'Analysis failed');
      }
      
    } catch (error) {
      console.error('❌ Analysis error:', error);
      toast.error(`Analysis failed: ${error.response?.data?.detail || error.message}`);
      setIsProcessing(false);
      setCurrentStep(2);
    }
  };

  const handleStartOver = () => {
    setCurrentStep(1);
    setUploadedFile(null);
    setJobData(null);
    setResults(null);
    setIsProcessing(false);
    
    // Cleanup uploaded file
    if (uploadedFile?.file_id) {
      fileService.cleanupFile(uploadedFile.file_id).catch(console.error);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return <FileUpload onFileUpload={handleFileUpload} />;
      case 2:
        return (
          <JobDescriptionForm 
            onSubmit={handleJobSubmit}
            onBack={() => setCurrentStep(1)}
          />
        );
      case 3:
        return (
          <div className="text-center py-12">
            <LoadingSpinner size="large" message="Analyzing your resume and job match..." />
            <div className="mt-6 space-y-2">
              <p className="text-gray-600">This may take a few minutes</p>
              <div className="max-w-md mx-auto bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  Our AI agents are working to:
                  <br />• Analyze job requirements
                  <br />• Score your resume fit
                  <br />• Generate optimization suggestions
                  <br />• Research company insights
                </p>
              </div>
            </div>
          </div>
        );
      case 4:
        return (
          <div className="text-center py-12">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-6">
              <Download className="w-8 h-8 text-green-600" />
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-4">Analysis Complete!</h3>
            <p className="text-gray-600 mb-8">Your optimized resume and career documents are ready.</p>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-8">
              <p className="text-yellow-800 text-sm">
                <strong>Phase 1 Complete!</strong> Basic infrastructure is ready. 
                Phase 2 will integrate the full CrewAI analysis and document generation.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto mb-8">
              {[
                { title: 'Optimized Resume', desc: 'ATS-friendly resume', icon: FileText },
                { title: 'Cover Letter', desc: 'Tailored for this job', icon: MessageSquare },
                { title: 'LinkedIn Profile', desc: 'Enhanced profile copy', icon: Linkedin },
                { title: 'Interview Prep', desc: 'Questions & coaching', icon: HelpCircle }
              ].map((item, idx) => (
                <div key={idx} className="bg-white border border-gray-200 rounded-lg p-4 card-hover">
                  <item.icon className="w-6 h-6 text-primary-600 mb-2" />
                  <h4 className="font-semibold text-gray-900">{item.title}</h4>
                  <p className="text-sm text-gray-600">{item.desc}</p>
                  <button 
                    disabled 
                    className="mt-2 text-sm text-gray-400 cursor-not-allowed"
                  >
                    Coming in Phase 2
                  </button>
                </div>
              ))}
            </div>

            <button
              onClick={handleStartOver}
              className="btn-primary px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
            >
              Start New Analysis
            </button>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <div className="h-8 w-8 bg-primary-600 rounded-lg flex items-center justify-center">
                <FileText className="h-5 w-5 text-white" />
              </div>
              <h1 className="ml-3 text-xl font-bold text-gray-900">Resume Optimizer</h1>
            </div>
            
            <div className="flex items-center space-x-4">
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
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`flex items-center ${index < steps.length - 1 ? 'flex-1' : ''}`}>
                  <div className={`
                    flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                    ${currentStep >= step.id 
                      ? 'bg-primary-600 border-primary-600 text-white' 
                      : 'bg-white border-gray-300 text-gray-400'}
                  `}>
                    <step.icon className="w-5 h-5" />
                  </div>
                  <div className="ml-3 hidden sm:block">
                    <p className={`text-sm font-medium ${
                      currentStep >= step.id ? 'text-primary-600' : 'text-gray-400'
                    }`}>
                      {step.title}
                    </p>
                    <p className="text-xs text-gray-500">{step.description}</p>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`
                    hidden sm:block flex-1 h-0.5 mx-4 transition-colors
                    ${currentStep > step.id ? 'bg-primary-600' : 'bg-gray-200'}
                  `} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border">
          <div className="p-6">
            {renderStepContent()}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;