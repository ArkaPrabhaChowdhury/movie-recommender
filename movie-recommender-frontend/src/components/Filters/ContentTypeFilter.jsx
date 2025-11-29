import { useState } from 'react';
import { CONTENT_TYPES, STYLES } from '../../config/constants';

const ContentTypeFilter = ({ selected, onSelect }) => {
  const [hoveredId, setHoveredId] = useState(null);

  const getButtonStyle = (typeId) => {
    const isSelected = selected === typeId;
    const isHovered = hoveredId === typeId;

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
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Content Type</h2>
      <div className="flex flex-wrap gap-3">
        {CONTENT_TYPES.map((type) => (
          <button
            key={type.id}
            onClick={() => onSelect(type.id)}
            onMouseEnter={() => setHoveredId(type.id)}
            onMouseLeave={() => setHoveredId(null)}
            className={STYLES.FILTER_BUTTON.BASE}
            style={getButtonStyle(type.id)}
          >
            {type.name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ContentTypeFilter;
