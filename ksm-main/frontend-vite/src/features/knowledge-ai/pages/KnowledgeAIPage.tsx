/**
 * Knowledge AI Page
 * Halaman untuk chat dengan AI dan search knowledge base dengan Tailwind CSS
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  useGetStatsQuery,
  useChatMutation,
  useSearchMutation,
} from '../store';
import { useSweetAlert } from '@/shared/hooks';
import { Button, Input } from '@/shared/components/ui';
import { LoadingSpinner } from '@/shared/components/feedback';
import type { ChatMessage, SearchResult } from '../types';

const KnowledgeAIPage: React.FC = () => {
  const sweetAlert = useSweetAlert();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [activeTab, setActiveTab] = useState<'chat' | 'search'>('chat');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: stats } = useGetStatsQuery();
  const [chat, { isLoading: chatting }] = useChatMutation();
  const [search, { isLoading: searching }] = useSearchMutation();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || chatting) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      message: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const currentInput = inputMessage;
    setInputMessage('');
    
    try {
      const response = await chat({
        message: currentInput,
        conversation_history: messages.map(m => ({
          role: m.type,
          content: m.message,
        })),
        context: {},
      }).unwrap();

      const aiMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        message: response.success ? response.message : 'Maaf, terjadi kesalahan saat memproses pesan Anda.',
        timestamp: new Date(),
        confidence: response.confidence,
        sourceFiles: response.source_files,
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        message: error?.message || 'Maaf, terjadi kesalahan koneksi. Silakan coba lagi.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() || searching) return;

    try {
      const response = await search({ query: searchQuery }).unwrap();
      if (response.success) {
        setSearchResults(response.data.results);
      } else {
        setSearchResults([]);
        await sweetAlert.showError('Gagal', 'Gagal melakukan pencarian');
      }
    } catch (error: any) {
      setSearchResults([]);
      await sweetAlert.showError('Gagal', error?.message || 'Gagal melakukan pencarian');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (activeTab === 'chat') {
        handleSendMessage();
      } else {
        handleSearch();
      }
    }
  };

  const clearChat = () => {
    setMessages([]);
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('id-ID', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="p-4 md:p-6 lg:p-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <h1 className="text-2xl md:text-3xl font-bold text-gray-800">🤖 Knowledge AI Assistant</h1>
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'chat'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              💬 Chat
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeTab === 'search'
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              🔍 Search
            </button>
          </div>
        </div>
      </div>

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Total Files</div>
            <div className="text-2xl font-bold text-gray-800">{stats.total_files}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Categories</div>
            <div className="text-2xl font-bold text-blue-600">{stats.total_categories}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">High Priority</div>
            <div className="text-2xl font-bold text-red-600">{stats.high_priority_files}</div>
          </div>
          <div className="bg-white rounded-lg shadow-md p-4">
            <div className="text-sm text-gray-600 mb-1">Recent Files</div>
            <div className="text-2xl font-bold text-green-600">{stats.recent_files}</div>
          </div>
        </div>
      )}

      {/* Chat Tab */}
      {activeTab === 'chat' && (
        <div className="bg-white rounded-lg shadow-md overflow-hidden flex flex-col" style={{ height: '600px' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                <p className="text-lg mb-2">👋 Selamat datang di Knowledge AI Assistant!</p>
                <p className="text-sm">Mulai percakapan dengan mengetik pesan di bawah.</p>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.type === 'user'
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  <div className="text-sm whitespace-pre-wrap">{message.message}</div>
                  <div className={`text-xs mt-1 ${
                    message.type === 'user' ? 'text-primary-100' : 'text-gray-500'
                  }`}>
                    {formatTime(message.timestamp)}
                  </div>
                  {message.type === 'ai' && message.confidence && (
                    <div className="text-xs mt-1 text-gray-500">
                      Confidence: {message.confidence}
                    </div>
                  )}
                  {message.type === 'ai' && message.sourceFiles && message.sourceFiles.length > 0 && (
                    <div className="text-xs mt-2 pt-2 border-t border-gray-300">
                      <div className="font-semibold mb-1">Sources:</div>
                      <div className="space-y-1">
                        {message.sourceFiles.map((file, idx) => (
                          <div key={idx} className="text-primary-600">• {file}</div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatting && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <LoadingSpinner size="sm" />
                    <span className="text-sm text-gray-600">AI sedang mengetik...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex gap-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ketik pesan Anda..."
                rows={2}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
              />
              <div className="flex flex-col gap-2">
                <Button
                  variant="primary"
                  onClick={handleSendMessage}
                  disabled={!inputMessage.trim() || chatting}
                >
                  {chatting ? '⏳' : '📤'}
                </Button>
                {messages.length > 0 && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={clearChat}
                  >
                    🗑️
                  </Button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Search Tab */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          {/* Search Form */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Search Query</label>
                <div className="flex gap-2">
                  <Input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Masukkan kata kunci untuk mencari..."
                    className="flex-1"
                  />
                  <Button
                    variant="primary"
                    onClick={handleSearch}
                    disabled={!searchQuery.trim() || searching}
                  >
                    {searching ? '⏳ Searching...' : '🔍 Search'}
                  </Button>
                </div>
              </div>
            </div>
          </div>

          {/* Search Results */}
          {searching && (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <LoadingSpinner />
              <p className="text-gray-600 mt-4">Mencari...</p>
            </div>
          )}

          {!searching && searchResults.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Search Results ({searchResults.length})
              </h3>
              <div className="space-y-4">
                {searchResults.map((result) => (
                  <div key={result.file_id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h4 className="font-semibold text-gray-900">{result.filename}</h4>
                        <div className="flex gap-2 mt-1">
                          <span className="px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                            {result.category}
                          </span>
                          <span className={`px-2 py-1 rounded-full text-xs ${
                            result.priority_level === 'high'
                              ? 'bg-red-100 text-red-800'
                              : result.priority_level === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-green-100 text-green-800'
                          }`}>
                            {result.priority_level}
                          </span>
                        </div>
                      </div>
                      <div className="text-sm font-semibold text-primary-600">
                        {(result.relevance_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">{result.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!searching && searchQuery && searchResults.length === 0 && (
            <div className="bg-white rounded-lg shadow-md p-8 text-center">
              <p className="text-gray-600">Tidak ada hasil ditemukan untuk "{searchQuery}"</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default KnowledgeAIPage;

