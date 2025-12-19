/**
 * Вкладка "Документы" проекта
 * Договоры, акты, счета
 */

import { useState, useEffect } from 'react'
import { useOutletContext } from 'react-router-dom'
import { FileText, Upload, Download, Trash2, Eye, Plus, Loader2, X } from 'lucide-react'
import axiosInstance from '../../services/api'

interface Project {
  id: number
  title: string
}

interface Document {
  id: number
  type: string
  name: string
  number?: string
  file_path?: string
  file_size?: number
  file_type?: string
  status: string
  date?: string
  signed_at?: string
  description?: string
  created_at: string
}

interface OutletContext {
  project: Project | null
}

export const ProjectDocuments = () => {
  const { project } = useOutletContext<OutletContext>()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [createForm, setCreateForm] = useState({
    type: 'contract',
    name: '',
    number: '',
    description: '',
  })
  const [creating, setCreating] = useState(false)

  // Загрузка документов
  useEffect(() => {
    if (project?.id) {
      loadDocuments()
    }
  }, [project?.id])

  const loadDocuments = async () => {
    if (!project?.id) return

    try {
      setLoading(true)
      const response = await axiosInstance.get(`/admin/api/projects/${project.id}/documents`)

      if (response.data.success) {
        setDocuments(response.data.documents || [])
      }
      setError(null)
    } catch (err: any) {
      console.error('Error loading documents:', err)
      setError('Ошибка загрузки документов')
    } finally {
      setLoading(false)
    }
  }

  // Типы документов
  const documentTypes: Record<string, { label: string; color: string }> = {
    contract: { label: 'Договор', color: 'blue' },
    act: { label: 'Акт', color: 'green' },
    invoice: { label: 'Счет', color: 'purple' },
    specification: { label: 'Спецификация', color: 'orange' },
    other: { label: 'Другое', color: 'gray' },
  }

  // Статусы документов
  const documentStatuses: Record<string, { label: string; color: string }> = {
    draft: { label: 'Черновик', color: 'gray' },
    sent: { label: 'Отправлен', color: 'blue' },
    signed: { label: 'Подписан', color: 'green' },
    rejected: { label: 'Отклонен', color: 'red' },
  }

  const getDocumentTypeColor = (type: string) => {
    const typeInfo = documentTypes[type] || documentTypes.other
    return typeInfo.color
  }

  const getDocumentStatusColor = (status: string) => {
    const statusInfo = documentStatuses[status] || documentStatuses.draft
    return statusInfo.color
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(2)} МБ`
  }

  // Создание документа
  const handleCreateDocument = async () => {
    if (!project?.id) return

    if (!createForm.name.trim()) {
      setError('Укажите название документа')
      return
    }

    try {
      setCreating(true)
      const response = await axiosInstance.post(`/admin/api/projects/${project.id}/documents`, {
        type: createForm.type,
        name: createForm.name.trim(),
        number: createForm.number.trim() || null,
        description: createForm.description.trim() || null,
      })

      if (response.data.success) {
        setShowCreateModal(false)
        setCreateForm({
          type: 'contract',
          name: '',
          number: '',
          description: '',
        })
        loadDocuments()
        setError(null)
      }
    } catch (err: any) {
      console.error('Error creating document:', err)
      setError('Ошибка создания документа: ' + (err.response?.data?.message || err.message))
    } finally {
      setCreating(false)
    }
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
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">Документы проекта</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>Добавить документ</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Список документов */}
      {documents.length > 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Тип
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Название
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Номер
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Статус
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Дата
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Размер
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                    Действия
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {documents.map((doc) => (
                  <tr
                    key={doc.id}
                    className="hover:bg-gray-50 dark:hover:bg-gray-900/30 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${getDocumentTypeColor(
                          doc.type
                        )}-100 text-${getDocumentTypeColor(
                          doc.type
                        )}-700 dark:bg-${getDocumentTypeColor(doc.type)}-900/30 dark:text-${getDocumentTypeColor(
                          doc.type
                        )}-400`}
                      >
                        {documentTypes[doc.type]?.label || doc.type}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {doc.name}
                        </span>
                      </div>
                      {doc.description && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{doc.description}</p>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {doc.number || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-${getDocumentStatusColor(
                          doc.status
                        )}-100 text-${getDocumentStatusColor(
                          doc.status
                        )}-700 dark:bg-${getDocumentStatusColor(
                          doc.status
                        )}-900/30 dark:text-${getDocumentStatusColor(doc.status)}-400`}
                      >
                        {documentStatuses[doc.status]?.label || doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                      {doc.date
                        ? new Date(doc.date).toLocaleDateString('ru-RU')
                        : new Date(doc.created_at).toLocaleDateString('ru-RU')}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                      {formatFileSize(doc.file_size)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                      <div className="flex items-center justify-end gap-2">
                        {doc.file_path && (
                          <button
                            className="p-1.5 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors"
                            title="Скачать"
                          >
                            <Download className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          className="p-1.5 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors"
                          title="Просмотр"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          className="p-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors"
                          title="Удалить"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Документы не найдены</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-4">Загрузите первый документ проекта</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
          >
            <Upload className="w-4 h-4" />
            <span>Загрузить документ</span>
          </button>
        </div>
      )}

      {/* Модалка создания документа */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl max-w-lg w-full p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">Добавить документ</h3>
              <button
                onClick={() => setShowCreateModal(false)}
                className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {error && (
              <div className="mb-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>
              </div>
            )}

            <div className="space-y-4">
              {/* Тип документа */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Тип документа *
                </label>
                <select
                  value={createForm.type}
                  onChange={(e) => setCreateForm({ ...createForm, type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                >
                  <option value="contract">Договор</option>
                  <option value="act">Акт</option>
                  <option value="invoice">Счет</option>
                  <option value="specification">Спецификация</option>
                  <option value="other">Другое</option>
                </select>
              </div>

              {/* Название */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Название документа *
                </label>
                <input
                  type="text"
                  value={createForm.name}
                  onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                  placeholder="Договор №123 от 01.12.2025"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
                />
              </div>

              {/* Номер документа */}
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Номер документа
                </label>
                <input
                  type="text"
                  value={createForm.number}
                  onChange={(e) => setCreateForm({ ...createForm, number: e.target.value })}
                  placeholder="№123"
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent"
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
                  placeholder="Дополнительная информация о документе"
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-amber-500 focus:border-transparent resize-none"
                />
              </div>

              {/* Информация о файлах */}
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  <strong>Примечание:</strong> Функционал загрузки файлов будет добавлен в следующей версии.
                  Пока можно создавать документы с метаданными.
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 mt-6">
              <button
                onClick={handleCreateDocument}
                disabled={creating}
                className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Создание...</span>
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4" />
                    <span>Создать документ</span>
                  </>
                )}
              </button>
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setError(null)
                }}
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

export default ProjectDocuments
