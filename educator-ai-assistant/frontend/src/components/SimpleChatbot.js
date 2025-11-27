import React, { useEffect, useRef, useState } from 'react';
import api from '../services/api';

const STORAGE_KEY = 'simple_chatbot_history_v1';

const SimpleChatbot = () => {
  const [messages, setMessages] = useState(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg = { id: Date.now(), role: 'user', content: input };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const payload = { message: userMsg.content, history: messages.concat(userMsg), auto_execute: true };
      const resp = await api.post('/api/v1/simple-chatbot/message', payload);
      const reply = resp.data && resp.data.reply ? resp.data.reply : 'No response';
      // Preserve action/executed metadata so the UI can render disambiguation buttons
      const assistantMsg = { id: Date.now() + 1, role: 'assistant', content: reply, meta: resp.data };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      const errMsg = { id: Date.now() + 2, role: 'assistant', content: 'Error contacting chatbot.' };
      setMessages((m) => [...m, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const sendQuickReply = async (text) => {
    if (!text) return;
    const userMsg = { id: Date.now(), role: 'user', content: text };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);
    try {
      const payload = { message: userMsg.content, history: messages.concat(userMsg), auto_execute: true };
      const resp = await api.post('/api/v1/simple-chatbot/message', payload);
      const reply = resp.data && resp.data.reply ? resp.data.reply : 'No response';
      const assistantMsg = { id: Date.now() + 1, role: 'assistant', content: reply, meta: resp.data };
      setMessages((m) => [...m, assistantMsg]);
    } catch (e) {
      const errMsg = { id: Date.now() + 2, role: 'assistant', content: 'Error contacting chatbot.' };
      setMessages((m) => [...m, errMsg]);
    } finally {
      setLoading(false);
    }
  };

  const clearHistory = () => {
    setMessages([]);
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 h-[600px] flex flex-col">
      <div className="p-6 border-b flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Simple Gemini Chatbot</h3>
          <p className="text-sm text-gray-500">Uses the provided Gemini API key. History is stored locally.</p>
        </div>
        <div>
          <button onClick={clearHistory} className="text-xs text-red-500">Clear</button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="space-y-4">
          {messages.map((m) => (
            <div key={m.id} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div>
                <div className={`inline-block p-3 rounded-2xl ${m.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900'}`}>
                  <div style={{ whiteSpace: 'pre-wrap' }}>{m.content}</div>
                </div>
                {m.role === 'assistant' && m.meta && m.meta.executed && m.meta.executed.suggestions && (
                  <div className="mt-2 flex flex-wrap gap-2">
                    {m.meta.executed.suggestions.map((sugg, idx) => (
                      <button
                        key={idx}
                        className="px-3 py-1 text-sm bg-gray-200 rounded-md hover:bg-gray-300"
                        onClick={() => sendQuickReply(String(idx + 1))}
                      >
                        {idx + 1}) {sugg}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={endRef} />
        </div>
      </div>

      <div className="p-6 border-t">
        <div className="flex space-x-4">
          <input
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder="Ask the Gemini chatbot..."
          />
          <button
            onClick={sendMessage}
            disabled={loading || !input.trim()}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg disabled:opacity-50"
          >
            {loading ? '...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimpleChatbot;
