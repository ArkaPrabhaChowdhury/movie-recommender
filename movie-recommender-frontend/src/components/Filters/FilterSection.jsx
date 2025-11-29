import LanguageFilter from './LanguageFilter';
import ContentTypeFilter from './ContentTypeFilter';
import ReleasePeriodFilter from './ReleasePeriodFilter';
import GenreFilter from './GenreFilter';

const FilterSection = ({ 
  selectedLanguage, setSelectedLanguage,
  selectedContentType, setSelectedContentType,
  selectedReleasePeriod, setSelectedReleasePeriod,
  selectedGenre, setSelectedGenre 
}) => {
  return (
    <div className="space-y-8 mb-12">
      <LanguageFilter 
        selected={selectedLanguage} 
        onSelect={setSelectedLanguage} 
      />
      
      <ContentTypeFilter 
        selected={selectedContentType} 
        onSelect={setSelectedContentType} 
      />
      
      <ReleasePeriodFilter 
        selected={selectedReleasePeriod} 
        onSelect={setSelectedReleasePeriod} 
      />
      
      <GenreFilter 
        selected={selectedGenre} 
        onSelect={setSelectedGenre} 
      />
    </div>
  );
};

export default FilterSection;
