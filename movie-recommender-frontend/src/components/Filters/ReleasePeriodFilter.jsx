import { useState } from 'react';
import { Calendar } from 'lucide-react';
import { RELEASE_PERIODS, STYLES } from '../../config/constants';

const ReleasePeriodFilter = ({ selected, onSelect }) => {
  const [hoveredId, setHoveredId] = useState(null);

  const getButtonStyle = (periodId) => {
    const isSelected = selected === periodId;
    const isHovered = hoveredId === periodId;

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
      <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>Release Period</h2>
      <div className="flex flex-wrap gap-3">
        {RELEASE_PERIODS.map((period) => (
          <button
            key={period.id}
            onClick={() => onSelect(period.id)}
            onMouseEnter={() => setHoveredId(period.id)}
            onMouseLeave={() => setHoveredId(null)}
            className={STYLES.FILTER_BUTTON.BASE}
            style={getButtonStyle(period.id)}
          >
            <Calendar size={16} className="inline-block mr-1" /> {period.name}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ReleasePeriodFilter;
