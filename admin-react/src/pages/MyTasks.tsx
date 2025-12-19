import { useState, useEffect, useCallback, useRef } from 'react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import myTasksApi from '../api/myTasks'
import type { MyTask, TasksByStatus, Executor, TaskComment } from '../api/myTasks'

interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info'
}

export const MyTasks = () => {
  const { currentTheme } = useTheme()
  const { isOwner } = useAuth()

  // ============= STATE =============
  const [tasksByStatus, setTasksByStatus] = useState<TasksByStatus>({
    pending: [],
    in_progress: [],
    completed: []
  })
  const [loading, setLoading] = useState(true)
  const [executors, setExecutors] = useState<Executor[]>([])
  const [selectedUser, setSelectedUser] = useState<number | undefined>(undefined)
  const [toasts, setToasts] = useState<Toast[]>([])
  const [draggedTask, setDraggedTask] = useState<MyTask | null>(null)
  const [dropZone, setDropZone] = useState<string | null>(null)

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [selectedTask, setSelectedTask] = useState<MyTask | null>(null)

  // Comment states
  const [comments, setComments] = useState<TaskComment[]>([])
  const [newComment, setNewComment] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [previewUrls, setPreviewUrls] = useState<string[]>([])
  const [isInternal, setIsInternal] = useState(false)
  const [commentLoading, setCommentLoading] = useState(false)

  // Progress state
  const [progress, setProgress] = useState(0)

  // Form states
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'normal',
    deadline: '',
    assigned_to_id: ''
  })

  // Refs for canvas and timers
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const timersRef = useRef<{ [key: number]: NodeJS.Timeout }>({})

  // ============= CONFETTI =============
  const launchConfetti = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    canvas.width = window.innerWidth
    canvas.height = window.innerHeight

    const confettiPieces: any[] = []
    const colors = ['#f44336', '#e91e63', '#9c27b0', '#673ab7', '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4', '#009688', '#4caf50', '#8bc34a', '#cddc39', '#ffeb3b', '#ffc107', '#ff9800', '#ff5722']

    for (let i = 0; i < 150; i++) {
      confettiPieces.push({
        x: Math.random() * canvas.width,
        y: -10,
        w: Math.random() * 10 + 5,
        h: Math.random() * 5 + 3,
        color: colors[Math.floor(Math.random() * colors.length)],
        speed: Math.random() * 3 + 2,
        rotation: Math.random() * 360,
        rotationSpeed: Math.random() * 10 - 5
      })
    }

    function animate() {
      ctx!.clearRect(0, 0, canvas!.width, canvas!.height)

      confettiPieces.forEach((piece, index) => {
        piece.y += piece.speed
        piece.rotation += piece.rotationSpeed

        ctx!.save()
        ctx!.translate(piece.x + piece.w / 2, piece.y + piece.h / 2)
        ctx!.rotate(piece.rotation * Math.PI / 180)
        ctx!.fillStyle = piece.color
        ctx!.fillRect(-piece.w / 2, -piece.h / 2, piece.w, piece.h)
        ctx!.restore()

        if (piece.y > canvas!.height) {
          confettiPieces.splice(index, 1)
        }
      })

      if (confettiPieces.length > 0) {
        requestAnimationFrame(animate)
      } else {
        ctx!.clearRect(0, 0, canvas!.width, canvas!.height)
      }
    }

    animate()
  }, [])

  const showSuccessMessage = useCallback(() => {
    const messages = [
      '🎉 Отличная работа!',
      '🌟 Так держать!',
      '🚀 Супер! Задача выполнена!',
      '💪 Молодец! Еще одна задача готова!',
      '✨ Превосходно!',
      '🏆 Чемпион! Задача завершена!'
    ]
    const message = messages[Math.floor(Math.random() * messages.length)]
    showToast(message, 'success')
  }, [])

  // ============= TOAST NOTIFICATIONS =============
  const showToast = useCallback((message: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Date.now()
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id))
    }, 3000)
  }, [])

  // ============= DATA LOADING =============
  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      const response = await myTasksApi.getUserTasks(selectedUser)

      if (response.success) {
        setTasksByStatus(response.tasksByStatus)
      } else {
        showToast(response.message || 'Ошибка загрузки задач', 'error')
      }
    } catch (error) {
      console.error('Error loading tasks:', error)
      showToast('Ошибка загрузки задач', 'error')
    } finally {
      setLoading(false)
    }
  }, [selectedUser, showToast])

  const loadExecutors = useCallback(async () => {
    const response = await myTasksApi.getExecutors()
    if (response.success) {
      setExecutors(response.executors)
    }
  }, [])

  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  useEffect(() => {
    loadExecutors()
  }, [loadExecutors])

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadTasks()
    }, 30000)

    return () => clearInterval(interval)
  }, [loadTasks])

  // ============= DRAG & DROP HANDLERS =============
  const handleDragStart = (e: React.DragEvent, task: MyTask) => {
    setDraggedTask(task)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragEnd = () => {
    setDraggedTask(null)
    setDropZone(null)
  }

  const handleDragEnter = (e: React.DragEvent, status: string) => {
    e.preventDefault()
    e.stopPropagation()
    setDropZone(status)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    // Проверяем что мышь действительно покинула зону drop, а не просто перешла на дочерний элемент
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    if (
      e.clientX < rect.left ||
      e.clientX >= rect.right ||
      e.clientY < rect.top ||
      e.clientY >= rect.bottom
    ) {
      setDropZone(null)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = async (newStatus: 'pending' | 'in_progress' | 'completed') => {
    if (!draggedTask) return

    setDropZone(null)
    const currentStatus = draggedTask.status

    if (currentStatus === newStatus) {
      setDraggedTask(null)
      return
    }

    // Optimistically update UI - добавляем задачу в НАЧАЛО списка (свежие задачи сверху)
    const updatedTasksByStatus = { ...tasksByStatus }
    updatedTasksByStatus[currentStatus] = updatedTasksByStatus[currentStatus].filter(t => t.id !== draggedTask.id)
    updatedTasksByStatus[newStatus] = [{ ...draggedTask, status: newStatus }, ...updatedTasksByStatus[newStatus]]
    setTasksByStatus(updatedTasksByStatus)

    // If moved to completed - confetti!
    if (newStatus === 'completed') {
      launchConfetti()
      showSuccessMessage()
    }

    // Update on server
    const response = await myTasksApi.updateTaskStatus(draggedTask.id, newStatus)

    if (response.success) {
      showToast(`Задача перемещена в "${getStatusLabel(newStatus)}"`, 'success')
    } else {
      showToast(response.message || 'Ошибка обновления задачи', 'error')
      await loadTasks()
    }

    setDraggedTask(null)
  }

  // ============= TASK ACTIONS =============
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.title) {
      showToast('Введите название задачи', 'error')
      return
    }

    const taskData = {
      title: formData.title,
      description: formData.description || undefined,
      priority: formData.priority,
      deadline: formData.deadline || undefined,
      assigned_to_id: formData.assigned_to_id ? parseInt(formData.assigned_to_id) : null,
      created_by_admin: true  // Backend determines this based on auth
    }

    const response = await myTasksApi.createTask(taskData)

    if (response.success) {
      showToast('Задача создана успешно', 'success')
      setShowCreateModal(false)
      setFormData({ title: '', description: '', priority: 'normal', deadline: '', assigned_to_id: '' })
      await loadTasks()
    } else {
      showToast(response.message || 'Ошибка создания задачи', 'error')
    }
  }

  const handleViewTask = async (taskId: number) => {
    const response = await myTasksApi.getTask(taskId)
    if (response.success && response.task) {
      setSelectedTask(response.task)
      setProgress(response.task.progress || 0)
      setShowViewModal(true)
      // Load comments
      await loadComments(taskId)
    } else {
      showToast(response.message || 'Ошибка загрузки задачи', 'error')
    }
  }

  const loadComments = async (taskId: number) => {
    try {
      const response = await myTasksApi.getComments(taskId)
      if (response.success) {
        setComments(response.comments)
      }
    } catch (error) {
      console.error('Error loading comments:', error)
    }
  }

  const handleAddComment = async () => {
    if (!selectedTask || (!newComment.trim() && selectedFiles.length === 0)) return

    try {
      setCommentLoading(true)
      const response = await myTasksApi.addComment(selectedTask.id, newComment, isInternal, selectedFiles)

      if (response.success) {
        setNewComment('')
        setSelectedFiles([])
        previewUrls.forEach(url => URL.revokeObjectURL(url))
        setPreviewUrls([])
        setIsInternal(false)
        await loadComments(selectedTask.id)
        showToast('Комментарий добавлен', 'success')
      } else {
        showToast(response.error || 'Ошибка добавления комментария', 'error')
      }
    } catch (error: any) {
      let errorMessage = 'Ошибка добавления комментария'
      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Превышено время ожидания. Попробуйте загрузить файлы меньшего размера.'
      }
      showToast(errorMessage, 'error')
    } finally {
      setCommentLoading(false)
    }
  }

  const handleProgressChange = async (newProgress: number) => {
    if (!selectedTask) return

    try {
      const response = await myTasksApi.updateProgress(selectedTask.id, newProgress)
      if (response.success) {
        setProgress(newProgress)
        showToast('Прогресс обновлен', 'success')
      }
    } catch (error) {
      console.error('Error updating progress:', error)
      showToast('Ошибка обновления прогресса', 'error')
    }
  }

  const handleFilesAdded = (newFiles: File[]) => {
    const updatedFiles = [...selectedFiles, ...newFiles]
    setSelectedFiles(updatedFiles)

    const newPreviewUrls: string[] = []
    newFiles.forEach(file => {
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file)
        newPreviewUrls.push(url)
      }
    })
    setPreviewUrls([...previewUrls, ...newPreviewUrls])
  }

  const handleRemoveFile = (index: number) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== index)
    setSelectedFiles(updatedFiles)

    if (previewUrls[index]) {
      URL.revokeObjectURL(previewUrls[index])
    }
    const updatedPreviews = previewUrls.filter((_, i) => i !== index)
    setPreviewUrls(updatedPreviews)
  }

  const handlePaste = (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
    const items = e.clipboardData?.items
    if (!items) return

    const files: File[] = []
    for (let i = 0; i < items.length; i++) {
      const item = items[i]
      if (item.type.indexOf('image') !== -1) {
        const file = item.getAsFile()
        if (file) {
          const timestamp = new Date().getTime()
          const newFile = new File([file], `screenshot-${timestamp}.png`, { type: file.type })
          files.push(newFile)
        }
      }
    }

    if (files.length > 0) {
      handleFilesAdded(files)
    }
  }

  const handleDeleteTask = async (taskId: number, task: MyTask) => {
    if (!confirm('Вы уверены, что хотите удалить эту задачу?')) {
      return
    }

    const response = await myTasksApi.deleteTask(taskId)

    if (response.success) {
      showToast('Задача удалена', 'success')
      await loadTasks()
    } else {
      showToast(response.message || 'Ошибка удаления задачи', 'error')
    }
  }

  // ============= TIMER LOGIC =============
  const formatTimer = (deadline: string): { text: string; colorClass: string; isOverdue: boolean } => {
    const now = new Date()
    const deadlineDate = new Date(deadline)
    const diff = deadlineDate.getTime() - now.getTime()

    if (diff <= 0) {
      return {
        text: 'Просрочено',
        colorClass: 'bg-red-100 text-red-800 animate-pulse',
        isOverdue: true
      }
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((diff % (1000 * 60)) / 1000)

    let timeString = ''
    if (days > 0) {
      timeString = `${days}д ${hours}ч`
    } else if (hours > 0) {
      timeString = `${hours}ч ${minutes}м`
    } else {
      timeString = `${minutes}м ${seconds}с`
    }

    let colorClass = 'bg-green-100 text-green-800'
    if (diff < 1000 * 60 * 60) {
      colorClass = 'bg-red-100 text-red-800'
    } else if (diff < 1000 * 60 * 60 * 6) {
      colorClass = 'bg-orange-100 text-orange-800'
    } else if (diff < 1000 * 60 * 60 * 24) {
      colorClass = 'bg-yellow-100 text-yellow-800'
    }

    return {
      text: timeString,
      colorClass,
      isOverdue: false
    }
  }

  // ============= HELPERS =============
  const getStatusLabel = (status: string): string => {
    const labels: Record<string, string> = {
      pending: 'Ожидает',
      in_progress: 'В работе',
      completed: 'Завершена'
    }
    return labels[status] || status
  }

  const getPriorityColor = (priority: string): string => {
    switch (priority) {
      case 'urgent': return 'border-l-4 border-red-500 bg-gradient-to-r from-red-50 to-white'
      case 'high': return 'border-l-4 border-orange-500 bg-gradient-to-r from-orange-50 to-white'
      case 'normal': return 'border-l-4 border-blue-500 bg-gradient-to-r from-blue-50 to-white'
      case 'low': return 'border-l-4 border-gray-500 bg-gradient-to-r from-gray-50 to-white'
      default: return 'border-l-4 border-gray-300 bg-white'
    }
  }

  const getPriorityLabel = (priority: string): string => {
    const labels: Record<string, string> = {
      urgent: 'Срочный',
      high: 'Высокий',
      normal: 'Обычный',
      low: 'Низкий'
    }
    return labels[priority] || priority
  }

  const getPriorityBadgeColor = (priority: string): string => {
    switch (priority) {
      case 'urgent': return 'bg-red-100 text-red-800'
      case 'high': return 'bg-orange-100 text-orange-800'
      case 'normal': return 'bg-blue-100 text-blue-800'
      case 'low': return 'bg-gray-100 text-gray-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'pending': return 'from-yellow-500 to-orange-500'
      case 'in_progress': return 'from-blue-500 to-cyan-500'
      case 'completed': return 'from-green-500 to-emerald-500'
      default: return 'from-gray-500 to-slate-500'
    }
  }

  // ============= STATISTICS =============
  const totalTasks = tasksByStatus.pending.length + tasksByStatus.in_progress.length + tasksByStatus.completed.length

  // ============= RENDER TASK CARD =============
  const TaskCard = ({ task }: { task: MyTask }) => {
    const [timer, setTimer] = useState(task.deadline ? formatTimer(task.deadline) : null)

    // Update timer every second
    useEffect(() => {
      if (!task.deadline) return

      const interval = setInterval(() => {
        setTimer(formatTimer(task.deadline!))
      }, 1000)

      return () => clearInterval(interval)
    }, [task.deadline])

    return (
      <div
        draggable
        onDragStart={(e) => handleDragStart(e, task)}
        onDragEnd={handleDragEnd}
        onClick={() => handleViewTask(task.id)}
        className={`${getPriorityColor(task.priority)} rounded-lg p-4 mb-3 cursor-pointer hover:shadow-md transition-all relative ${
          draggedTask?.id === task.id ? 'opacity-50 scale-95' : ''
        }`}
      >
        {/* Action Buttons */}
        <div className="absolute top-2 right-2 flex gap-1 opacity-100">
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleViewTask(task.id)
            }}
            className="bg-white border border-gray-300 rounded p-1 hover:bg-gray-100"
            title="Просмотр"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          </button>
          {isOwner() && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                handleDeleteTask(task.id, task)
              }}
              className="bg-white border border-gray-300 rounded p-1 hover:bg-red-100 text-red-600"
              title="Удалить"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>

        <h3 className={`font-semibold ${currentTheme.text} mb-2 pr-16`}>
          {task.priority === 'urgent' && <span className="text-red-600 mr-1">⚠️</span>}
          {task.title}
        </h3>

        {task.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">{task.description}</p>
        )}

        <div className="flex flex-wrap gap-2 mb-2">
          <span className={`px-2 py-1 rounded text-xs font-semibold ${getPriorityBadgeColor(task.priority)}`}>
            {getPriorityLabel(task.priority)}
          </span>
          {task.created_by_admin && (
            <span className="px-2 py-1 rounded text-xs font-semibold bg-gradient-to-r from-yellow-400 to-orange-400 text-white">
              От админа
            </span>
          )}
          {task.project_name && (
            <span className="px-2 py-1 rounded text-xs bg-purple-100 text-purple-800">
              {task.project_name}
            </span>
          )}
        </div>

        {timer && (
          <div className={`px-2 py-1 rounded text-xs font-semibold mb-2 inline-flex items-center gap-1 ${timer.colorClass}`}>
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {timer.text}
          </div>
        )}

        <div className="text-xs text-gray-500 flex justify-between items-center">
          <span>
            <svg className="w-3 h-3 inline mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {task.assigned_to_name || 'Не назначен'}
          </span>
          <span>{new Date(task.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    )
  }

  // ============= RENDER DROPPABLE COLUMN =============
  const DroppableColumn = ({
    status,
    tasks
  }: {
    status: 'pending' | 'in_progress' | 'completed'
    tasks: MyTask[]
  }) => (
    <div className={`flex-1 min-w-[350px] ${currentTheme.card} rounded-2xl overflow-hidden shadow-lg`}>
      {/* Column Header */}
      <div className={`bg-gradient-to-r ${getStatusColor(status)} p-5 text-white`}>
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold flex items-center gap-2">
            {status === 'pending' && (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {status === 'in_progress' && (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            )}
            {status === 'completed' && (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            )}
            {getStatusLabel(status)}
          </h2>
          <span className="bg-white/30 px-3 py-1 rounded-full text-sm font-semibold">
            {tasks.length}
          </span>
        </div>
      </div>

      {/* Column Body */}
      <div
        className={`p-4 min-h-[400px] transition-all ${
          dropZone === status ? 'bg-blue-50 ring-2 ring-blue-400 ring-inset' : ''
        }`}
        onDragEnter={(e) => handleDragEnter(e, status)}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={() => handleDrop(status)}
      >
        {tasks.length === 0 ? (
          <div className="text-center text-gray-400 py-12">
            <div className="text-6xl mb-4">
              {status === 'pending' && '📥'}
              {status === 'in_progress' && '⚙️'}
              {status === 'completed' && '🏆'}
            </div>
            <p>Нет задач</p>
          </div>
        ) : (
          tasks.map(task => (
            <TaskCard key={task.id} task={task} />
          ))
        )}
      </div>
    </div>
  )

  // ============= RENDER =============
  return (
    <div className="p-6 space-y-6">
      {/* Confetti Canvas */}
      <canvas
        ref={canvasRef}
        className="fixed top-0 left-0 w-full h-full pointer-events-none z-50"
      />

      {/* Header */}
      <div className={`${currentTheme.card} ${currentTheme.border} border rounded-lg p-6`}>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className={`text-3xl font-bold ${currentTheme.text}`}>
              Мои задачи
              {executors.length > 0 && selectedUser && (
                <select
                  value={selectedUser || 'my'}
                  onChange={(e) => setSelectedUser(e.target.value === 'my' ? undefined : parseInt(e.target.value))}
                  className={`ml-4 px-4 py-2 border ${currentTheme.border} rounded-lg ${currentTheme.input} ${currentTheme.text} text-base`}
                >
                  <option value="my">Мои задачи</option>
                  {executors.map((executor) => (
                    <option key={executor.id} value={executor.id}>
                      {executor.first_name} {executor.last_name} (@{executor.username})
                    </option>
                  ))}
                </select>
              )}
            </h1>
            <p className="text-gray-500 mt-1">Канбан-доска для управления задачами</p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Создать задачу
            </button>
            <button
              onClick={loadTasks}
              className={`px-4 py-2 ${currentTheme.primary} text-white rounded-lg hover:opacity-80 transition-opacity flex items-center gap-2`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Обновить
            </button>
          </div>
        </div>

        {/* Statistics */}
        <div className="grid grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className={`text-3xl font-bold ${currentTheme.text}`}>{totalTasks}</div>
            <div className="text-sm text-gray-500 mt-1">Всего задач</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-3xl font-bold text-yellow-600">{tasksByStatus.pending.length}</div>
            <div className="text-sm text-gray-500 mt-1">Ожидают</div>
          </div>
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-3xl font-bold text-blue-600">{tasksByStatus.in_progress.length}</div>
            <div className="text-sm text-gray-500 mt-1">В работе</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-3xl font-bold text-green-600">{tasksByStatus.completed.length}</div>
            <div className="text-sm text-gray-500 mt-1">Выполнено</div>
          </div>
        </div>
      </div>

      {/* Kanban Board */}
      {loading ? (
        <div className="text-center py-12">
          <div className={`inline-block animate-spin rounded-full h-12 w-12 border-b-2 ${currentTheme.primary}`}></div>
          <p className={`mt-4 ${currentTheme.text}`}>Загрузка задач...</p>
        </div>
      ) : (
        <div className="flex gap-6 overflow-x-auto pb-4">
          <DroppableColumn status="pending" tasks={tasksByStatus.pending} />
          <DroppableColumn status="in_progress" tasks={tasksByStatus.in_progress} />
          <DroppableColumn status="completed" tasks={tasksByStatus.completed} />
        </div>
      )}

      {/* Create Task Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`${currentTheme.card} rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto`}>
            <div className="p-6 border-b border-gray-200">
              <h2 className={`text-2xl font-bold ${currentTheme.text}`}>Создать новую задачу</h2>
            </div>
            <form onSubmit={handleCreateTask} className="p-6 space-y-4">
              <div>
                <label className={`block text-sm font-medium ${currentTheme.text} mb-2`}>
                  Название задачи *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className={`w-full px-4 py-2 border ${currentTheme.border} rounded-lg ${currentTheme.input} ${currentTheme.text}`}
                />
              </div>

              <div>
                <label className={`block text-sm font-medium ${currentTheme.text} mb-2`}>
                  Описание
                </label>
                <textarea
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  className={`w-full px-4 py-2 border ${currentTheme.border} rounded-lg ${currentTheme.input} ${currentTheme.text}`}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${currentTheme.text} mb-2`}>
                    Приоритет
                  </label>
                  <select
                    value={formData.priority}
                    onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                    className={`w-full px-4 py-2 border ${currentTheme.border} rounded-lg ${currentTheme.input} ${currentTheme.text}`}
                  >
                    <option value="low">Низкий</option>
                    <option value="normal">Обычный</option>
                    <option value="high">Высокий</option>
                    <option value="urgent">Срочный</option>
                  </select>
                </div>

                <div>
                  <label className={`block text-sm font-medium ${currentTheme.text} mb-2`}>
                    Дедлайн
                  </label>
                  <input
                    type="datetime-local"
                    value={formData.deadline}
                    onChange={(e) => setFormData({ ...formData, deadline: e.target.value })}
                    className={`w-full px-4 py-2 border ${currentTheme.border} rounded-lg ${currentTheme.input} ${currentTheme.text}`}
                  />
                </div>
              </div>

              <div>
                <label className={`block text-sm font-medium ${currentTheme.text} mb-2`}>
                  Назначить исполнителю
                </label>
                <select
                  value={formData.assigned_to_id}
                  onChange={(e) => setFormData({ ...formData, assigned_to_id: e.target.value })}
                  className={`w-full px-4 py-2 border ${currentTheme.border} rounded-lg ${currentTheme.input} ${currentTheme.text}`}
                >
                    <option value="">Выберите исполнителя</option>
                    {executors.map((executor) => (
                      <option key={executor.id} value={executor.id}>
                        {executor.first_name} {executor.last_name} (@{executor.username})
                      </option>
                    ))}
                  </select>
                </div>

              <div className="flex justify-end gap-2 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false)
                    setFormData({ title: '', description: '', priority: 'normal', deadline: '', assigned_to_id: '' })
                  }}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Создать
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Task Modal */}
      {showViewModal && selectedTask && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className={`${currentTheme.card} rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col`}>
            {/* Header */}
            <div className="p-6 border-b border-gray-200 flex-shrink-0">
              <div className="flex items-start justify-between gap-4">
                <h2 className={`text-2xl font-bold ${currentTheme.text}`}>{selectedTask.title}</h2>
                <button
                  onClick={() => {
                    setShowViewModal(false)
                    setSelectedTask(null)
                    setComments([])
                    setNewComment('')
                    setSelectedFiles([])
                    setPreviewUrls([])
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            </div>

            {/* Body - Scrollable */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {/* Description */}
              {selectedTask.description && (
                <div className="bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 rounded-xl p-4 border border-blue-200">
                  <h4 className="font-bold text-gray-900 mb-2">Описание</h4>
                  <p className="text-gray-800 text-sm whitespace-pre-wrap">{selectedTask.description}</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Progress Card */}
                <div className="bg-gradient-to-br from-indigo-50 to-purple-50 rounded-xl p-4 border border-indigo-200">
                  <div className="flex items-center gap-2 mb-3">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-indigo-700">
                      <path d="M16 7h6v6"></path>
                      <path d="m22 7-8.5 8.5-5-5L2 17"></path>
                    </svg>
                    <h4 className="font-bold text-gray-900">Прогресс</h4>
                  </div>
                  <div className="text-center mb-3">
                    <span className={`text-3xl font-bold ${
                      progress < 25 ? 'text-red-600' :
                      progress < 50 ? 'text-orange-600' :
                      progress < 75 ? 'text-yellow-600' :
                      progress < 100 ? 'text-blue-600' :
                      'text-green-600'
                    }`}>{progress}%</span>
                  </div>
                  <div className="relative w-full">
                    <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className="h-full transition-all duration-500 ease-out"
                        style={{
                          width: `${progress}%`,
                          background: progress < 25
                            ? 'linear-gradient(90deg, #ef4444, #f87171)'
                            : progress < 50
                            ? 'linear-gradient(90deg, #f97316, #fb923c)'
                            : progress < 75
                            ? 'linear-gradient(90deg, #eab308, #fde047)'
                            : progress < 100
                            ? 'linear-gradient(90deg, #3b82f6, #60a5fa)'
                            : 'linear-gradient(90deg, #22c55e, #4ade80)',
                        }}
                      />
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={progress}
                      onChange={(e) => handleProgressChange(parseInt(e.target.value))}
                      className="absolute top-0 left-0 w-full h-3 appearance-none cursor-pointer bg-transparent opacity-0"
                      disabled={selectedTask.status === 'completed'}
                    />
                  </div>
                  <p className="text-xs text-gray-600 mt-1 text-center">Перетащите для изменения</p>
                </div>

                {/* Status & Priority */}
                <div className="space-y-4">
                  <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 border border-blue-200">
                    <strong className="text-gray-900 block mb-2">Статус:</strong>
                    <span className={`px-3 py-1 rounded-full text-sm inline-block ${
                      selectedTask.status === 'completed' ? 'bg-green-100 text-green-800' :
                      selectedTask.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {getStatusLabel(selectedTask.status)}
                    </span>
                  </div>
                  <div className="bg-gradient-to-br from-orange-50 to-red-50 rounded-xl p-4 border border-orange-200">
                    <strong className="text-gray-900 block mb-2">Приоритет:</strong>
                    <span className={`px-3 py-1 rounded-full text-sm inline-block ${getPriorityBadgeColor(selectedTask.priority)}`}>
                      {getPriorityLabel(selectedTask.priority)}
                    </span>
                  </div>
                </div>

                {/* Executor */}
                <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl p-4 border border-green-200">
                  <strong className="text-gray-900 block mb-2">Исполнитель:</strong>
                  <p className="text-gray-800">{selectedTask.assigned_to_name || 'Не назначен'}</p>
                </div>

                {/* Creator */}
                <div className="bg-gradient-to-br from-slate-50 to-gray-100 rounded-xl p-4 border border-slate-200">
                  <strong className="text-gray-900 block mb-2">Создатель:</strong>
                  <p className="text-gray-800">
                    {selectedTask.created_by_name}
                    {selectedTask.created_by_admin && (
                      <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs">Админ</span>
                    )}
                  </p>
                </div>

                {/* Deadline */}
                {selectedTask.deadline && (
                  <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl p-4 border border-purple-200">
                    <strong className="text-gray-900 block mb-2">Дедлайн:</strong>
                    <p className="text-gray-800">{new Date(selectedTask.deadline).toLocaleString()}</p>
                  </div>
                )}

                {/* Created */}
                <div className="bg-gradient-to-br from-yellow-50 to-amber-50 rounded-xl p-4 border border-yellow-200">
                  <strong className="text-gray-900 block mb-2">Создано:</strong>
                  <p className="text-gray-800">{new Date(selectedTask.created_at).toLocaleString()}</p>
                </div>
              </div>

              {/* Comments Section */}
              <div className="bg-gradient-to-br from-slate-50 to-gray-100 rounded-xl p-4 border border-slate-200">
                <h4 className="font-bold text-gray-900 mb-3">Комментарии ({comments.length})</h4>

                {/* Comments List */}
                <div className="space-y-2 mb-4 max-h-80 overflow-y-auto">
                  {comments.map((comment) => (
                    <div
                      key={comment.id}
                      className={`p-3 rounded-lg ${
                        comment.is_internal ? 'bg-yellow-50 border border-yellow-200' : 'bg-white border border-gray-200'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-xs text-gray-900">
                          {comment.author?.first_name || comment.author?.username}
                        </span>
                        <span className="text-xs text-gray-500">{new Date(comment.created_at).toLocaleString()}</span>
                        {comment.is_internal && (
                          <span className="text-xs bg-yellow-200 text-yellow-800 px-1.5 py-0.5 rounded font-semibold">
                            Внутренний
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-700 whitespace-pre-wrap mb-2">{comment.comment}</p>
                      {comment.attachments && comment.attachments.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {comment.attachments.map((file, idx) => {
                            const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(file.original_filename)
                            const fileUrl = `/${file.path || file.filename}`

                            if (isImage) {
                              return (
                                <a
                                  key={idx}
                                  href={fileUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="group relative block"
                                >
                                  <img
                                    src={fileUrl}
                                    alt={file.original_filename}
                                    className="h-32 w-auto rounded-lg border-2 border-gray-200 hover:border-blue-500 transition-all cursor-pointer object-cover shadow-sm hover:shadow-md"
                                    loading="lazy"
                                  />
                                  <p className="text-xs text-gray-500 mt-1 max-w-[150px] truncate">
                                    {file.original_filename}
                                  </p>
                                </a>
                              )
                            } else {
                              return (
                                <a
                                  key={idx}
                                  href={fileUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-800 bg-blue-50 px-3 py-2 rounded-lg hover:bg-blue-100 transition-colors"
                                >
                                  📎 {file.original_filename}
                                </a>
                              )
                            }
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                  {comments.length === 0 && (
                    <p className="text-center text-gray-400 py-4 text-sm">Комментариев пока нет</p>
                  )}
                </div>

                {/* Add Comment */}
                <div className="space-y-3 bg-white p-3 rounded-lg border border-gray-200">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    onPaste={handlePaste}
                    placeholder="Написать комментарий... (Ctrl+V для вставки скриншотов)"
                    rows={2}
                    className="w-full px-3 py-2 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-sm"
                  />

                  {/* Preview изображений */}
                  {previewUrls.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {previewUrls.map((url, index) => (
                        <div key={index} className="relative group">
                          <img
                            src={url}
                            alt={`Preview ${index + 1}`}
                            className="w-24 h-24 object-cover rounded-lg border-2 border-gray-200"
                          />
                          <button
                            onClick={() => handleRemoveFile(index)}
                            className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Список файлов */}
                  {selectedFiles.filter(f => !f.type.startsWith('image/')).length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {selectedFiles.map((file, index) =>
                        !file.type.startsWith('image/') && (
                          <div key={index} className="flex items-center gap-2 px-3 py-2 bg-gray-100 rounded-lg text-sm">
                            <span className="text-gray-700">{file.name}</span>
                            <button
                              onClick={() => handleRemoveFile(index)}
                              className="text-red-500 hover:text-red-700"
                            >
                              ✕
                            </button>
                          </div>
                        )
                      )}
                    </div>
                  )}

                  <div className="flex items-center gap-2">
                    <label className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 hover:bg-gray-200 rounded-lg cursor-pointer transition-colors">
                      <span className="text-xs font-medium">📎 Прикрепить</span>
                      <input
                        type="file"
                        multiple
                        accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt"
                        onChange={(e) => handleFilesAdded(Array.from(e.target.files || []))}
                        className="hidden"
                      />
                    </label>
                    {selectedFiles.length > 0 && (
                      <span className="text-xs text-gray-600">
                        {selectedFiles.length} {selectedFiles.length === 1 ? 'файл' : 'файлов'}
                      </span>
                    )}
                    <div className="flex-1" />
                    <label className="flex items-center gap-1.5 text-xs">
                      <input
                        type="checkbox"
                        checked={isInternal}
                        onChange={(e) => setIsInternal(e.target.checked)}
                        className="rounded"
                      />
                      Внутренний
                    </label>
                    <button
                      onClick={handleAddComment}
                      disabled={commentLoading || (!newComment.trim() && selectedFiles.length === 0)}
                      className="px-4 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                    >
                      Отправить
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-gray-200 flex justify-end flex-shrink-0">
              <button
                onClick={() => {
                  setShowViewModal(false)
                  setSelectedTask(null)
                  setComments([])
                  setNewComment('')
                  setSelectedFiles([])
                  setPreviewUrls([])
                }}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
              >
                Закрыть
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast Notifications */}
      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            className={`px-6 py-3 rounded-lg shadow-lg text-white ${
              toast.type === 'success' ? 'bg-green-600' :
              toast.type === 'error' ? 'bg-red-600' :
              'bg-blue-600'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </div>
  )
}
