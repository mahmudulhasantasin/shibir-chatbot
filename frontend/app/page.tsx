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
  HelpCircle,
  RotateCcw,
  Sun,
  Moon,
} from 'lucide-react';

/* ==========================================================================
   TypeScript Interfaces
   ========================================================================== */

export interface ApiResponse {
  answer: string;
  suggested_questions?: string[];
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'error';
  content: string;
  suggestedQuestions?: string[];
  timestamp: string;
}

/* ==========================================================================
   API Endpoint Configuration
   - Uses NEXT_PUBLIC_CHAT_API_URL if configured in .env.local
   - Defaults to live Render backend: https://shibir-chatbot.onrender.com/api/chat/ask
   - For local development: http://127.0.0.1:8000/api/chat/ask
   ========================================================================== */
const API_ENDPOINT =
  process.env.NEXT_PUBLIC_CHAT_API_URL ||
  'https://shibir-chatbot.onrender.com/api/chat/ask';

/* ==========================================================================
   Starter Prompts for Empty State
   ========================================================================== */
const STARTER_PROMPTS = [
  'সংগঠনের মূল উদ্দেশ্য ও লক্ষ্য কী?',
  'সিলেবাস ও পাঠ্যতালিকা সম্পর্কে বিস্তারিত বলুন',
  'দাওয়াত ও প্রচার বিভাগের কার্যক্রম কী?',
  'সদস্য পদের দায়িত্ব ও কর্তব্যসমূহ কী কী?',
];

/* ==========================================================================
   Main Page Component
   ========================================================================== */

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDarkMode, setIsDarkMode] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Auto-scroll to bottom whenever messages or loading state change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Dynamically adjust textarea height up to 160px
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

  // Reset textarea height back to standard single row
  const resetTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  // Toggle dark mode class on <html>
  const toggleTheme = () => {
    setIsDarkMode((prev) => {
      const next = !prev;
      if (next) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      return next;
    });
  };

  // Send message function (accepts custom text for clicking suggested question pills)
  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || input).trim();
    if (!query || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    // Optimistically update message list
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
        id: `bot-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        role: 'assistant',
        content: response.data.answer || 'No response returned.',
        suggestedQuestions: response.data.suggested_questions || [],
        timestamp: new Date().toLocaleTimeString([], {
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
        content:
          'Sorry, something went wrong while communicating with the assistant. Please check your backend connection or try again.',
        timestamp: new Date().toLocaleTimeString([], {
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

  // Keyboard navigation: Enter sends, Shift+Enter creates a new line
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Clear chat (no history / no local storage persistence)
  const handleClearChat = () => {
    if (confirm('Are you sure you want to clear this conversation?')) {
      setMessages([]);
      setInput('');
      resetTextareaHeight();
    }
  };

  return (
    <div
      className="flex flex-col h-screen w-full overflow-hidden transition-colors duration-200"
      style={{
        backgroundColor: 'var(--bg-primary, #f8fafc)',
        color: 'var(--text-primary, #0f172a)',
      }}
    >
      {/* ===================================================================
          1. Header (Fixed Top)
          =================================================================== */}
      <header
        className="w-full h-16 border-b flex-shrink-0 z-20 backdrop-blur-md transition-colors"
        style={{
          backgroundColor: 'var(--bg-card, #ffffff)',
          borderColor: 'rgba(var(--text-primary-rgb, 15, 23, 42), 0.08)',
        }}
      >
        <div className="max-w-4xl mx-auto h-full px-4 flex items-center justify-between">
          {/* Centered Brand Title & Icon */}
          <div className="flex items-center gap-2.5">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center shadow-sm"
              style={{
                backgroundColor: 'var(--accent-solid, #4f46e5)',
                color: 'var(--accent-contrast, #ffffff)',
              }}
            >
              <Sparkles className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <h1 className="font-semibold text-base sm:text-lg leading-tight tracking-tight">
                Shibir PDF Assistant
              </h1>
              <p
                className="text-xs flex items-center gap-1.5"
                style={{ color: 'var(--text-muted, #64748b)' }}
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping inline-block" />
                Live AI Document Knowledge Base
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-1.5 sm:gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleClearChat}
                title="Clear Chat"
                className="p-2 rounded-xl text-xs sm:text-sm font-medium transition-colors hover:bg-black/5 dark:hover:bg-white/10 flex items-center gap-1"
                style={{ color: 'var(--text-muted, #64748b)' }}
              >
                <RotateCcw className="w-4 h-4" />
                <span className="hidden sm:inline">Reset</span>
              </button>
            )}

            <button
              onClick={toggleTheme}
              title="Toggle theme"
              className="p-2 rounded-xl transition-colors hover:bg-black/5 dark:hover:bg-white/10"
              style={{ color: 'var(--text-muted, #64748b)' }}
            >
              {isDarkMode ? (
                <Sun className="w-4 h-4 text-amber-400" />
              ) : (
                <Moon className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </header>

      {/* ===================================================================
          2. Chat Area (Scrollable Middle)
          =================================================================== */}
      <main className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto w-full flex flex-col justify-start">
          {/* Empty State */}
          {messages.length === 0 ? (
            <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4 animate-fade-in">
              <div
                className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl flex items-center justify-center mb-6 shadow-md border"
                style={{
                  backgroundColor: 'var(--bg-card, #ffffff)',
                  borderColor: 'rgba(var(--text-primary-rgb, 15, 23, 42), 0.1)',
                }}
              >
                <Bot
                  className="w-8 h-8 sm:w-10 sm:h-10"
                  style={{ color: 'var(--accent-solid, #4f46e5)' }}
                />
              </div>

              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight mb-2">
                How can I help you today?
              </h2>
              <p
                className="max-w-md text-sm sm:text-base mb-8 leading-relaxed"
                style={{ color: 'var(--text-muted, #64748b)' }}
              >
                Ask any question related to documents, guidelines, study materials, or constitution.
              </p>

              {/* Starter Question Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                {STARTER_PROMPTS.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(prompt)}
                    className="group text-left p-3.5 rounded-2xl border text-sm font-medium transition-all duration-200 hover:shadow-md hover:scale-[1.01] active:scale-[0.99] flex items-start gap-2.5"
                    style={{
                      backgroundColor: 'var(--bg-card, #ffffff)',
                      borderColor:
                        'rgba(var(--text-primary-rgb, 15, 23, 42), 0.08)',
                    }}
                  >
                    <HelpCircle className="w-4 h-4 mt-0.5 text-indigo-500 flex-shrink-0 group-hover:rotate-12 transition-transform" />
                    <span className="line-clamp-2">{prompt}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            /* Message List */
            <div className="space-y-6">
              {messages.map((msg) => (
                <div key={msg.id} className="animate-fade-in">
                  {/* User Message Bubble (Right-aligned) */}
                  {msg.role === 'user' && (
                    <div className="flex justify-end items-end gap-2.5 pl-10">
                      <div className="flex flex-col items-end max-w-[85%] sm:max-w-[75%]">
                        <div
                          className="px-4 py-3 rounded-2xl rounded-tr-none shadow-sm text-sm sm:text-base leading-relaxed break-words"
                          style={{
                            backgroundColor: 'var(--accent-solid, #4f46e5)',
                            color: 'var(--accent-contrast, #ffffff)',
                          }}
                        >
                          {msg.content}
                        </div>
                        <span
                          className="text-[11px] mt-1 mr-1"
                          style={{ color: 'var(--text-muted, #64748b)' }}
                        >
                          {msg.timestamp}
                        </span>
                      </div>

                      <div
                        className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 shadow-sm"
                        style={{
                          backgroundColor: 'var(--accent-solid, #4f46e5)',
                          color: 'var(--accent-contrast, #ffffff)',
                        }}
                      >
                        <User className="w-4 h-4" />
                      </div>
                    </div>
                  )}

                  {/* Bot Message Bubble (Left-aligned) */}
                  {msg.role === 'assistant' && (
                    <div className="flex flex-col items-start pr-4 sm:pr-10">
                      <div className="flex items-start gap-2.5 w-full">
                        <div
                          className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border mt-1"
                          style={{
                            backgroundColor: 'var(--bg-card, #ffffff)',
                            borderColor:
                              'rgba(var(--text-primary-rgb, 15, 23, 42), 0.1)',
                            color: 'var(--accent-solid, #4f46e5)',
                          }}
                        >
                          <Bot className="w-4 h-4" />
                        </div>

                        <div className="flex flex-col items-start max-w-[88%] sm:max-w-[82%]">
                          <div
                            className="px-4 py-3.5 rounded-2xl rounded-tl-none shadow-sm border text-sm sm:text-base leading-relaxed break-words w-full"
                            style={{
                              backgroundColor: 'var(--bg-card, #ffffff)',
                              color: 'var(--text-primary, #0f172a)',
                              borderColor:
                                'rgba(var(--text-primary-rgb, 15, 23, 42), 0.08)',
                            }}
                          >
                            {/* React Markdown for formatting */}
                            <div className="markdown-content">
                              <ReactMarkdown
                                components={{
                                  p: ({ children }) => (
                                    <p className="mb-2.5 last:mb-0 leading-relaxed">
                                      {children}
                                    </p>
                                  ),
                                  ul: ({ children }) => (
                                    <ul className="list-disc pl-5 my-2 space-y-1">
                                      {children}
                                    </ul>
                                  ),
                                  ol: ({ children }) => (
                                    <ol className="list-decimal pl-5 my-2 space-y-1">
                                      {children}
                                    </ol>
                                  ),
                                  li: ({ children }) => (
                                    <li className="leading-relaxed">{children}</li>
                                  ),
                                  strong: ({ children }) => (
                                    <strong className="font-semibold text-indigo-600 dark:text-indigo-400">
                                      {children}
                                    </strong>
                                  ),
                                  a: ({ href, children }) => (
                                    <a
                                      href={href}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-indigo-600 dark:text-indigo-400 underline underline-offset-2 hover:opacity-80 transition-opacity"
                                    >
                                      {children}
                                    </a>
                                  ),
                                  code: ({ children }) => (
                                    <code className="bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono">
                                      {children}
                                    </code>
                                  ),
                                }}
                              >
                                {msg.content}
                              </ReactMarkdown>
                            </div>
                          </div>

                          <span
                            className="text-[11px] mt-1 ml-1"
                            style={{ color: 'var(--text-muted, #64748b)' }}
                          >
                            {msg.timestamp}
                          </span>
                        </div>
                      </div>

                      {/* Suggested Questions Section */}
                      {msg.suggestedQuestions &&
                        msg.suggestedQuestions.length > 0 && (
                          <div className="ml-10.5 sm:ml-11 mt-3 flex flex-col gap-1.5">
                            <span
                              className="text-xs font-medium flex items-center gap-1"
                              style={{ color: 'var(--text-muted, #64748b)' }}
                            >
                              <Sparkles className="w-3.5 h-3.5 text-indigo-500" />
                              Suggested follow-ups:
                            </span>

                            <div className="flex flex-wrap gap-2 pt-1">
                              {msg.suggestedQuestions.map((question, qIdx) => (
                                <button
                                  key={qIdx}
                                  onClick={() => handleSendMessage(question)}
                                  disabled={isLoading}
                                  className="text-xs sm:text-sm px-3.5 py-1.5 bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600 dark:text-indigo-300 rounded-xl border border-indigo-200/70 dark:border-indigo-800/60 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-all duration-150 cursor-pointer font-medium text-left shadow-2xs hover:shadow-xs active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                  {question}
                                </button>
                              ))}
                            </div>
                          </div>
                        )}
                    </div>
                  )}

                  {/* Error State Message */}
                  {msg.role === 'error' && (
                    <div className="flex items-start gap-2.5 max-w-[85%]">
                      <div className="w-8 h-8 rounded-xl bg-red-100 dark:bg-red-950/50 text-red-600 dark:text-red-400 flex items-center justify-center flex-shrink-0 mt-1">
                        <AlertCircle className="w-4 h-4" />
                      </div>
                      <div className="px-4 py-3 rounded-2xl rounded-tl-none bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 text-red-700 dark:text-red-300 text-sm">
                        {msg.content}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading State Bubble */}
              {isLoading && (
                <div className="flex items-start gap-2.5 animate-fade-in">
                  <div
                    className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-sm border mt-1"
                    style={{
                      backgroundColor: 'var(--bg-card, #ffffff)',
                      borderColor:
                        'rgba(var(--text-primary-rgb, 15, 23, 42), 0.1)',
                      color: 'var(--accent-solid, #4f46e5)',
                    }}
                  >
                    <Bot className="w-4 h-4" />
                  </div>

                  <div
                    className="px-4 py-3 rounded-2xl rounded-tl-none shadow-sm border text-sm flex items-center gap-2.5"
                    style={{
                      backgroundColor: 'var(--bg-card, #ffffff)',
                      color: 'var(--text-primary, #0f172a)',
                      borderColor:
                        'rgba(var(--text-primary-rgb, 15, 23, 42), 0.08)',
                    }}
                  >
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                    <span className="font-medium tracking-wide">Searching...</span>
                  </div>
                </div>
              )}

              {/* Anchor for Auto-scroll */}
              <div ref={messagesEndRef} className="h-2" />
            </div>
          )}
        </div>
      </main>

      {/* ===================================================================
          3. Input Area (Fixed Bottom)
          =================================================================== */}
      <footer
        className="w-full flex-shrink-0 border-t backdrop-blur-md pt-3 pb-4 sm:pb-6 px-4 z-20"
        style={{
          backgroundColor: 'var(--bg-primary, #f8fafc)',
          borderColor: 'rgba(var(--text-primary-rgb, 15, 23, 42), 0.06)',
        }}
      >
        <div className="max-w-3xl mx-auto w-full">
          <div
            className="flex items-end gap-2 p-2 sm:p-2.5 rounded-3xl border shadow-lg transition-all focus-within:ring-2 focus-within:ring-indigo-500/30"
            style={{
              backgroundColor: 'var(--bg-card, #ffffff)',
              borderColor: 'rgba(var(--text-primary-rgb, 15, 23, 42), 0.12)',
            }}
          >
            {/* Auto-expanding Textarea */}
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about Shibir PDF documents..."
              disabled={isLoading}
              className="flex-1 max-h-40 bg-transparent resize-none outline-none border-none px-3 py-1.5 text-sm sm:text-base leading-relaxed placeholder:text-gray-400 dark:placeholder:text-gray-500 disabled:opacity-60"
            />

            {/* Send Button */}
            <button
              onClick={() => handleSendMessage()}
              disabled={!input.trim() || isLoading}
              aria-label="Send Message"
              className="flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center transition-all duration-200 active:scale-95 disabled:opacity-30 disabled:scale-100 disabled:cursor-not-allowed shadow-sm"
              style={{
                backgroundColor: 'var(--accent-solid, #4f46e5)',
                color: 'var(--accent-contrast, #ffffff)',
              }}
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>

          {/* Footer Subtext */}
          <p
            className="text-[11px] text-center mt-2"
            style={{ color: 'var(--text-muted, #64748b)' }}
          >
            Press <kbd className="font-mono font-medium">Enter</kbd> to send,{' '}
            <kbd className="font-mono font-medium">Shift + Enter</kbd> for new
            line. Powered by Qdrant &amp; Gemini RAG.
          </p>
        </div>
      </footer>
    </div>
  );
}
