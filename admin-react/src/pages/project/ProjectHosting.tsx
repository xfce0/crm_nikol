/**
 * Вкладка "Хостинг" проекта
 * Информация о хостинге, домене, FTP
 */

import { useState, useEffect } from 'react'
import { useOutletContext } from 'react-router-dom'
import { Server, Globe, Key, HardDrive, Loader2, ExternalLink, Copy, CheckCircle, DollarSign, TrendingUp, Calendar, AlertCircle } from 'lucide-react'
import axiosInstance from '../../services/api'

interface Project {
  id: number
  title: string
}

interface HostingServer {
  id: number
  project_id: number | null
  client_id: number | null
  client_name: string
  client_company: string | null
  server_name: string
  configuration: string | null
  ip_address: string | null
  cost_price: number
  client_price: number
  service_fee: number
  total_price: number
  profit_amount: number
  profit_percent: number
  start_date: string
  next_payment_date: string
  payment_period: string
  status: string
  notes: string | null
  created_at: string
  updated_at: string
}

interface HostingFinance {
  total_cost_price: number
  total_client_price: number
  total_service_fee: number
  total_revenue: number
  total_profit: number
  monthly_cost: number
  paid_payments: number
}

interface OutletContext {
  project: Project | null
}

export const ProjectHosting = () => {
  const { project } = useOutletContext<OutletContext>()
  const [servers, setServers] = useState<HostingServer[]>([])
  const [hostingFinance, setHostingFinance] = useState<HostingFinance | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedField, setCopiedField] = useState<string | null>(null)
  const [showLinkModal, setShowLinkModal] = useState(false)
  const [availableServers, setAvailableServers] = useState<HostingServer[]>([])
  const [selectedServerId, setSelectedServerId] = useState<number | null>(null)

  // Загрузка информации о хостинге
  useEffect(() => {
    if (project?.id) {
      loadHosting()
      loadHostingFinance()
    }
  }, [project?.id])

  const loadHosting = async () => {
    if (!project?.id) return

    try {
      setLoading(true)
      const response = await axiosInstance.get(`/admin/hosting/api/servers?project_id=${project.id}`)

      if (response.data.success) {
        setServers(response.data.servers || [])
      }
      setError(null)
    } catch (err: any) {
      console.error('Error loading hosting:', err)
      setError('Ошибка загрузки информации о хостинге')
    } finally {
      setLoading(false)
    }
  }

  // Загрузка финансов хостинга
  const loadHostingFinance = async () => {
    if (!project?.id) return

    try {
      const response = await axiosInstance.get(`/admin/hosting/api/project/${project.id}/hosting-costs`)

      if (response.data.success) {
        setHostingFinance(response.data.finance || null)
      }
    } catch (err: any) {
      console.error('Error loading hosting finance:', err)
    }
  }

  // Копирование в буфер обмена
  const copyToClipboard = (text: string, field: string) => {
    navigator.clipboard.writeText(text)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  // Загрузка доступных серверов
  const loadAvailableServers = async () => {
    try {
      const response = await axiosInstance.get('/admin/hosting/api/servers')
      if (response.data.success) {
        // Фильтруем серверы, которые еще не привязаны к этому проекту
        const currentServerIds = servers.map(s => s.id)
        const available = (response.data.servers || []).filter(
          (server: HostingServer) => !currentServerIds.includes(server.id)
        )
        setAvailableServers(available)
      }
    } catch (err: any) {
      console.error('Error loading available servers:', err)
      setError('Ошибка загрузки списка серверов')
    }
  }

  // Открыть модальное окно привязки
  const handleOpenLinkModal = () => {
    loadAvailableServers()
    setShowLinkModal(true)
  }

  // Привязать сервер к проекту
  const handleLinkServer = async () => {
    if (!selectedServerId || !project?.id) return

    try {
      const response = await axiosInstance.patch(`/admin/hosting/api/server/${selectedServerId}/link-project`, {
        project_id: project.id,
      })

      if (response.data.success) {
        setShowLinkModal(false)
        setSelectedServerId(null)
        setError(null)
        loadHosting()
        loadHostingFinance()
      }
    } catch (err: any) {
      console.error('Error linking server:', err)
      setError('Ошибка привязки сервера: ' + (err.response?.data?.detail || err.message))
    }
  }

  // Статусы хостинга
  const hostingStatuses: Record<string, { label: string; color: string }> = {
    active: { label: 'Активен', color: 'green' },
    suspended: { label: 'Приостановлен', color: 'yellow' },
    expired: { label: 'Истек', color: 'red' },
    pending: { label: 'Ожидает', color: 'blue' },
  }

  const getHostingStatus = (status: string) => {
    return hostingStatuses[status] || hostingStatuses.pending
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Хостинг проекта</h2>
        <button
          onClick={handleOpenLinkModal}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <Server className="w-4 h-4" />
          <span>Привязать сервер</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Сводка финансов по хостингу */}
      {hostingFinance && servers.length > 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-indigo-100 dark:from-purple-900/20 dark:to-indigo-900/20 rounded-xl p-6 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-500 rounded-lg">
                <DollarSign className="w-6 h-6 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                  Финансы хостинга
                </h3>
                <p className="text-sm text-purple-600 dark:text-purple-400">
                  {servers.length} {servers.length === 1 ? 'сервер' : servers.length < 5 ? 'сервера' : 'серверов'} привязано
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-purple-600 dark:text-purple-400">Ежемесячный расход</p>
              <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                {hostingFinance.monthly_cost.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-purple-200 dark:border-purple-700">
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Себестоимость</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {hostingFinance.total_cost_price.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Цена клиента</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {hostingFinance.total_client_price.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Комиссия</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {hostingFinance.total_service_fee.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-3">
              <p className="text-xs text-green-600 dark:text-green-400 mb-1">Прибыль</p>
              <p className={`text-lg font-bold ${hostingFinance.total_profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {hostingFinance.total_profit >= 0 ? '+' : ''}{hostingFinance.total_profit.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>

          {/* Предупреждение о следующих платежах */}
          {servers.some(s => {
            const nextPayment = new Date(s.next_payment_date)
            const now = new Date()
            const daysUntil = Math.ceil((nextPayment.getTime() - now.getTime()) / (1000 * 60 * 60 * 24))
            return daysUntil <= 7
          }) && (
            <div className="mt-4 flex items-center gap-2 text-yellow-600 dark:text-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3">
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
              <span className="text-sm">
                Есть серверы с платежом в ближайшие 7 дней
              </span>
            </div>
          )}
        </div>
      )}

      {servers.length > 0 ? (
        <div className="space-y-4">
          {servers.map((server) => {
            const statusInfo = getHostingStatus(server.status)

            return (
              <div
                key={server.id}
                className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6"
              >
                {/* Заголовок сервера */}
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-500 rounded-lg">
                      <Server className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {server.server_name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {server.configuration || 'Без описания'}
                      </p>
                    </div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-medium bg-${statusInfo.color}-100 text-${statusInfo.color}-700 dark:bg-${statusInfo.color}-900/30 dark:text-${statusInfo.color}-400`}
                  >
                    {statusInfo.label}
                  </span>
                </div>

                {/* Информация о сервере */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* IP адрес */}
                  {server.ip_address && (
                    <div className="space-y-1">
                      <p className="text-xs text-gray-500 dark:text-gray-400">IP адрес</p>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-mono text-gray-900 dark:text-white">
                          {server.ip_address}
                        </p>
                        <button
                          onClick={() => copyToClipboard(server.ip_address!, `ip-${server.id}`)}
                          className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                          title="Копировать IP"
                        >
                          {copiedField === `ip-${server.id}` ? (
                            <CheckCircle className="w-3 h-3 text-green-600" />
                          ) : (
                            <Copy className="w-3 h-3 text-gray-600" />
                          )}
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Клиент */}
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Клиент</p>
                    <p className="text-sm text-gray-900 dark:text-white">{server.client_name}</p>
                  </div>

                  {/* Следующий платеж */}
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Следующий платеж</p>
                    <p className="text-sm text-gray-900 dark:text-white">
                      {new Date(server.next_payment_date).toLocaleDateString('ru-RU')}
                    </p>
                  </div>
                </div>

                {/* Финансовая информация */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Себестоимость</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {server.cost_price.toLocaleString('ru-RU')} ₽
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Цена клиента</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {server.client_price.toLocaleString('ru-RU')} ₽
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Комиссия</p>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {server.service_fee.toLocaleString('ru-RU')} ₽
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs text-gray-500 dark:text-gray-400">Прибыль</p>
                    <p className="text-sm font-semibold text-green-600 dark:text-green-400">
                      {server.profit_amount.toLocaleString('ru-RU')} ₽ ({server.profit_percent.toFixed(1)}%)
                    </p>
                  </div>
                </div>

                {/* Заметки */}
                {server.notes && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Заметки</p>
                    <p className="text-sm text-gray-700 dark:text-gray-300">{server.notes}</p>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      ) : (
        /* Пустое состояние */
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Server className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Нет привязанных серверов
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Привяжите сервер к проекту для управления хостингом
          </p>
          <button
            onClick={handleOpenLinkModal}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Server className="w-4 h-4" />
            <span>Привязать сервер</span>
          </button>
        </div>
      )}

      {/* Модальное окно привязки сервера */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">Привязать сервер</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                Выберите сервер для привязки к проекту "{project.title}"
              </p>
            </div>

            <div className="p-6 space-y-4">
              {availableServers.length > 0 ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Доступные серверы
                  </label>
                  <select
                    value={selectedServerId || ''}
                    onChange={(e) => setSelectedServerId(Number(e.target.value))}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Выберите сервер...</option>
                    {availableServers.map((server) => (
                      <option key={server.id} value={server.id}>
                        {server.server_name} - {server.client_name} ({server.client_price.toLocaleString('ru-RU')} ₽)
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400">
                    Нет доступных серверов для привязки
                  </p>
                  <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                    Создайте новый сервер в разделе "Хостинг"
                  </p>
                </div>
              )}
            </div>

            <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setShowLinkModal(false)
                  setSelectedServerId(null)
                }}
                className="px-4 py-2 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                Отмена
              </button>
              <button
                onClick={handleLinkServer}
                disabled={!selectedServerId}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Привязать сервер
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectHosting
