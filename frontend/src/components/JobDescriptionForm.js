import React, { useState } from 'react';
import { ArrowLeft, Link as LinkIcon, FileText, Briefcase } from 'lucide-react';

const JobDescriptionForm = ({ onSubmit, onBack }) => {
  const [inputType, setInputType] = useState('url'); // 'url' or 'text'
  const [formData, setFormData] = useState({
    jobUrl: '',
    jobDescription: '',
    companyName: ''
  });
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form
    if (inputType === 'url' && !formData.jobUrl.trim()) {
      alert('Please provide a job URL');
      return;
    }
    
    if (inputType === 'text' && !formData.jobDescription.trim()) {
      alert('Please provide a job description');
      return;
    }
    
    if (!formData.companyName.trim()) {
      alert('Please provide the company name');
      return;
    }

    setLoading(true);

    const submitData = {
      company_name: formData.companyName,
      ...(inputType === 'url' 
        ? { job_url: formData.jobUrl }
        : { job_description: formData.jobDescription }
      )
    };

    try {
      await onSubmit(submitData);
    } catch (error) {
      console.error('Submit error:', error);
    } finally {
      setLoading(false);
    }
  };

  const switchInputType = (type) => {
    setInputType(type);
    // Clear the opposite field when switching
    if (type === 'url') {
      setFormData({ ...formData, jobDescription: '' });
    } else {
      setFormData({ ...formData, jobUrl: '' });
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center mb-6">
        <button
          onClick={onBack}
          className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4 mr-1" />
          Back
        </button>
      </div>

      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Job Description</h2>
        <p className="text-gray-600">
          Provide the job description either by URL or by pasting the text directly.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Input Type Selection */}
        <div className="flex space-x-4 p-1 bg-gray-100 rounded-lg">
          <button
            type="button"
            onClick={() => switchInputType('url')}
            className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              inputType === 'url'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <LinkIcon className="w-4 h-4 mr-2" />
            Job URL
          </button>
          <button
            type="button"
            onClick={() => switchInputType('text')}
            className={`flex-1 flex items-center justify-center py-2 px-4 rounded-md text-sm font-medium transition-colors ${
              inputType === 'text'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            <FileText className="w-4 h-4 mr-2" />
            Paste Text
          </button>
        </div>

        {/* Job URL Input */}
        {inputType === 'url' && (
          <div>
            <label htmlFor="jobUrl" className="block text-sm font-medium text-gray-700 mb-2">
              Job Posting URL
            </label>
            <div className="relative">
              <LinkIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="url"
                id="jobUrl"
                name="jobUrl"
                value={formData.jobUrl}
                onChange={handleInputChange}
                placeholder="https://company.com/careers/job-posting"
                className="pl-10 w-full px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                required={inputType === 'url'}
              />
            </div>
            <p className="mt-2 text-sm text-gray-500">
              Paste the full URL of the job posting from LinkedIn, Indeed, company website, etc.
            </p>
          </div>
        )}

        {/* Job Description Text Input */}
        {inputType === 'text' && (
          <div>
            <label htmlFor="jobDescription" className="block text-sm font-medium text-gray-700 mb-2">
              Job Description
            </label>
            <textarea
              id="jobDescription"
              name="jobDescription"
              rows={12}
              value={formData.jobDescription}
              onChange={handleInputChange}
              placeholder="Paste the complete job description here including requirements, responsibilities, qualifications, etc."
              className="w-full px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-vertical"
              required={inputType === 'text'}
            />
            <p className="mt-2 text-sm text-gray-500">
              Include all relevant details: job title, requirements, responsibilities, qualifications, benefits, etc.
            </p>
          </div>
        )}

        {/* Company Name Input */}
        <div>
          <label htmlFor="companyName" className="block text-sm font-medium text-gray-700 mb-2">
            Company Name *
          </label>
          <div className="relative">
            <Briefcase className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              id="companyName"
              name="companyName"
              value={formData.companyName}
              onChange={handleInputChange}
              placeholder="e.g., Google, Microsoft, Apple"
              className="pl-10 w-full px-3 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              required
            />
          </div>
          <p className="mt-2 text-sm text-gray-500">
            This helps our AI research company-specific insights for better optimization.
          </p>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={onBack}
            className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Back
          </button>
          <button
            type="submit"
            disabled={loading}
            className="btn-primary px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Start Analysis'}
          </button>
        </div>
      </form>

      {/* Tips */}
      <div className="mt-8 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <h4 className="font-semibold text-amber-900 mb-2">📋 What happens next?</h4>
        <ul className="text-sm text-amber-800 space-y-1">
          <li>• Our AI will analyze the job requirements and your resume</li>
          <li>• You'll get a detailed match score and optimization suggestions</li>
          <li>• We'll generate a tailored resume, cover letter, and LinkedIn profile</li>
          <li>• Interview preparation materials will be created specifically for this role</li>
        </ul>
      </div>
    </div>
  );
};

export default JobDescriptionForm;