import { LANGUAGES, GENRES, CONTENT_TYPES, RELEASE_PERIODS, SORT_OPTIONS, DEFAULTS } from '../../config/constants';
import Dropdown from '../UI/Dropdown';
import { Globe, LayoutGrid, Calendar, Film, RotateCcw, ArrowUpDown } from 'lucide-react';

const FilterSection = ({
  selectedLanguage, setSelectedLanguage,
  selectedContentType, setSelectedContentType,
  selectedReleasePeriod, setSelectedReleasePeriod,
  selectedGenre, setSelectedGenre,
  selectedSortBy, setSelectedSortBy,
  onReset
}) => {
  const isDirty = selectedLanguage !== DEFAULTS.LANGUAGE ||
    selectedGenre !== DEFAULTS.GENRE ||
    selectedContentType !== DEFAULTS.CONTENT_TYPE ||
    selectedReleasePeriod !== DEFAULTS.RELEASE_PERIOD ||
    selectedSortBy !== DEFAULTS.SORT_BY;

  return (
    <div className="flex flex-wrap items-center gap-4 mb-10 py-6 border-b border-gray-800/30">
      <Dropdown
        label="Language"
        options={LANGUAGES}
        selected={selectedLanguage}
        onSelect={setSelectedLanguage}
        icon={Globe}
      />

      <Dropdown
        label="Type"
        options={CONTENT_TYPES}
        selected={selectedContentType}
        onSelect={setSelectedContentType}
        icon={LayoutGrid}
      />

      <Dropdown
        label="Genre"
        options={GENRES}
        selected={selectedGenre}
        onSelect={setSelectedGenre}
        icon={Film}
      />

      <Dropdown
        label="Release"
        options={RELEASE_PERIODS}
        selected={selectedReleasePeriod}
        onSelect={setSelectedReleasePeriod}
        icon={Calendar}
      />

      <Dropdown
        label="Sort By"
        options={SORT_OPTIONS}
        selected={selectedSortBy}
        onSelect={setSelectedSortBy}
        icon={ArrowUpDown}
      />

      {isDirty && (
        <button
          onClick={onReset}
          className="ml-auto flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-400 hover:text-teal-400 transition-colors bg-gray-800/20 hover:bg-teal-500/5 rounded-xl border border-transparent hover:border-teal-500/20"
        >
          <RotateCcw size={16} />
          Reset Filters
        </button>
      )}
    </div>
  );
};

export default FilterSection;
