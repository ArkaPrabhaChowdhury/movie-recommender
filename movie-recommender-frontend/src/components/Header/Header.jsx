import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, X } from 'lucide-react';
import { UI_CONFIG, API_CONFIG } from '../../config/constants';

const Header = ({
  searchQuery,
  onSearchChange,
  onClearSearch,
  isGlobalSearch,
  globalSearchResults,
  userId
}) => {
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-50 backdrop-blur-sm border-b" style={{ background: 'var(--color-bg-elevated)', borderColor: 'var(--color-border-primary)' }}>
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 cursor-pointer" onClick={() => navigate('/')}>
            <svg
              version="1.1"
              id="Icons"
              xmlns="http://www.w3.org/2000/svg"
              xmlnsXlink="http://www.w3.org/1999/xlink"
              viewBox="0 0 32 32"
              xmlSpace="preserve"
              width="40"
              height="40"
              style={{ color: 'var(--color-primary-500)' }}
            >
              <circle
                className="st0"
                cx="13"
                cy="16"
                r="2"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
              <circle
                className="st0"
                cx="13"
                cy="16"
                r="12"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
              <circle
                className="st0"
                cx="8"
                cy="11"
                r="2"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
              <circle
                className="st0"
                cx="8"
                cy="21"
                r="2"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
              <circle
                className="st0"
                cx="18"
                cy="21"
                r="2"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
              <circle
                className="st0"
                cx="18"
                cy="11"
                r="2"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
              <path
                className="st0"
                d="M22.4,8.5l1.3,1.3c1.5,1.5,3.8,1.5,5.3,0l0,0c1.5-1.5,1.5-3.8,0-5.3"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeMiterlimit="10"
              />
            </svg>
            <h1 className="text-3xl font-bold" style={{ color: 'var(--color-primary-500)' }}>{UI_CONFIG.APP_NAME}</h1>
          </div>
          <div className="flex items-center space-x-4">
            <div className="relative">
              <input
                type="text"
                placeholder="Search movies & shows globally..."
                value={searchQuery}
                onChange={onSearchChange}
                className="w-80 px-4 py-2 pr-10 rounded-md focus:outline-none transition-all duration-200"
                style={{
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border-primary)',
                  color: 'var(--color-text-primary)'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = 'var(--color-primary-500)';
                  e.target.style.boxShadow = '0 0 0 1px var(--color-primary-500)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'var(--color-border-primary)';
                  e.target.style.boxShadow = 'none';
                }}
              />
              {searchQuery && (
                <button
                  onClick={onClearSearch}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 transition-colors"
                  style={{ color: 'var(--color-text-tertiary)' }}
                  onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-text-primary)'}
                  onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-tertiary)'}
                >
                  <X size={18} />
                </button>
              )}
            </div>

            {/* Profile Button */}
            {userId && (
              <button
                onClick={() => navigate('/profile')}
                className="flex items-center gap-2 px-4 py-2 rounded-md transition-all duration-200"
                style={{
                  background: 'var(--color-bg-secondary)',
                  border: '1px solid var(--color-border-primary)',
                  color: 'var(--color-text-primary)'
                }}
                onMouseEnter={(e) => {
                  e.target.style.background = 'var(--color-primary-500)';
                  e.target.style.borderColor = 'var(--color-primary-500)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.background = 'var(--color-bg-secondary)';
                  e.target.style.borderColor = 'var(--color-border-primary)';
                }}
              >
                <User size={20} />
                <span className="font-medium">Profile</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
