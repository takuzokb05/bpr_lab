import React, { useState, useEffect, forwardRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Plus,
    Trash2,
    Check,
    Sparkles,
    Shirt,
    Search,
    ShoppingCart,
    Utensils,
    Coffee
} from 'lucide-react';

// --- canvas-confetti loader ---
// CDNからスクリプトを読み込むためのフック
const useConfetti = () => {
    const [isLoaded, setIsLoaded] = useState(false);

    useEffect(() => {
        if (typeof window.confetti === 'function') {
            setIsLoaded(true);
            return;
        }

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js';
        script.async = true;
        script.onload = () => setIsLoaded(true);
        document.body.appendChild(script);

        return () => {
            document.body.removeChild(script);
        };
    }, []);

    // 紙吹雪を発火させる関数
    const triggerConfetti = () => {
        if (isLoaded && window.confetti) {
            window.confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#FDA4AF', '#6EE7B7', '#FDE047', '#BAE6FD'], // パステルカラー
                disableForReducedMotion: true
            });
        }
    };

    return triggerConfetti;
};


// --- Components ---

// 掃除機のアイコン（SVGを描画）
const VacuumIcon = ({ size, className, strokeWidth }) => (
    <svg
        xmlns="http://www.w3.org/2000/svg"
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
    >
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7" />
        <path d="M12 19V3" />
        <path d="M12 3h4" />
        <rect x="8" y="9" width="8" height="6" rx="1" />
    </svg>
);

const QuickButton = ({ icon: Icon, label, colorClass, onClick, delay }) => (
    <motion.button
        whileHover={{ scale: 1.1, rotate: 3 }}
        whileTap={{ scale: 0.9 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
            type: "spring",
            stiffness: 400,
            damping: 10,
            delay: delay
        }}
        onClick={onClick}
        className={`flex flex-col items-center justify-center p-3 sm:p-4 rounded-full ${colorClass} border-2 sm:border-4 border-gray-700 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] active:shadow-none transition-colors w-20 h-20 sm:w-24 sm:h-24`}
    >
        <Icon size={32} className="text-gray-700 mb-1" strokeWidth={2.5} />
        <span className="text-xs sm:text-sm font-bold text-gray-700">{label}</span>
    </motion.button>
);

// AnimatePresenceの直下で使用するため、forwardRefを使用
const TaskCard = forwardRef(({ task, onToggle, onDelete }, ref) => (
    <motion.div
        ref={ref}
        layout
        initial={{ opacity: 0, y: -20, scale: 0.8 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ scale: 0, opacity: 0, transition: { duration: 0.2 } }}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 500, damping: 30 }}
        className="bg-white rounded-3xl p-4 mb-3 border-2 sm:border-4 border-gray-200 shadow-[0px_4px_0px_0px_#E5E7EB] flex items-center justify-between group"
    >
        <div className="flex items-center gap-4 flex-1 cursor-pointer" onClick={() => onToggle(task.id)}>
            <div className={`relative w-8 h-8 sm:w-10 sm:h-10 rounded-full border-2 sm:border-4 transition-colors duration-300 flex items-center justify-center ${task.completed ? 'bg-[#6EE7B7] border-[#6EE7B7]' : 'bg-white border-gray-300'}`}>
                {task.completed && (
                    <motion.div
                        initial={{ scale: 0, rotate: -45 }}
                        animate={{ scale: 1, rotate: 0 }}
                        transition={{ type: "spring", stiffness: 500, damping: 20 }}
                    >
                        <Check size={20} className="text-white" strokeWidth={4} />
                    </motion.div>
                )}
            </div>
            <span className={`text-lg sm:text-xl font-bold text-gray-700 transition-all duration-300 ${task.completed ? 'line-through text-gray-300 decoration-4 decoration-gray-300' : ''}`}>
                {task.text}
            </span>
        </div>

        <motion.button
            whileHover={{ scale: 1.1, rotate: 15 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => onDelete(task.id)}
            className="p-2 bg-red-50 text-red-400 rounded-full hover:bg-red-100 transition-colors"
        >
            <Trash2 size={24} strokeWidth={2.5} />
        </motion.button>
    </motion.div>
));

// コンポーネント名を定義（デバッグ用）
TaskCard.displayName = "TaskCard";

const AnimatedTitle = () => {
    const title = "がんばるリスト";
    const colors = ["text-pink-400", "text-yellow-400", "text-blue-400", "text-green-400", "text-purple-400", "text-orange-400", "text-teal-400"];

    return (
        <div className="relative z-10 mb-2">
            {/* Cloud Background Removed for better visibility on mobile */}

            <div className="flex justify-center items-baseline gap-1">
                {title.split('').map((char, index) => (
                    <motion.span
                        key={index}
                        className={`text-4xl sm:text-5xl font-black ${colors[index % colors.length]} drop-shadow-sm`}
                        initial={{ y: -20, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        transition={{
                            type: "spring",
                            stiffness: 300,
                            delay: index * 0.1
                        }}
                        whileHover={{ y: -10, rotate: index % 2 === 0 ? 5 : -5 }}
                    >
                        {char}
                    </motion.span>
                ))}
            </div>
        </div>
    );
};

export default function App() {
    // --- Logic for 3AM Reset & Persistence ---

    // 業務日付（朝3時区切り）を取得する関数
    const getBusinessDateStr = () => {
        const now = new Date();
        // 3時間引くことで、00:00-02:59を前日に含める
        const adjustedDate = new Date(now.getTime() - 3 * 60 * 60 * 1000);

        // ローカル時間で日付文字列を生成 (YYYY-MM-DD)
        const year = adjustedDate.getFullYear();
        const month = String(adjustedDate.getMonth() + 1).padStart(2, '0');
        const day = String(adjustedDate.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };

    const DEFAULT_TASKS = [
        { id: 9999, text: "朝起きれてえらい！", completed: true },
    ];

    // 初期化関数
    const initializeTodos = () => {
        // サーバーサイドレンダリング対策
        if (typeof window === 'undefined') return DEFAULT_TASKS;

        const savedTodos = localStorage.getItem('ganbaru_todos');
        const lastBusinessDate = localStorage.getItem('ganbaru_last_date');
        const currentBusinessDate = getBusinessDateStr();

        // 日付が変わっている場合、リセット
        if (lastBusinessDate && lastBusinessDate !== currentBusinessDate) {
            localStorage.setItem('ganbaru_last_date', currentBusinessDate);

            // リセット時は「朝起きれてえらい！」のみ
            const resetTasks = [
                { id: Date.now(), text: "朝起きれてえらい！", completed: true }
            ];
            return resetTasks;
        }

        // 保存されたデータがあれば使う
        if (savedTodos) {
            if (!lastBusinessDate) {
                localStorage.setItem('ganbaru_last_date', currentBusinessDate);
            }
            return JSON.parse(savedTodos);
        }

        // 初回起動時（データなし）
        localStorage.setItem('ganbaru_last_date', currentBusinessDate);
        return DEFAULT_TASKS;
    };

    const [todos, setTodos] = useState(initializeTodos);

    // マウント時に日付再チェック（ホットリロード時などに有効）
    useEffect(() => {
        const currentBusinessDate = getBusinessDateStr();
        const lastBusinessDate = localStorage.getItem('ganbaru_last_date');
        if (lastBusinessDate && lastBusinessDate !== currentBusinessDate) {
            setTodos(initializeTodos());
        }
    }, []);

    const [inputValue, setInputValue] = useState("");
    const [completedCount, setCompletedCount] = useState(0);

    // 紙吹雪フックを使用
    const triggerConfetti = useConfetti();

    useEffect(() => {
        // タスク変更時に保存
        localStorage.setItem('ganbaru_todos', JSON.stringify(todos));

        // Calculate completed tasks for the rainbow counter
        const count = todos.filter(t => t.completed).length;
        setCompletedCount(count);
    }, [todos]);

    const addTodo = (text) => {
        if (!text.trim()) return;
        const newTodo = {
            id: Date.now(),
            text: text,
            completed: false
        };
        setTodos([newTodo, ...todos]);
        setInputValue("");
    };

    const toggleTodo = (id) => {
        setTodos(todos.map(todo => {
            if (todo.id === id) {
                const newCompletedStatus = !todo.completed;
                // 未完了から完了になった時だけ紙吹雪を発火
                if (newCompletedStatus) {
                    triggerConfetti();
                }
                return { ...todo, completed: newCompletedStatus };
            }
            return todo;
        }));
    };

    const deleteTodo = (id) => {
        setTodos(todos.filter(todo => todo.id !== id));
    };

    const quickAdd = (text) => {
        addTodo(text);
    };

    const activeTodos = todos.filter(t => !t.completed);
    const hasCompletedTodos = todos.some(t => t.completed);

    return (
        <div className="min-h-screen bg-[#FFFDF5] font-['Zen_Maru_Gothic'] text-[#4B5563] overflow-x-hidden selection:bg-[#FDA4AF] selection:text-white pb-32">
            {/* Font Import */}
            <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700;900&display=swap');
        
        body {
          font-family: 'Zen Maru Gothic', sans-serif;
        }
      `}</style>
            <div className="max-w-xl mx-auto px-4 py-8 sm:py-12 relative">

                {/* Header */}
                <header className="text-center mb-8 relative">
                    <AnimatedTitle />
                    <p className="text-gray-500 font-bold text-lg mt-4 bg-white/50 inline-block px-4 py-1 rounded-full border-2 border-gray-100">
                        {new Date().toLocaleDateString('ja-JP', { month: 'long', day: 'numeric', weekday: 'short' })}
                    </p>
                </header>

                {/* Quick Buttons */}
                <div className="flex justify-center gap-3 sm:gap-4 mb-8 overflow-x-auto py-2 no-scrollbar relative z-20">
                    <QuickButton
                        icon={Shirt}
                        label="洗濯"
                        colorClass="bg-[#BAE6FD]"
                        onClick={() => quickAdd("洗濯する")}
                        delay={0.1}
                    />
                    <QuickButton
                        icon={VacuumIcon}
                        label="掃除"
                        colorClass="bg-[#FDE047]"
                        onClick={() => quickAdd("掃除する")}
                        delay={0.2}
                    />
                    <QuickButton
                        icon={ShoppingCart}
                        label="買い物"
                        colorClass="bg-[#FCA5A5]"
                        onClick={() => quickAdd("買い物に行く")}
                        delay={0.3}
                    />
                </div>

                {/* Input Area (Button Removed) */}
                <div className="flex mb-8 relative z-20">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && addTodo(inputValue)}
                        placeholder="なにをがんばる？"
                        className="w-full bg-white border-4 border-[#D1D5DB] rounded-full px-6 py-4 text-xl font-bold placeholder-gray-300 focus:outline-none focus:border-[#FDA4AF] focus:ring-4 focus:ring-[#FDA4AF]/20 transition-all shadow-[inset_2px_2px_4px_rgba(0,0,0,0.05)] text-center"
                    />
                </div>

                {/* Active List Label */}
                <div className="flex items-center gap-2 mb-4 px-2">
                    <Sparkles size={24} className="text-yellow-400 animate-pulse" />
                    <h2 className="text-2xl font-black text-gray-700">やることリスト</h2>
                </div>

                {/* Task List */}
                <div className="space-y-2">
                    <AnimatePresence mode='popLayout'>
                        {activeTodos.map(task => (
                            <TaskCard
                                key={task.id}
                                task={task}
                                onToggle={toggleTodo}
                                onDelete={deleteTodo}
                            />
                        ))}
                    </AnimatePresence>

                    {/* 条件分岐1: タスクが完了しており、かつアクティブなタスクがない場合 */}
                    {activeTodos.length === 0 && hasCompletedTodos && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center py-12 text-gray-400 bg-white/30 rounded-3xl border-2 border-dashed border-gray-300"
                        >
                            <p className="font-bold text-xl text-[#6EE7B7] drop-shadow-sm mb-2">
                                <Sparkles className="inline-block mr-2" />
                                全部おわったよ！すごい！
                                <Sparkles className="inline-block ml-2" />
                            </p>
                        </motion.div>
                    )}

                    {/* 条件分岐2: 全くタスクがない場合（初期状態など） */}
                    {todos.length === 0 && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="text-center py-12 text-gray-400 bg-white/30 rounded-3xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center gap-2"
                        >
                            <div className="bg-orange-100 p-3 rounded-full mb-2">
                                <Coffee size={32} className="text-orange-400" />
                            </div>
                            <p className="font-bold text-lg">今日も無理せず頑張ろ～</p>
                        </motion.div>
                    )}
                </div>

                {/* Completed Section (Optional, showing recently completed) */}
                {hasCompletedTodos && (
                    <div className="mt-8 transition-opacity">
                        <div className="flex items-center gap-2 mb-4 px-2">
                            <span className="text-2xl">💮</span>
                            <h3 className="text-2xl font-black text-gray-700">がんばったリスト</h3>
                        </div>
                        <AnimatePresence mode='popLayout'>
                            {todos.filter(t => t.completed).map(task => (
                                <TaskCard
                                    key={task.id}
                                    task={task}
                                    onToggle={toggleTodo}
                                    onDelete={deleteTodo}
                                />
                            ))}
                        </AnimatePresence>
                    </div>
                )}

            </div>

            {/* Floating Footer Counter */}
            <div className="fixed bottom-6 left-0 right-0 z-50 pointer-events-none">
                <div className="max-w-xl mx-auto pl-4 pr-6 flex justify-end">
                    <motion.div
                        initial={{ y: 100, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        className="pointer-events-auto bg-white/80 backdrop-blur-md border-2 border-white/50 p-3 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.1)] flex items-center gap-4 pl-6 pr-4"
                    >
                        <span className="font-bold text-gray-600">今日のがんばり</span>
                        <div className="flex items-center gap-1">
                            <motion.span
                                key={completedCount}
                                initial={{ scale: 1.5, color: '#FDA4AF' }}
                                animate={{ scale: 1, color: '#EC4899' }}
                                className="text-4xl font-black bg-gradient-to-r from-pink-500 via-purple-500 to-indigo-500 text-transparent bg-clip-text"
                            >
                                {completedCount}
                            </motion.span>
                            <motion.div
                                animate={{ rotate: [0, 10, -10, 0] }}
                                transition={{ repeat: Infinity, duration: 2, repeatDelay: 1 }}
                            >
                                <span className="text-3xl">🌸</span>
                            </motion.div>
                        </div>
                    </motion.div>
                </div>
            </div>

        </div>
    );
}
