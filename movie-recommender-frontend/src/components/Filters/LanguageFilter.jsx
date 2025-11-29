import { useState } from 'react';
import { LANGUAGES, STYLES } from '../../config/constants';

const LanguageFilter = ({ selected, onSelect }) => {
  const [hoveredId, setHoveredId] = useState(null);

  const getButtonStyle = (languageId) => {
    const isSelected = selected === languageId;
    const isHovered = hoveredId === languageId;

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
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Languages</h2>
      <div className="flex flex-wrap gap-3">
        {LANGUAGES.map((language) => (
          <button
            key={language.id}
            onClick={() => onSelect(language.id)}
            onMouseEnter={() => setHoveredId(language.id)}
            onMouseLeave={() => setHoveredId(null)}
            className={STYLES.FILTER_BUTTON.BASE}
            style={getButtonStyle(language.id)}
          >
            {language.name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default LanguageFilter;
