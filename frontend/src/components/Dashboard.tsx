import { useState } from 'react'
import { Plus, Search, MessageSquare, Settings, LogOut, Sparkles, Zap, Layout } from 'lucide-react'
import ChatInterface from './ChatInterface'
import ItemCreator from './ItemCreator'

interface DashboardProps {
  userEmail: string
  onLogout: () => void
}

export default function Dashboard({ userEmail, onLogout }: DashboardProps) {
  const [activeView, setActiveView] = useState<'chat' | 'create' | 'landing'>('landing')
  const [conversations, setConversations] = useState([
    'Implementação de nova funcionalidade',
    'Correção de bugs críticos',
    'Melhoria na experiência do usuário'
  ])

  const quickActions = [
    {
      title: 'Criar um épico',
      description: 'Defina grandes iniciativas e objetivos',
      icon: Layout,
      action: () => setActiveView('create')
    },
    {
      title: 'Nova história',
      description: 'Detalhe funcionalidades específicas',
      icon: MessageSquare,
      action: () => setActiveView('create')
    },
    {
      title: 'Reportar bug',
      description: 'Identifique e documente problemas',
      icon: Settings,
      action: () => setActiveView('create')
    },
    {
      title: 'Conversar com agentes',
      description: 'Discuta requisitos com nossa equipe IA',
      icon: Sparkles,
      action: () => setActiveView('chat')
    }
  ]

  const renderLanding = () => (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <div className="text-center mb-12">
        <div className="inline-block bg-orange-500 text-white px-6 py-3 rounded-xl font-bold text-2xl mb-6">
          SAM <span className="text-sm border border-white rounded px-2">PM</span>
        </div>
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Seu assistente de <br />
          <span className="text-orange-500">gestão de produtos</span>
        </h1>
        <p className="text-gray-600 text-lg max-w-2xl">
          Potencialize sua produtividade com o poder da IA. Crie, gerencie e otimize 
          seus projetos com tecnologia de ponta.
        </p>
        <button
          onClick={() => setActiveView('chat')}
          className="mt-8 bg-orange-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors inline-flex items-center"
        >
          Começar agora <span className="ml-2">→</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl w-full">
        {quickActions.map((action, index) => (
          <div
            key={index}
            onClick={action.action}
            className="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow cursor-pointer border border-gray-100"
          >
            <div className="bg-orange-100 w-12 h-12 rounded-lg flex items-center justify-center mb-4">
              <action.icon className="w-6 h-6 text-orange-500" />
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">{action.title}</h3>
            <p className="text-gray-600 text-sm">{action.description}</p>
          </div>
        ))}
      </div>

      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl w-full">
        <div className="text-center">
          <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-orange-500" />
          </div>
          <h3 className="font-semibold text-gray-800 mb-2">IA Avançada</h3>
          <p className="text-gray-600 text-sm">
            Tecnologia GPT-4 para conversas naturais e respostas precisas
          </p>
        </div>
        <div className="text-center">
          <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Zap className="w-8 h-8 text-orange-500" />
          </div>
          <h3 className="font-semibold text-gray-800 mb-2">Respostas Rápidas</h3>
          <p className="text-gray-600 text-sm">
            Obtenha respostas instantâneas para suas perguntas e desafios
          </p>
        </div>
        <div className="text-center">
          <div className="bg-orange-100 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
            <Layout className="w-8 h-8 text-orange-500" />
          </div>
          <h3 className="font-semibold text-gray-800 mb-2">Interface Intuitiva</h3>
          <p className="text-gray-600 text-sm">
            Design moderno e fácil de usar para máxima produtividade
          </p>
        </div>
      </div>
    </div>
  )

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="w-64 bg-orange-500 text-white flex flex-col">
        <div className="p-4">
          <button
            onClick={() => setActiveView('chat')}
            className="w-full bg-orange-600 hover:bg-orange-700 px-4 py-2 rounded-lg flex items-center transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Novo chat
          </button>
        </div>

        <div className="px-4 mb-4">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-orange-300" />
            <input
              type="text"
              placeholder="Buscar em chats"
              className="w-full bg-orange-400 placeholder-orange-200 text-white px-10 py-2 rounded-lg focus:outline-none focus:bg-orange-300"
            />
          </div>
        </div>

        <div className="flex-1 px-4">
          <h3 className="text-sm font-semibold mb-3 text-orange-200">CONVERSAS RECENTES</h3>
          <div className="space-y-2">
            {conversations.map((conv, index) => (
              <div
                key={index}
                className="p-3 rounded-lg hover:bg-orange-400 cursor-pointer transition-colors text-sm"
              >
                {conv}
              </div>
            ))}
          </div>
        </div>

        <div className="p-4 border-t border-orange-400">
          <div className="flex items-center space-x-3 mb-4">
            <div className="w-8 h-8 bg-orange-300 rounded-full flex items-center justify-center">
              <span className="text-orange-700 font-semibold text-sm">
                {userEmail.charAt(0).toUpperCase()}
              </span>
            </div>
            <span className="text-sm truncate">{userEmail}</span>
          </div>
          
          <div className="space-y-2">
            <button
              onClick={() => setActiveView('landing')}
              className="w-full flex items-center px-3 py-2 rounded-lg hover:bg-orange-400 transition-colors text-sm"
            >
              <Layout className="w-4 h-4 mr-3" />
              Dashboard
            </button>
            <button
              onClick={() => setActiveView('create')}
              className="w-full flex items-center px-3 py-2 rounded-lg hover:bg-orange-400 transition-colors text-sm"
            >
              <Plus className="w-4 h-4 mr-3" />
              Criar Item
            </button>
            <button
              onClick={onLogout}
              className="w-full flex items-center px-3 py-2 rounded-lg hover:bg-orange-400 transition-colors text-sm"
            >
              <LogOut className="w-4 h-4 mr-3" />
              Sair
            </button>
          </div>
        </div>
      </div>

      {activeView === 'landing' && renderLanding()}
      {activeView === 'chat' && <ChatInterface userEmail={userEmail} />}
      {activeView === 'create' && <ItemCreator userEmail={userEmail} />}
    </div>
  )
}
