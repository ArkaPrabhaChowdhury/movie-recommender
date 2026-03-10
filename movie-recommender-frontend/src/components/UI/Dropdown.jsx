import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

const Dropdown = ({ label, options, selected, onSelect, icon: Icon }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Find the label for the selected option
  const getDisplayLabel = () => {
    const option = options.find(opt => {
      const id = typeof opt === 'string' ? opt.toLowerCase() : opt.id;
      return id === selected;
    });
    return typeof option === 'string' ? option : (option?.name || selected);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-gray-800/40 border border-gray-700 hover:border-teal-500/50 hover:bg-gray-800/60 transition-all text-sm font-medium ${isOpen ? 'border-teal-500 ring-4 ring-teal-500/10 bg-gray-800/80' : ''
          }`}
      >
        {Icon && <Icon size={16} className="text-teal-400" />}
        <span className="text-gray-400 font-normal">{label}:</span>
        <span className="text-gray-100">{getDisplayLabel()}</span>
        <ChevronDown size={14} className={`text-gray-500 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-2 w-64 bg-[#161b22] border border-gray-700/50 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] overflow-hidden backdrop-blur-xl">
          <div className="p-1.5 max-h-[400px] overflow-y-auto custom-scrollbar">
            {options.map((option) => {
              const id = typeof option === 'string' ? option.toLowerCase() : option.id;
              const name = typeof option === 'string' ? option : option.name;
              const isSelected = id === selected;

              return (
                <button
                  key={id}
                  onClick={() => {
                    onSelect(id);
                    setIsOpen(false);
                  }}
                  className={`w-full text-left px-4 py-3 rounded-xl text-sm transition-all flex items-center justify-between mb-0.5 last:mb-0 ${isSelected
                    ? 'bg-teal-500/10 text-teal-400 font-semibold'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                    }`}
                >
                  {name}
                  {isSelected && (
                    <div className="flex items-center justify-center w-5 h-5 rounded-full bg-teal-500/20">
                      <div className="w-2 h-2 rounded-full bg-teal-500 shadow-[0_0_8px_rgba(20,184,166,0.8)]" />
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default Dropdown;
