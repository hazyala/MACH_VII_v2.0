import React, { useState, useRef, useEffect } from 'react';
import useAppStore from '../store';
import { Send, Cpu } from 'lucide-react';

const ChatPanel = () => {
    // Subscribe to chat history from global store
    const chatHistory = useAppStore((state) => state.brain.chat_history || []);

    // Local state only for input
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);

    // Scroll to bottom
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatHistory]);

    const handleSend = async () => {
        if (!input.trim()) return;

        try {
            // UserRequestDTO (COMMAND 타입) 준수
            const payload = {
                request_type: 'command',
                command: input
            };

            await fetch(`http://localhost:8000/api/request`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            setInput('');
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="bg-white rounded-[22px] shadow-[0_4px_20px_rgba(0,0,0,0.05)] p-5 h-full flex flex-col">
            <div className="text-[11px] font-bold text-[#86868B] uppercase tracking-wider mb-4 flex justify-between items-center">
                <span>Dialogue Flow</span>
                <span className="flex items-center gap-1 text-[10px] bg-green-100 text-green-600 px-2 py-0.5 rounded-full">
                    <Cpu size={10} /> ONLINE
                </span>
            </div>

            {/* Chat History */}
            <div className="flex-1 overflow-y-auto pr-2 space-y-4 font-sans mb-4">
                {chatHistory.length === 0 && (
                    <div className="text-center text-gray-400 text-sm mt-10">
                        대화 내역이 없습니다. (시스템 연결 대기중...)
                    </div>
                )}
                {chatHistory.map((msg, idx) => (
                    <div
                        key={idx}
                        className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[75%] px-5 py-3 text-[15px] leading-relaxed shadow-sm
                                ${msg.role === 'user'
                                    ? 'bg-[#007AFF] text-white rounded-[20px] rounded-br-[4px]'
                                    : 'bg-[#F2F2F7] text-[#1D1D1F] rounded-[20px] rounded-bl-[4px]'
                                }`}
                        >
                            {msg.text}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="mt-auto bg-[#F2F2F7] rounded-[28px] p-2 pl-5 flex items-center shadow-inner">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                    placeholder="마마, 명을 내리소서..."
                    className="flex-1 bg-transparent border-none text-[15px] outline-none text-[#1D1D1F] placeholder-gray-400"
                />
                <button
                    onClick={handleSend}
                    className="w-[36px] h-[36px] bg-[#007AFF] rounded-full flex items-center justify-center text-white hover:bg-blue-600 transition-colors shadow-md"
                >
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
};

export default ChatPanel;
