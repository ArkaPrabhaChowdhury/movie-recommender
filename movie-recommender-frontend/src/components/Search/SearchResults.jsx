const SearchResults = ({ query, resultCount, onBackToBrowse }) => {
    return (
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-white mb-2">
          🔍 Search Results for "{query}"
        </h2>
        <p className="text-gray-400">
          Found {resultCount} OTT-available titles matching your search
        </p>
        <button
          onClick={onBackToBrowse}
          className="mt-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-md text-sm text-gray-300 transition-colors"
        >
          ← Back to Browse
        </button>
      </div>
    );
  };
  
  export default SearchResults;
  