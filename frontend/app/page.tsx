'use client';

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  Sparkles,
  Send,
  User,
  Bot,
  Loader2,
  AlertCircle,
  RotateCcw,
  BookOpen,
  Sun,
  Moon,
} from 'lucide-react';

export interface ApiResponse {
  answer: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  timestamp: string;
}

const API_ENDPOINT =
  process.env.NEXT_PUBLIC_CHAT_API_URL ||
  'https://shibir-chatbot.onrender.com/api/chat/ask';

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(true);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Initialize theme from localStorage or default to dark
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
      setIsDarkMode(false);
      document.documentElement.classList.remove('dark');
    } else {
      setIsDarkMode(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
      } else {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
      }
      return next;
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        160
      )}px`;
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    adjustTextareaHeight();
  };

  const resetTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString('bn-BD', {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    resetTextareaHeight();
    setIsLoading(true);

    try {
      const response = await axios.post<ApiResponse>(
        API_ENDPOINT,
        { message: query },
        { headers: { 'Content-Type': 'application/json' } }
      );

      const botMessage: Message = {
        id: `bot-${Date.now()}`,
        role: 'assistant',
        content: response.data.answer || 'কোনো উত্তর পাওয়া যায়নি।',
        timestamp: new Date().toLocaleTimeString('bn-BD', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('API Error:', error);
      const errorMessage: Message = {
        id: `error-${Date.now()}`,
        role: 'error',
        content: 'সংযোগে সমস্যা হয়েছে। অনুগ্রহ করে আবার চেষ্টা করুন।',
        timestamp: new Date().toLocaleTimeString('bn-BD', {
          hour: '2-digit',
          minute: '2-digit',
        }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setTimeout(() => textareaRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setInput('');
    resetTextareaHeight();
  };

  return (
    <div className="flex flex-col h-screen w-full bg-slate-50 dark:bg-[#0f1117] text-slate-800 dark:text-white transition-colors duration-200 overflow-hidden">
      {/* ── Header ── */}
      <header className="flex-shrink-0 border-b border-slate-200/80 dark:border-white/[0.06] bg-white/90 dark:bg-[#0f1117]/95 backdrop-blur-xl z-20 transition-colors duration-200">
        <div className="max-w-3xl mx-auto h-16 px-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/20">
              <BookOpen className="w-4.5 h-4.5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-[15px] tracking-tight text-slate-900 dark:text-white">
                সদস্য সহায়িকা
              </h1>
              <p className="text-[11px] text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5 font-medium">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 dark:bg-emerald-400 inline-block animate-pulse" />
                সক্রিয়
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs text-slate-500 hover:text-slate-800 dark:text-white/50 dark:hover:text-white/80 hover:bg-slate-100 dark:hover:bg-white/5 transition-all duration-200"
                title="নতুন চ্যাট"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>নতুন চ্যাট</span>
              </button>
            )}

            {/* Dark / Light Mode Toggle Button */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-500 hover:text-slate-800 dark:text-white/50 dark:hover:text-white/80 hover:bg-slate-100 dark:hover:bg-white/5 transition-all duration-200 flex items-center justify-center"
              title={isDarkMode ? 'লাইট মোড চালু করুন' : 'ডার্ক মোড চালু করুন'}
              aria-label="Toggle theme"
            >
              {isDarkMode ? (
                <Sun className="w-4 h-4 text-amber-400 hover:rotate-45 transition-transform" />
              ) : (
                <Moon className="w-4 h-4 text-slate-600 hover:-rotate-12 transition-transform" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ── Chat area ── */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-3xl mx-auto w-full px-4 py-8">
          {/* Empty state */}
          {messages.length === 0 ? (
            <div className="h-full min-h-[55vh] flex flex-col items-center justify-center text-center animate-fade-in">
              <div className="w-20 h-20 rounded-3xl bg-emerald-50 dark:bg-gradient-to-br dark:from-emerald-500/20 dark:to-teal-600/20 border border-emerald-200/80 dark:border-emerald-500/20 flex items-center justify-center mb-6 shadow-sm">
                <Sparkles className="w-9 h-9 text-emerald-600 dark:text-emerald-400" />
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-3 tracking-tight">
                সদস্য সহায়িকা
              </h2>
              <p className="text-slate-500 dark:text-white/40 text-sm sm:text-base max-w-sm leading-relaxed">
                নোট, সিলেবাস, সংবিধান ও সহায়িকা থেকে যেকোনো তথ্যের জন্য প্রশ্ন করুন।
              </p>
            </div>
          ) : (
            <div className="space-y-6 pb-4">
              {messages.map((msg) => (
                <div key={msg.id} className="animate-fade-in">
                  {/* User message */}
                  {msg.role === 'user' && (
                    <div className="flex justify-end items-end gap-2.5 pl-12">
                      <div className="flex flex-col items-end">
                        <div className="bg-emerald-600 text-white px-4 py-3 rounded-2xl rounded-br-md text-sm leading-relaxed max-w-[85%] shadow-md shadow-emerald-600/10 whitespace-pre-wrap">
                          {msg.content}
                        </div>
                        <span className="text-[10px] text-slate-400 dark:text-white/25 mt-1">
                          {msg.timestamp}
                        </span>
                      </div>
                      <div className="w-7 h-7 rounded-full bg-emerald-600 flex items-center justify-center flex-shrink-0 mb-4 shadow-sm">
                        <User className="w-3.5 h-3.5 text-white" />
                      </div>
                    </div>
                  )}

                  {/* Bot message */}
                  {msg.role === 'assistant' && (
                    <div className="flex items-end gap-2.5 pr-12">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center flex-shrink-0 mb-4 shadow-md shadow-emerald-500/20">
                        <Bot className="w-3.5 h-3.5 text-white" />
                      </div>
                      <div className="flex flex-col items-start">
                        <div className="bg-white dark:bg-[#1a1f2e] border border-slate-200 dark:border-white/[0.07] px-4 py-3.5 rounded-2xl rounded-bl-md text-sm leading-relaxed max-w-full shadow-sm dark:shadow-lg transition-colors">
                          <div className="markdown-content whitespace-pre-wrap prose-sm text-slate-800 dark:text-white/90 max-w-none">
                            <ReactMarkdown
                              components={{
                                p: ({ children }) => (
                                  <p className="mb-2 last:mb-0 leading-7 whitespace-pre-wrap">
                                    {children}
                                  </p>
                                ),
                                ul: ({ children }) => (
                                  <ul className="list-disc pl-5 my-2 space-y-1.5">
                                    {children}
                                  </ul>
                                ),
                                ol: ({ children }) => (
                                  <ol className="list-decimal pl-5 my-2 space-y-1.5">
                                    {children}
                                  </ol>
                                ),
                                li: ({ children }) => (
                                  <li className="leading-relaxed">{children}</li>
                                ),
                                strong: ({ children }) => (
                                  <strong className="font-bold text-emerald-600 dark:text-emerald-400">
                                    {children}
                                  </strong>
                                ),
                                code: ({ children }) => (
                                  <code className="bg-slate-100 dark:bg-white/5 px-1.5 py-0.5 rounded text-xs font-mono text-emerald-700 dark:text-emerald-300">
                                    {children}
                                  </code>
                                ),
                              }}
                            >
                              {msg.content}
                            </ReactMarkdown>
                          </div>
                        </div>
                        <span className="text-[10px] text-slate-400 dark:text-white/25 mt-1 ml-1">
                          {msg.timestamp}
                        </span>
                      </div>
                    </div>
                  )}

                  {/* Error message */}
                  {msg.role === 'error' && (
                    <div className="flex items-start gap-2.5">
                      <div className="w-7 h-7 rounded-full bg-red-100 dark:bg-red-500/20 flex items-center justify-center flex-shrink-0">
                        <AlertCircle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" />
                      </div>
                      <div className="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-300 px-4 py-3 rounded-2xl rounded-bl-md text-sm">
                        {msg.content}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading / Typing Indicator */}
              {isLoading && (
                <div className="flex items-end gap-2.5 animate-fade-in pr-12">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center flex-shrink-0 mb-1 shadow-md shadow-emerald-500/20">
                    <Bot className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div className="bg-white dark:bg-[#1a1f2e] border border-slate-200 dark:border-white/[0.08] px-4 py-3 rounded-2xl rounded-bl-md shadow-sm dark:shadow-lg flex items-center gap-3 transition-colors">
                    <div className="flex items-center gap-1.5 py-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-typing-dot-1" />
                      <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-typing-dot-2" />
                      <span className="w-2 h-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-typing-dot-3" />
                    </div>
                    <span className="text-xs text-slate-500 dark:text-white/50 tracking-wide font-normal">
                      সদস্য সহায়িকা লিখছে...
                    </span>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </main>

      {/* ── Input area ── */}
      <footer className="flex-shrink-0 border-t border-slate-200/80 dark:border-white/[0.06] bg-slate-50/90 dark:bg-[#0f1117]/95 backdrop-blur-xl px-4 pt-4 pb-5 z-20 transition-colors duration-200">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-white dark:bg-[#1a1f2e] border border-slate-200 dark:border-white/[0.08] rounded-2xl px-3 py-2 focus-within:border-emerald-500 dark:focus-within:border-emerald-500/50 focus-within:ring-2 focus-within:ring-emerald-500/20 transition-all duration-200 shadow-sm dark:shadow-xl">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="সদস্য সহায়িকা থেকে জানতে প্রশ্ন করুন..."
              disabled={isLoading}
              className="flex-1 max-h-40 bg-transparent resize-none outline-none border-none px-2 py-2 text-sm text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-white/25 leading-relaxed disabled:opacity-40"
            />
            <button
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || isLoading}
              className="flex-shrink-0 w-9 h-9 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-200 dark:disabled:bg-white/5 text-white disabled:text-slate-400 dark:disabled:text-white/20 flex items-center justify-center transition-all duration-200 active:scale-95 mb-0.5 shadow-md shadow-emerald-500/20"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-white" />
              ) : (
                <Send className="w-4 h-4 text-white" />
              )}
            </button>
          </div>
          <p className="text-[10px] text-slate-400 dark:text-white/20 text-center mt-2.5">
            Enter চাপুন পাঠাতে · Shift+Enter নতুন লাইনের জন্য
          </p>
        </div>
      </footer>
    </div>
  );
}
