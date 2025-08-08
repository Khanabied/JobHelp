import React from 'react';

const LoadingSpinner = ({ size = 'medium', message = 'Loading...' }) => {
  const sizeClasses = {
    small: 'w-4 h-4',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <div className={`${sizeClasses[size]} animate-spin`}>
        <div className="h-full w-full border-4 border-gray-200 border-t-indigo-600 rounded-full"></div>
      </div>
      {message && (
        <p className="mt-2 text-sm text-gray-600 text-center">{message}</p>
      )}
    </div>
  );
};

export default LoadingSpinner;