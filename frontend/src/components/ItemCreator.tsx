import { useState } from 'react'
import { Save, AlertTriangle, CheckCircle, X } from 'lucide-react'

interface ItemCreatorProps {
  userEmail: string
}

interface ConflictItem {
  item_key: string
  summary: string
  created_at: string
  conflict_reason: string
}

export default function ItemCreator({ userEmail }: ItemCreatorProps) {
  const [itemType, setItemType] = useState('história')
  const [summary, setSummary] = useState('')
  const [description, setDescription] = useState('')
  const [epicLink, setEpicLink] = useState('')
  const [storyLink, setStoryLink] = useState('')
  const [parentKey, setParentKey] = useState('')
  const [labels, setLabels] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conflicts, setConflicts] = useState<ConflictItem[]>([])
  const [showConflicts, setShowConflicts] = useState(false)
  const [successMessage, setSuccessMessage] = useState('')

  const itemTypes = [
    { value: 'épico', label: 'Épico' },
    { value: 'história', label: 'História' },
    { value: 'task', label: 'Task' },
    { value: 'subtask', label: 'Subtask' },
    { value: 'bug', label: 'Bug' }
  ]

  const checkConflicts = async () => {
    if (!summary || !description) return

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/check-conflicts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          summary,
          description,
          item_type: itemType,
          user_context: userEmail
        })
      })

      const data = await response.json()
      
      if (data.has_conflicts) {
        setConflicts(data.conflicts)
        setShowConflicts(true)
      } else {
        setConflicts([])
        setShowConflicts(false)
      }
    } catch (error) {
      console.error('Error checking conflicts:', error)
    }
  }

  const createItem = async () => {
    if (!summary || !description) return

    setIsLoading(true)
    setSuccessMessage('')

    try {
      const requestBody = {
        item_type: itemType,
        summary,
        description,
        epic_link: epicLink || undefined,
        story_link: storyLink || undefined,
        parent_key: parentKey || undefined,
        labels: labels ? labels.split(',').map(l => l.trim()) : [],
        user_context: userEmail
      }

      const response = await fetch(`${import.meta.env.VITE_API_URL}/api/create-item`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      const data = await response.json()

      if (data.success) {
        setSuccessMessage(data.message)
        setSummary('')
        setDescription('')
        setEpicLink('')
        setStoryLink('')
        setParentKey('')
        setLabels('')
        setConflicts([])
        setShowConflicts(false)
      } else if (data.conflicts) {
        setConflicts(data.conflicts)
        setShowConflicts(true)
      }
    } catch (error) {
      console.error('Error creating item:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const renderLinkField = () => {
    switch (itemType) {
      case 'história':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Epic Link *
            </label>
            <input
              type="text"
              value={epicLink}
              onChange={(e) => setEpicLink(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="Ex: PROJ-123"
              required
            />
          </div>
        )
      case 'task':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Story Link *
            </label>
            <input
              type="text"
              value={storyLink}
              onChange={(e) => setStoryLink(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="Ex: PROJ-124"
              required
            />
          </div>
        )
      case 'subtask':
      case 'bug':
        return (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Parent Key {itemType === 'subtask' ? '*' : ''}
            </label>
            <input
              type="text"
              value={parentKey}
              onChange={(e) => setParentKey(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="Ex: PROJ-125"
              required={itemType === 'subtask'}
            />
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="flex-1 p-6 bg-white overflow-y-auto">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">Criar Novo Item</h1>

        {successMessage && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center">
            <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
            <span className="text-green-700">{successMessage}</span>
          </div>
        )}

        {showConflicts && conflicts.length > 0 && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <AlertTriangle className="w-5 h-5 text-yellow-500 mr-2" />
                <span className="font-medium text-yellow-800">Conflitos Detectados</span>
              </div>
              <button
                onClick={() => setShowConflicts(false)}
                className="text-yellow-500 hover:text-yellow-700"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="space-y-2">
              {conflicts.map((conflict, index) => (
                <div key={index} className="text-sm text-yellow-700">
                  <strong>{conflict.item_key}</strong>: {conflict.summary}
                  <br />
                  <span className="text-yellow-600">{conflict.conflict_reason}</span>
                </div>
              ))}
            </div>
            <p className="text-sm text-yellow-600 mt-3">
              Revise os conflitos antes de prosseguir ou continue mesmo assim.
            </p>
          </div>
        )}

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de Item *
            </label>
            <select
              value={itemType}
              onChange={(e) => setItemType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
            >
              {itemTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Resumo *
            </label>
            <input
              type="text"
              value={summary}
              onChange={(e) => setSummary(e.target.value)}
              onBlur={checkConflicts}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="Título do item"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descrição *
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onBlur={checkConflicts}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              rows={6}
              placeholder="Descrição detalhada do item"
              required
            />
          </div>

          {renderLinkField()}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Labels
            </label>
            <input
              type="text"
              value={labels}
              onChange={(e) => setLabels(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="label1, label2, label3"
            />
            <p className="text-sm text-gray-500 mt-1">
              Separe múltiplas labels com vírgulas
            </p>
          </div>

          <div className="flex space-x-4">
            <button
              onClick={checkConflicts}
              disabled={!summary || !description || isLoading}
              className="flex-1 bg-gray-500 text-white py-3 px-6 rounded-lg font-semibold hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Verificar Conflitos
            </button>
            
            <button
              onClick={createItem}
              disabled={!summary || !description || isLoading}
              className="flex-1 bg-orange-500 text-white py-3 px-6 rounded-lg font-semibold hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <>
                  <Save className="w-5 h-5 mr-2" />
                  Criar Item
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
