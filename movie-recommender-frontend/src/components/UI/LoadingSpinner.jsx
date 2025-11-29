const LoadingSpinner = () => {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="flex flex-col items-center space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-2 border-teal-600 border-t-transparent"></div>
        <p className="text-gray-400">Finding great content for you...</p>
      </div>
    </div>
  );
};

export default LoadingSpinner;
