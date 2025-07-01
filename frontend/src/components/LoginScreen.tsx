import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import AnimatedCircles from './AnimatedCircles'

interface LoginScreenProps {
  onLogin: (email: string) => void
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState('gabriel.ferreira@teddydigital.io')
  const [token, setToken] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [needsToken, setNeedsToken] = useState(false)

  const handleLogin = async () => {
    if (!email) return
    
    setIsLoading(true)
    
    try {
      if (!needsToken) {
        setNeedsToken(true)
        setIsLoading(false)
        return
      }
      
      if (token) {
        onLogin(email)
      }
    } catch (error) {
      console.error('Login error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const requestToken = () => {
    alert('Token solicitado! Verifique seu email.')
  }

  return (
    <div className="min-h-screen relative overflow-hidden bg-gradient-to-br from-orange-50 to-orange-100">
      <AnimatedCircles />
      
      <div className="relative z-10 flex items-center justify-center min-h-screen p-4">
        <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <div className="flex items-center mb-6">
            <ArrowLeft className="w-5 h-5 text-gray-600 mr-2 cursor-pointer" />
            <span className="text-gray-600">Voltar</span>
          </div>
          
          <div className="text-center mb-8">
            <div className="inline-block bg-orange-500 text-white px-4 py-2 rounded-lg font-bold text-lg mb-4">
              SAM <span className="text-xs border border-white rounded px-1">PM</span>
            </div>
            <h1 className="text-2xl font-bold text-orange-500 mb-2">Fazer Login</h1>
            <p className="text-gray-600">
              Digite seu email e o token recebido por email
            </p>
          </div>

          <div className="space-y-4">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              placeholder="Seu email"
            />
            
            {needsToken && (
              <input
                type="text"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                placeholder="Token de acesso"
              />
            )}

            <button
              onClick={handleLogin}
              disabled={isLoading || !email}
              className="w-full bg-orange-500 text-white py-3 rounded-lg font-semibold hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Carregando...' : needsToken ? 'Entrar' : 'Continuar'}
            </button>

            {needsToken && (
              <button
                onClick={requestToken}
                className="w-full text-gray-600 py-2 text-sm hover:text-orange-500 transition-colors"
              >
                Preciso de um token
              </button>
            )}
          </div>
        </div>
      </div>
      
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-center">
        <p className="text-gray-500 text-sm">Desenvolvido pela Teddy Digital</p>
        <div className="w-2 h-2 bg-orange-300 rounded-full mx-auto mt-2"></div>
      </div>
    </div>
  )
}
