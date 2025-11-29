import { useState } from 'react';
import { GENRES, STYLES } from '../../config/constants';

const GenreFilter = ({ selected, onSelect }) => {
  const [hoveredGenre, setHoveredGenre] = useState(null);

  const getButtonStyle = (genre) => {
    const genreId = genre.toLowerCase();
    const isSelected = selected === genreId;
    const isHovered = hoveredGenre === genreId;

    if (isSelected) {
      return STYLES.FILTER_BUTTON.getActiveStyle();
    } else if (isHovered) {
      return STYLES.FILTER_BUTTON.getHoverStyle();
    } else {
      return STYLES.FILTER_BUTTON.getInactiveStyle();
    }
  };

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Genres</h2>
      <div className="flex flex-wrap gap-3">
        {GENRES.map((genre) => (
          <button
            key={genre}
            onClick={() => onSelect(genre.toLowerCase())}
            onMouseEnter={() => setHoveredGenre(genre.toLowerCase())}
            onMouseLeave={() => setHoveredGenre(null)}
            className={STYLES.FILTER_BUTTON.BASE}
            style={getButtonStyle(genre)}
          >
            {genre}
          </button>
        ))}
      </div>
    </div>
  );
};

export default GenreFilter;
