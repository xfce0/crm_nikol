import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { useEffect, useState } from 'react'
import { Menu, LogOut, User, Palette, Circle } from 'lucide-react'
import { FontSelector } from '../common/FontSelector'
import { useTheme } from '../../contexts/ThemeContext'

export const Layout = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [userInfo, setUserInfo] = useState<any>(null)
  const { theme, setTheme } = useTheme()

  // Toggle between colorful and monochrome themes
  const toggleColorMode = () => {
    setTheme(theme === 'monochrome' ? 'colorful' : 'monochrome')
  }

  // Close sidebar on route change
  useEffect(() => {
    setSidebarOpen(false)
  }, [location])

  // Load user info from localStorage
  useEffect(() => {
    const authString = localStorage.getItem('auth')
    if (authString) {
      try {
        const auth = JSON.parse(authString)
        setUserInfo(auth)
      } catch (e) {
        console.error('Error parsing auth:', e)
      }
    }
  }, [])

  // Logout handler
  const handleLogout = () => {
    localStorage.removeItem('auth')
    navigate('/login')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main content - full screen */}
      <main className="w-full">
        {/* Top bar with hamburger menu */}
        <div className="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(true)}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Открыть меню"
              >
                <Menu className="w-6 h-6 text-gray-700" />
              </button>
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 via-pink-500 to-red-500 flex items-center justify-center font-bold text-white text-sm shadow-lg">
                  N
                </div>
                <h1 className="text-sm font-bold text-gray-900">
                  Nikolaev Code Studio CRM
                </h1>
              </div>
            </div>

            {/* User Info and Actions */}
            <div className="flex items-center gap-3">
              {/* Theme Toggle Button */}
              <button
                onClick={toggleColorMode}
                className="theme-toggle-btn relative p-2 rounded-lg border border-gray-200 hover:border-gray-300 bg-white hover:bg-gray-50 transition-all duration-200 group"
                title={theme === 'monochrome' ? 'Включить цветную тему' : 'Включить ЧБ тему'}
              >
                {theme === 'monochrome' ? (
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 shadow-sm" />
                    <span className="text-xs font-medium text-gray-600 hidden sm:inline">Цвет</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-gray-800 to-gray-400 shadow-sm" />
                    <span className="text-xs font-medium text-gray-600 hidden sm:inline">ЧБ</span>
                  </div>
                )}
              </button>

              {/* Font Selector */}
              <FontSelector />

              {/* User Info */}
              {userInfo && (
                <div className="flex items-center gap-3 px-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                      <User className="w-4 h-4 text-white" />
                    </div>
                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                        {userInfo.firstName || userInfo.username}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {userInfo.role === 'owner' ? 'Владелец' :
                         userInfo.role === 'timlead' ? 'Тимлид' : 'Исполнитель'}
                      </span>
                    </div>
                  </div>

                  {/* Logout Button */}
                  <button
                    onClick={handleLogout}
                    className="p-2 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors group"
                    title="Выйти"
                  >
                    <LogOut className="w-4 h-4 text-gray-600 dark:text-gray-400 group-hover:text-red-600 dark:group-hover:text-red-400" />
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Page content */}
        <Outlet />
      </main>
    </div>
  )
}
