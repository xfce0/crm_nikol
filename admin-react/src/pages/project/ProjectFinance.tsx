/**
 * Вкладка "Финансы" проекта
 * Платежи, бюджет, отчет по прибыли
 */

import { useState, useEffect } from 'react'
import { useOutletContext } from 'react-router-dom'
import { DollarSign, Plus, TrendingUp, TrendingDown, Calendar, Loader2, CheckCircle, Clock, X, Server, HardDrive } from 'lucide-react'
import axiosInstance from '../../services/api'

interface Project {
  id: number
  title: string
  budget?: number
  estimated_cost?: number
  executor_cost?: number
  client_paid_total?: number
  executor_paid_total?: number
}

interface Payment {
  id: number
  type: string
  amount: number
  status: string
  due_date?: string
  paid_at?: string
  description?: string
  created_at: string
}

interface PaymentSummary {
  total_amount: number
  paid_amount: number
  pending_amount: number
}

interface HostingCosts {
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

export const ProjectFinance = () => {
  const { project } = useOutletContext<OutletContext>()
  const [payments, setPayments] = useState<Payment[]>([])
  const [summary, setSummary] = useState<PaymentSummary>({
    total_amount: 0,
    paid_amount: 0,
    pending_amount: 0,
  })
  const [hostingCosts, setHostingCosts] = useState<HostingCosts | null>(null)
  const [serversCount, setServersCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createForm, setCreateForm] = useState({
    type: 'PREPAYMENT',
    amount: '',
    due_date: '',
    description: '',
  })
  const [creating, setCreating] = useState(false)

  // Загрузка платежей и расходов хостинга
  useEffect(() => {
    if (project?.id) {
      loadPayments()
      loadHostingCosts()
    }
  }, [project?.id])

  const loadPayments = async () => {
    if (!project?.id) return

    try {
      setLoading(true)
      const response = await axiosInstance.get(`/admin/api/projects/${project.id}/payments`)

      if (response.data.success) {
        setPayments(response.data.payments || [])
        setSummary(response.data.summary || { total_amount: 0, paid_amount: 0, pending_amount: 0 })
      }
      setError(null)
    } catch (err: any) {
      console.error('Error loading payments:', err)
      setError('Ошибка загрузки платежей')
    } finally {
      setLoading(false)
    }
  }

  // Загрузка расходов на хостинг
  const loadHostingCosts = async () => {
    if (!project?.id) return

    try {
      const response = await axiosInstance.get(`/admin/hosting/api/project/${project.id}/hosting-costs`)

      if (response.data.success) {
        setHostingCosts(response.data.finance || null)
        setServersCount(response.data.servers_count || 0)
      }
    } catch (err: any) {
      console.error('Error loading hosting costs:', err)
      // Не показываем ошибку - хостинг может отсутствовать
    }
  }

  // Создание платежа
  const handleCreatePayment = async () => {
    if (!project?.id) return

    if (!createForm.amount || parseFloat(createForm.amount) <= 0) {
      setError('Укажите корректную сумму платежа')
      return
    }

    try {
      setCreating(true)
      const response = await axiosInstance.post(`/admin/api/projects/${project.id}/payments`, {
        type: createForm.type,
        amount: parseFloat(createForm.amount),
        due_date: createForm.due_date || null,
        description: createForm.description || null,
      })

      if (response.data.success) {
        setShowCreateModal(false)
        setCreateForm({
          type: 'PREPAYMENT',
          amount: '',
          due_date: '',
          description: '',
        })
        loadPayments()
      }
    } catch (err: any) {
      console.error('Error creating payment:', err)
      setError('Ошибка создания платежа: ' + (err.response?.data?.message || err.message))
    } finally {
      setCreating(false)
    }
  }

  // Отметить платеж как оплаченный
  const handleMarkAsPaid = async (paymentId: number) => {
    try {
      const today = new Date().toISOString().split('T')[0]
      const response = await axiosInstance.patch(`/admin/api/payments/${paymentId}`, {
        status: 'PAID',
        paid_at: today,
      })

      if (response.data.success) {
        loadPayments()
      }
    } catch (err: any) {
      console.error('Error updating payment:', err)
      setError('Ошибка обновления платежа')
    }
  }

  // Типы платежей
  const paymentTypes: Record<string, string> = {
    PREPAYMENT: 'Предоплата',
    MILESTONE: 'Этап',
    FINAL: 'Финальный',
    ADDITIONAL: 'Дополнительный',
  }

  // Статусы платежей с цветами
  const paymentStatuses: Record<string, { label: string; color: string; icon: any }> = {
    PLANNED: { label: 'Запланирован', color: 'gray', icon: Clock },
    PENDING: { label: 'Ожидает', color: 'yellow', icon: Clock },
    PAID: { label: 'Оплачен', color: 'green', icon: CheckCircle },
    OVERDUE: { label: 'Просрочен', color: 'red', icon: TrendingDown },
  }

  const getPaymentStatusInfo = (status: string) => {
    return paymentStatuses[status] || paymentStatuses.PLANNED
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
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Финансы проекта</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Добавить платеж</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Карточки финансов */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-blue-500 rounded-lg">
              <DollarSign className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-blue-600 dark:text-blue-400">Общий бюджет</p>
              <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                {summary.total_amount.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg p-6 border border-green-200 dark:border-green-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-green-500 rounded-lg">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-green-600 dark:text-green-400">Оплачено</p>
              <p className="text-2xl font-bold text-green-900 dark:text-green-100">
                {summary.paid_amount.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>
          <div className="w-full bg-green-200 dark:bg-green-900/50 rounded-full h-2">
            <div
              className="bg-green-500 h-2 rounded-full transition-all"
              style={{
                width: `${summary.total_amount > 0 ? (summary.paid_amount / summary.total_amount) * 100 : 0}%`,
              }}
            ></div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-lg p-6 border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-3 mb-3">
            <div className="p-3 bg-red-500 rounded-lg">
              <TrendingDown className="w-6 h-6 text-white" />
            </div>
            <div>
              <p className="text-sm text-red-600 dark:text-red-400">Ожидается</p>
              <p className="text-2xl font-bold text-red-900 dark:text-red-100">
                {summary.pending_amount.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>
          <div className="w-full bg-red-200 dark:bg-red-900/50 rounded-full h-2">
            <div
              className="bg-red-500 h-2 rounded-full transition-all"
              style={{
                width: `${summary.total_amount > 0 ? (summary.pending_amount / summary.total_amount) * 100 : 0}%`,
              }}
            ></div>
          </div>
        </div>
      </div>

      {/* Карточка расходов на хостинг */}
      {hostingCosts && serversCount > 0 && (
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg p-6 border border-purple-200 dark:border-purple-800">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-500 rounded-lg">
                <Server className="w-6 h-6 text-white" />
              </div>
              <div>
                <p className="text-sm text-purple-600 dark:text-purple-400">Расходы на хостинг</p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                  {hostingCosts.monthly_cost.toLocaleString('ru-RU')} ₽/мес
                </p>
              </div>
            </div>
            <span className="px-3 py-1 bg-purple-200 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 rounded-full text-sm font-medium">
              {serversCount} {serversCount === 1 ? 'сервер' : serversCount < 5 ? 'сервера' : 'серверов'}
            </span>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-purple-200 dark:border-purple-700">
            <div>
              <p className="text-xs text-purple-600 dark:text-purple-400">Себестоимость</p>
              <p className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                {hostingCosts.total_cost_price.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <div>
              <p className="text-xs text-purple-600 dark:text-purple-400">Цена клиента</p>
              <p className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                {hostingCosts.total_client_price.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <div>
              <p className="text-xs text-purple-600 dark:text-purple-400">Комиссия</p>
              <p className="text-lg font-semibold text-purple-900 dark:text-purple-100">
                {hostingCosts.total_service_fee.toLocaleString('ru-RU')} ₽
              </p>
            </div>
            <div>
              <p className="text-xs text-green-600 dark:text-green-400">Прибыль</p>
              <p className={`text-lg font-bold ${hostingCosts.total_profit >= 0 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {hostingCosts.total_profit >= 0 ? '+' : ''}{hostingCosts.total_profit.toLocaleString('ru-RU')} ₽
              </p>
            </div>
          </div>
        </div>
      )}

      {/* История платежей */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">История платежей</h3>
        </div>

        {payments.length > 0 ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {payments.map((payment) => {
              const statusInfo = getPaymentStatusInfo(payment.status)
              const StatusIcon = statusInfo.icon

              return (
                <div key={payment.id} className="px-6 py-4 hover:bg-gray-50 dark:hover:bg-gray-900/30 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4 flex-1">
                      <div className={`p-2 bg-${statusInfo.color}-100 dark:bg-${statusInfo.color}-900/20 rounded-lg`}>
                        <StatusIcon className={`w-5 h-5 text-${statusInfo.color}-600 dark:text-${statusInfo.color}-400`} />
                      </div>

                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                            {paymentTypes[payment.type] || payment.type}
                          </h4>
                          <span
                            className={`px-2 py-0.5 rounded-full text-xs font-medium bg-${statusInfo.color}-100 text-${statusInfo.color}-700 dark:bg-${statusInfo.color}-900/30 dark:text-${statusInfo.color}-400`}
                          >
                            {statusInfo.label}
                          </span>
                        </div>

                        {payment.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">{payment.description}</p>
                        )}

                        <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                          {payment.due_date && (
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              <span>Срок: {new Date(payment.due_date).toLocaleDateString('ru-RU')}</span>
                            </div>
                          )}
                          {payment.paid_at && (
                            <div className="flex items-center gap-1">
                              <CheckCircle className="w-3 h-3" />
                              <span>Оплачено: {new Date(payment.paid_at).toLocaleDateString('ru-RU')}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="text-right flex items-center gap-3">
                      <div>
                        <p className="text-lg font-bold text-gray-900 dark:text-white">
                          {payment.amount.toLocaleString('ru-RU')} ₽
                        </p>
                      </div>
                      {payment.status !== 'PAID' && (
                        <button
                          onClick={() => handleMarkAsPaid(payment.id)}
                          className="px-3 py-1.5 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors whitespace-nowrap"
                        >
                          Оплачен
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <p className="text-gray-500 dark:text-gray-400 text-sm">
              Платежи для этого проекта еще не созданы
            </p>
          </div>
        )}
      </div>

      {/* Модальное окно создания платежа */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Создать платеж</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Тип платежа */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Тип платежа
                </label>
                <select
                  value={createForm.type}
                  onChange={(e) => setCreateForm({ ...createForm, type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                >
                  <option value="PREPAYMENT">Предоплата</option>
                  <option value="MILESTONE">Этап</option>
                  <option value="FINAL">Финальный</option>
                  <option value="ADDITIONAL">Дополнительный</option>
                </select>
              </div>

              {/* Сумма */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Сумма (₽) *
                </label>
                <input
                  type="number"
                  value={createForm.amount}
                  onChange={(e) => setCreateForm({ ...createForm, amount: e.target.value })}
                  placeholder="Введите сумму"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              {/* Срок оплаты */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Срок оплаты
                </label>
                <input
                  type="date"
                  value={createForm.due_date}
                  onChange={(e) => setCreateForm({ ...createForm, due_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>

              {/* Описание */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Описание
                </label>
                <textarea
                  value={createForm.description}
                  onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                  placeholder="Дополнительная информация о платеже"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent resize-none"
                />
              </div>
            </div>

            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={handleCreatePayment}
                disabled={creating}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Создание...</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    <span>Создать платеж</span>
                  </>
                )}
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                disabled={creating}
                className="px-4 py-2.5 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors disabled:opacity-50"
              >
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectFinance
