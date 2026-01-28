import React, { useState, useRef, useEffect } from 'react';
import useAppStore from '../store';
import { Send, Cpu } from 'lucide-react';

const ChatPanel = () => {
    // We could pull logs from store if available, for now using dummy + simple interactive chat
    const [messages, setMessages] = useState([
        { id: 1, role: 'bot', text: '공주마마, 맹칠이 대령했사옵니다. 원하시는 대로 대궐의 배치를 다시 하였사옵니다.' },
        { id: 2, role: 'user', text: '그래, 중앙을 좀 줄이고 채팅창을 넓게 하니까 훨씬 시원해 보여.' },
        { id: 3, role: 'bot', text: '혜안이 무궁하시옵니다! 이제 마마와 더 많은 서신을 주고받아도 화면이 부족할 일은 없겠사옵니다.' },
        { id: 4, role: 'bot', text: '기억 저장소(FalkorDB)도 이 넓은 대화 내용을 꼼꼼히 기록하고 있사오니 안심하시옵소서.' },
    ]);
    const [input, setInput] = useState('');
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    useEffect(scrollToBottom, [messages]);

    const handleSend = () => {
        if (!input.trim()) return;
        const newMsg = { id: Date.now(), role: 'user', text: input };
        setMessages(prev => [...prev, newMsg]);
        setInput('');

        // Dummy Reply for now (Later connect to backend)
        setTimeout(() => {
            setMessages(prev => [...prev, { id: Date.now() + 1, role: 'bot', text: '명 받들겠사옵니다. (시스템 연결 필요)' }]);
        }, 1000);
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
                {messages.map((msg) => (
                    <div
                        key={msg.id}
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
