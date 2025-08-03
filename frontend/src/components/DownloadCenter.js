import React, { useState, useEffect } from 'react';
import { 
  Download, FileText, Calendar, Clock, AlertCircle, 
  CheckCircle, RefreshCw, Trash2, Eye
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiService } from '../services/api';

const DownloadCenter = ({ user }) => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/api/documents/list');
      setDocuments(response.documents || []);
    } catch (error) {
      console.error('Error fetching documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (documentId, fileType) => {
    try {
      const response = await apiService.get(`/api/documents/download/${documentId}/${fileType}`);
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${fileType}_${new Date().toISOString().split('T')[0]}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      toast.success(`${fileType} downloaded successfully`);
    } catch (error) {
      console.error('Download error:', error);
      toast.error(`Failed to download ${fileType}`);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const isExpiringSoon = (expiryDate) => {
    const now = new Date();
    const expiry = new Date(expiryDate);
    const hoursUntilExpiry = (expiry - now) / (1000 * 60 * 60);
    return hoursUntilExpiry < 24;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading your documents...</p>
        </div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mx-auto w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
          <FileText className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">No Documents Generated</h3>
        <p className="text-gray-600 mb-6">Complete an analysis to generate professional documents.</p>
        <button
          onClick={() => window.location.href = '/dashboard'}
          className="btn-primary px-6 py-3 bg-gradient-to-r from-indigo-500 to-cyan-500 text-white rounded-lg"
        >
          Start Analysis
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900">Document Center</h2>
        <button
          onClick={fetchDocuments}
          className="flex items-center px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      <div className="grid gap-6">
        {documents.map((doc) => {
          const expiringSoon = isExpiringSoon(doc.expires_at);
          
          return (
            <div 
              key={doc.document_id}
              className={`card-hover p-6 border-l-4 ${
                expiringSoon ? 'border-l-red-400 bg-red-50' : 'border-l-blue-400'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <FileText className="w-5 h-5 text-blue-600 mr-2" />
                    <h3 className="font-semibold text-gray-900">
                      Analysis Documents
                    </h3>
                    {expiringSoon && (
                      <span className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                        Expires Soon
                      </span>
                    )}
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-2" />
                      Created: {formatDate(doc.created_at)}
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 mr-2" />
                      Expires: {formatDate(doc.expires_at)}
                    </div>
                  </div>

                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-900 mb-2">Available Files:</h4>
                    <div className="flex flex-wrap gap-2">
                      {doc.available_files.map((fileType) => (
                        <span
                          key={fileType}
                          className="px-3 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                        >
                          {fileType.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="ml-4 space-y-2">
                  {doc.available_files.map((fileType) => (
                    <button
                      key={fileType}
                      onClick={() => handleDownload(doc.document_id, fileType)}
                      className="flex items-center px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                    >
                      <Download className="w-4 h-4 mr-1" />
                      {fileType.includes('pdf') ? 'PDF' : 'DOCX'}
                    </button>
                  ))}
                </div>
              </div>

              {expiringSoon && (
                <div className="mt-4 p-3 bg-red-100 border border-red-200 rounded-lg">
                  <div className="flex items-center text-red-800">
                    <AlertCircle className="w-4 h-4 mr-2" />
                    <span className="text-sm font-medium">
                      This document will expire in less than 24 hours. Download now!
                    </span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start">
          <CheckCircle className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">Document Management</p>
            <ul className="space-y-1">
              <li>• Documents are available for 48 hours after generation</li>
              <li>• DOCX files are editable and ATS-compliant</li>
              <li>• PDF files are print-ready and professional</li>
              <li>• Generate new documents anytime with fresh analysis</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DownloadCenter;