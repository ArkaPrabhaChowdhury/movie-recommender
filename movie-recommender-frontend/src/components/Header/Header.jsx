import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, X, Bookmark, Search, ArrowLeft } from 'lucide-react';
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
  const [isSearchMobileOpen, setIsSearchMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 backdrop-blur-sm border-b" style={{ background: 'var(--color-bg-elevated)', borderColor: 'var(--color-border-primary)' }}>
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between gap-4">
          {/* Logo - Hidden on mobile when search is active */}
          <div
            className={`flex items-center space-x-2 sm:space-x-4 cursor-pointer shrink-0 transition-all ${isSearchMobileOpen ? 'hidden md:flex' : 'flex'}`}
            onClick={() => navigate('/')}
          >
            <div className="shrink-0">
              <svg
                version="1.1"
                id="Icons"
                xmlns="http://www.w3.org/2000/svg"
                xmlnsXlink="http://www.w3.org/1999/xlink"
                viewBox="0 0 32 32"
                xmlSpace="preserve"
                width="32"
                height="32"
                className="sm:w-10 sm:h-10"
                style={{ color: 'var(--color-primary-500)' }}
              >
                <circle cx="13" cy="16" r="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
                <circle cx="13" cy="16" r="12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
                <circle cx="8" cy="11" r="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
                <circle cx="8" cy="21" r="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
                <circle cx="18" cy="21" r="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
                <circle cx="18" cy="11" r="2" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
                <path d="M22.4,8.5l1.3,1.3c1.5,1.5,3.8,1.5,5.3,0l0,0c1.5-1.5,1.5-3.8,0-5.3" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" strokeMiterlimit="10" />
              </svg>
            </div>
            <h1 className="text-xl sm:text-2xl md:text-3xl font-black tracking-tighter" style={{ color: 'var(--color-primary-500)' }}>
              {UI_CONFIG.APP_NAME}
            </h1>
          </div>

          <div className={`flex items-center gap-2 sm:gap-4 flex-1 justify-end`}>
            {/* Desktop Search / Mobile Expanded Search */}
            <div className={`flex items-center gap-2 transition-all duration-300 ${isSearchMobileOpen ? 'flex-1' : 'hidden md:flex'}`}>
              {isSearchMobileOpen && (
                <button
                  onClick={() => setIsSearchMobileOpen(false)}
                  className="p-2 md:hidden text-gray-400 hover:text-white transition-colors"
                >
                  <ArrowLeft size={20} />
                </button>
              )}
              <div className="relative flex-1">
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">
                  <Search size={16} />
                </div>
                <input
                  type="text"
                  autoFocus={isSearchMobileOpen}
                  placeholder="Search globally..."
                  value={searchQuery}
                  onChange={onSearchChange}
                  className="w-full md:w-64 lg:w-96 pl-9 pr-10 py-2 rounded-xl focus:outline-none transition-all duration-200 text-sm"
                  style={{
                    background: 'var(--color-bg-secondary)',
                    border: '1px solid var(--color-border-primary)',
                    color: 'var(--color-text-primary)'
                  }}
                />
                {searchQuery && (
                  <button
                    onClick={onClearSearch}
                    className="absolute right-2 top-1/2 -translate-y-1/2 p-1 hover:text-white transition-colors text-gray-400"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>

            {/* Mobile Search Toggle */}
            {!isSearchMobileOpen && (
              <button
                onClick={() => setIsSearchMobileOpen(true)}
                className="md:hidden p-2 rounded-full hover:bg-white/5 text-gray-400 transition-colors"
              >
                <Search size={22} />
              </button>
            )}

            {/* Actions - Hidden on mobile when search is open */}
            {!isSearchMobileOpen && (
              <div className="flex items-center gap-2 sm:gap-3">
                {userId && (
                  <>
                    <button
                      onClick={() => navigate('/my-list')}
                      className="group flex items-center justify-center p-2 sm:px-4 sm:py-2 rounded-xl transition-all border border-gray-800 bg-gray-900/50 hover:bg-teal-500 hover:border-teal-500 text-gray-300 hover:text-black"
                      title="My List"
                    >
                      <Bookmark size={20} className="group-hover:scale-110 transition-transform" />
                      <span className="hidden lg:inline ml-2 font-bold text-sm">My List</span>
                    </button>

                    <button
                      onClick={() => navigate('/profile')}
                      className="group flex items-center justify-center p-2 sm:px-4 sm:py-2 rounded-xl transition-all border border-gray-800 bg-gray-900/50 hover:bg-teal-500 hover:border-teal-500 text-gray-300 hover:text-black"
                      title="Profile"
                    >
                      <User size={20} className="group-hover:scale-110 transition-transform" />
                      <span className="hidden lg:inline ml-2 font-bold text-sm">Profile</span>
                    </button>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
