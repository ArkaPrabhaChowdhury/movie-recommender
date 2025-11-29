const EmptyState = ({ message }) => {
    return (
      <div className="text-center py-20">
        <div className="mb-4 text-6xl">🎬</div>
        <p className="text-xl text-gray-400">{message}</p>
        <p className="text-gray-500 text-sm mt-2">Try adjusting your filters or search terms</p>
      </div>
    );
  };
  
  export default EmptyState;
  