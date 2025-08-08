import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const FileUpload = ({ onFileUpload }) => {
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const onDrop = useCallback(async (acceptedFiles, rejectedFiles) => {
    // Handle rejected files
    if (rejectedFiles.length > 0) {
      const error = rejectedFiles[0].errors[0];
      if (error.code === 'file-invalid-type') {
        toast.error('Please upload a PDF file only');
      } else if (error.code === 'file-too-large') {
        toast.error('File size must be less than 10MB');
      } else {
        toast.error('Invalid file. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);

    try {
      await onFileUpload(file);
      setUploadedFile(file);
    } catch (error) {
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  }, [onFileUpload]);

  const {
    getRootProps,
    getInputProps,
    isDragActive,
    isDragReject
  } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
    disabled: uploading || uploadedFile
  });

  const removeFile = () => {
    setUploadedFile(null);
  };

  if (uploadedFile) {
    return (
      <div className="text-center">
        <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
          <CheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Resume Uploaded Successfully!</h3>
        <div className="bg-gray-50 rounded-lg p-4 max-w-sm mx-auto mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <FileText className="w-5 h-5 text-gray-600 mr-2" />
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900">{uploadedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
        <p className="text-gray-600 mb-8">
          Great! Your resume has been uploaded and is ready for analysis. 
          Click continue to proceed to the next step.
        </p>
      </div>
    );
  }

  return (
    <div className="text-center">
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Resume</h2>
      <p className="text-gray-600 mb-8">
        Upload your current resume in PDF format. Our AI will analyze it and optimize it for your target job.
      </p>

      <div
        {...getRootProps()}
        className={`
          file-upload-container max-w-xl mx-auto p-12 text-center cursor-pointer
          ${isDragActive && !isDragReject ? 'drag-active' : ''}
          ${isDragReject ? 'border-red-300 bg-red-50' : ''}
          ${uploading ? 'pointer-events-none opacity-50' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 flex items-center justify-center">
              <div className="w-8 h-8 animate-spin">
                <div className="h-full w-full border-4 border-gray-200 border-t-primary-600 rounded-full"></div>
              </div>
            </div>
            <p className="text-gray-600">Uploading your resume...</p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="mx-auto w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center">
              <Upload className="upload-icon text-indigo-600" />
            </div>
            
            {isDragActive ? (
              <div>
                <p className="text-lg font-medium text-primary-600">
                  {isDragReject ? 'Please upload a PDF file' : 'Drop your resume here'}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drag and drop your resume here
                </p>
                <p className="text-gray-500 mb-4">or</p>
                <button className="btn-primary px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                  Choose File
                </button>
              </div>
            )}
            
            <div className="text-xs text-gray-500 space-y-1">
              <p>Supported format: PDF only</p>
              <p>Maximum file size: 10MB</p>
            </div>
          </div>
        )}
      </div>

      <div className="mt-8 max-w-xl mx-auto">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-semibold text-blue-900 mb-2">💡 Tips for best results:</h4>
          <ul className="text-sm text-blue-800 text-left space-y-1">
            <li>• Use a well-formatted, recent version of your resume</li>
            <li>• Ensure all text is selectable (not scanned images)</li>
            <li>• Include all relevant work experience and skills</li>
            <li>• Use a professional resume format</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;