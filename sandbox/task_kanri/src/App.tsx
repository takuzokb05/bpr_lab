import { useState, useEffect } from 'react';
import type { Task } from './types';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingCart, Shirt, Trash2, SprayCan, Flower, Sparkles, Leaf } from 'lucide-react';
import confetti from 'canvas-confetti';
import clsx from 'clsx';

const STORAGE_KEY = 'home-hero-db-v1';
const LAST_OPEN_DATE_KEY = 'home-hero-last-open-date';

// Polyfill for crypto.randomUUID
const generateId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};

export default function App() {
  const [tasks, setTasks] = useState<Task[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch (e) {
      console.error('Failed to parse tasks', e);
      return [];
    }
  });

  const [inputValue, setInputValue] = useState('');
  const [showJackpot, setShowJackpot] = useState(false);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
  }, [tasks]);

  useEffect(() => {
    const lastDate = localStorage.getItem(LAST_OPEN_DATE_KEY);
    const today = new Date().toDateString();

    if (lastDate !== today) {
      const dailyTask: Task = {
        id: generateId(),
        text: '今日の私、起きてえらい！',
        completed: true,
        createdAt: Date.now(),
      };
      setTasks(prev => [dailyTask, ...prev]);
      localStorage.setItem(LAST_OPEN_DATE_KEY, today);
    }
  }, []);

  // Auto-dismiss jackpot after 3 seconds
  useEffect(() => {
    if (showJackpot) {
      const timer = setTimeout(() => {
        setShowJackpot(false);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [showJackpot]);

  const addTask = (text: string) => {
    if (!text.trim()) return;
    const newTask: Task = {
      id: generateId(),
      text: text,
      completed: false,
      createdAt: Date.now(),
    };
    setTasks(prev => [newTask, ...prev]);
    setInputValue('');
  };

  const toggleTask = (id: string, completed: boolean) => {
    if (!completed) {
      triggerReward();
    }
    setTimeout(() => {
      setTasks(prev => prev.map(t => t.id === id ? { ...t, completed: !t.completed } : t));
    }, 300);
  };

  const deleteTask = (id: string) => {
    setTasks(prev => prev.filter(t => t.id !== id));
  };

  const triggerReward = () => {
    const rand = Math.random();
    if (rand < 0.3) {
      confetti({
        particleCount: 150,
        spread: 100,
        origin: { x: 0.5, y: 0.5 }, // Centered
        zIndex: 60,
        colors: ['#ff99c8', '#fcf6bd', '#d0f4de', '#a9def9', '#e4c1f9']
      });
      setShowJackpot(true);
    } else {
      confetti({
        particleCount: 40,
        spread: 50,
        origin: { x: 0.5, y: 0.7 }
      });
    }
  };

  const activeTasks = tasks.filter(t => !t.completed);
  const completedTasks = tasks.filter(t => t.completed);

  return (
    <div className="min-h-screen bg-[#FFFDF5] text-[#374151] pb-32 font-sans font-bold selection:bg-[#fbcfe8] selection:text-white">
      {/* Jackpot Modal - RESTORED PREMIUM LOOK */}
      <AnimatePresence>
        {showJackpot && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed top-0 left-0 w-screen h-screen z-[100] grid place-items-center bg-black/40 backdrop-blur-sm"
            onClick={() => setShowJackpot(false)}
          >
            <motion.div
              initial={{ scale: 0, rotate: -10 }}
              animate={{ scale: 1, rotate: 0 }}
              exit={{ scale: 0, rotate: 10 }}
              transition={{ type: "spring", bounce: 0.5 }}
              className="relative bg-[#fffbeb] rounded-[2rem] shadow-2xl border-4 border-[#fcd34d] p-10 flex flex-col items-center justify-center text-center max-w-[90%] w-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <h2 className="text-5xl font-black text-[#f59e0b] mb-4 drop-shadow-sm whitespace-nowrap">
                🎉 GREAT! 🎉
              </h2>
              <p className="text-3xl font-black text-gray-700 leading-relaxed whitespace-nowrap">
                世界一の妻！<br />ありがとう！
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="max-w-xl mx-auto px-4 py-8 sm:py-12 relative">
        {/* Header - RESTORED LOGOTITLE */}
        <header className="mb-8 text-center relative flex flex-col items-center">
          <LogoTitle />

          <div className="mx-auto w-fit min-w-[12rem] bg-white border-4 border-[#fbcfe8] rounded-full px-8 py-3 shadow-[0px_4px_0px_0px_rgba(0,0,0,0.05)] whitespace-nowrap mt-4">
            <span className="font-bold text-gray-500 tracking-widest text-lg">
              {new Date().toLocaleDateString('ja-JP', { month: 'long', day: 'numeric', weekday: 'short' })}
            </span>
          </div>
        </header>

        {/* Quick Add Buttons - RESTORED COLORS */}
        <div className="flex justify-center gap-3 sm:gap-4 mb-8 overflow-x-auto py-2 no-scrollbar">
          <QuickAddButton
            label="洗濯"
            color="bg-[#dbeafe] border-[#bfdbfe]"
            icon={<Shirt size={32} className="text-[#2563eb]" strokeWidth={2.5} />}
            onClick={() => addTask('洗濯')}
          />
          <QuickAddButton
            label="掃除"
            color="bg-[#fef9c3] border-[#fde047]"
            icon={<SprayCan size={32} className="text-[#a16207]" strokeWidth={2.5} />}
            onClick={() => addTask('掃除')}
          />
          <QuickAddButton
            label="買い物"
            color="bg-[#fee2e2] border-[#fecaca]"
            icon={<ShoppingCart size={32} className="text-[#dc2626]" strokeWidth={2.5} />}
            onClick={() => addTask('買い物')}
          />
        </div>

        {/* Input Area - RESTORED COLORS */}
        <div className="flex gap-2 mb-8 relative z-20">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addTask(inputValue)}
            placeholder="入力してえらい～"
            className="flex-1 bg-white border-4 border-[#fed7aa] rounded-full px-8 py-4 text-xl font-bold placeholder:text-[#fed7aa] focus:outline-none focus:border-[#fb923c] focus:ring-4 focus:ring-[#fb923c]/20 transition-all shadow-[inset_2px_2px_4px_rgba(0,0,0,0.05)] w-full text-center text-gray-700"
          />
        </div>

        {/* Active List - REFERENCE SPACING */}
        <div className="space-y-2 mb-8">
          <div className="flex items-center gap-2 mb-4 px-2">
            <Sparkles size={24} className="text-yellow-400 animate-pulse" />
            <h2 className="text-2xl font-black text-gray-700">がんばる！</h2>
          </div>

          <ul className="space-y-2">
            <AnimatePresence mode="popLayout">
              {activeTasks.map(task => (
                <TaskCard
                  key={task.id}
                  task={task}
                  onToggle={() => toggleTask(task.id, task.completed)}
                  onDelete={() => deleteTask(task.id)}
                />
              ))}
            </AnimatePresence>
          </ul>
        </div>

        {/* Completed List */}
        {completedTasks.length > 0 && (
          <div className="mt-8 opacity-60 hover:opacity-100 transition-opacity">
            <div className="flex items-center gap-2 mb-2 px-2">
              <CheckCircle size={20} className="text-gray-400" />
              <h3 className="text-lg font-bold text-gray-400">がんばったこと</h3>
            </div>
            <ul className="space-y-2">
              <AnimatePresence mode="popLayout">
                {completedTasks.slice(0, 5).map(task => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onToggle={() => toggleTask(task.id, task.completed)}
                    onDelete={() => deleteTask(task.id)}
                    isCompleted
                  />
                ))}
              </AnimatePresence>
            </ul>
          </div>
        )}
      </div>

      {/* Floating Footer - RESTORED STYLE */}
      <motion.div
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-sm bg-white/90 backdrop-blur-md border-4 border-[#fbcfe8] p-3 rounded-full shadow-[0_8px_32px_rgba(0,0,0,0.1)] flex items-center justify-between px-6 z-50"
      >
        <span className="font-bold text-gray-600">今日のがんばり</span>
        <div className="flex items-center gap-1">
          <motion.span
            key={completedTasks.length}
            initial={{ scale: 1.5, color: '#f472b6' }}
            animate={{ scale: 1, color: '#db2777' }}
            className="text-4xl font-black text-[#f472b6]"
          >
            {completedTasks.length}
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
  );
}

// Helper for Footer Icon
function CheckCircle({ size, className }: { size: number, className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
      <polyline points="22 4 12 14.01 9 11.01" />
    </svg>
  );
}

// RESTORED PREMIUM LOGOTITLE
function LogoTitle() {
  const chars = "がんばるリスト".split('');
  const colors = ['#ff99c8', '#facc15', '#6ee7b7', '#a9def9', '#e4c1f9'];

  return (
    <div className="flex items-center justify-center gap-1 select-none flex-wrap">
      <motion.div
        animate={{ rotate: [0, 10, -10, 0] }}
        transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
        className="mr-2"
      >
        <Sparkles className="text-[#facc15]" size={40} />
      </motion.div>

      {chars.map((char, index) => (
        <motion.span
          key={index}
          className="text-6xl md:text-7xl font-black inline-block relative my-1"
          style={{
            color: colors[index % colors.length],
            // Thick white outline + Soft Shadow - RESTORED
            textShadow: `
                            3px 3px 0 #fff, -3px 3px 0 #fff, 3px -3px 0 #fff, -3px -3px 0 #fff,
                            3px 0 0 #fff, -3px 0 0 #fff, 0 3px 0 #fff, 0 -3px 0 #fff,
                            4px 4px 0 rgba(0,0,0,0.1)
                        `
          }}
          animate={{
            y: [0, -8, 0],
            rotate: [0, Math.random() * 6 - 3, 0]
          }}
          transition={{
            repeat: Infinity,
            duration: 2.5,
            ease: "easeInOut",
            delay: index * 0.15
          }}
        >
          {char}
        </motion.span>
      ))}

      <motion.div
        animate={{ rotate: [0, -10, 10, 0] }}
        transition={{ repeat: Infinity, duration: 3, ease: "easeInOut", delay: 1 }}
        className="ml-2"
      >
        <Leaf className="text-[#6ee7b7]" size={40} />
      </motion.div>
    </div>
  );
}

function QuickAddButton({ label, icon, color, onClick }: { label: string, icon: React.ReactNode, color: string, onClick: () => void }) {
  return (
    <motion.button
      onClick={onClick}
      className={clsx(
        "flex flex-col items-center justify-center p-3 sm:p-4 rounded-full border-4 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.05)] active:shadow-none transition-colors w-24 h-24 shrink-0",
        color
      )}
      whileHover={{ scale: 1.1, rotate: 3 }}
      whileTap={{ scale: 0.9 }}
    >
      {icon}
      <span className="text-sm font-bold text-gray-700">{label}</span>
    </motion.button>
  );
}

function TaskCard({ task, onToggle, onDelete, isCompleted }: { task: Task, onToggle: () => void, onDelete: () => void, isCompleted?: boolean }) {
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: -20, scale: 0.8 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ scale: 0, opacity: 0 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={clsx(
        "bg-white rounded-3xl p-4 mb-3 border-4 flex items-center justify-between shadow-[0px_4px_0px_0px_#E5E7EB] group",
        isCompleted ? "border-[#f3f4f6]" : "border-[#ffedd5]"
      )}
    >
      <div className="flex items-center gap-4 flex-1 cursor-pointer" onClick={onToggle}>
        <div className={clsx(
          "relative w-10 h-10 rounded-full border-4 transition-colors duration-300 flex items-center justify-center flex-shrink-0",
          isCompleted ? "bg-[#fecaca] border-[#fecaca]" : "bg-white border-[#fed7aa] group-hover:bg-[#fff7ed]"
        )}>
          {isCompleted ? (
            <motion.div
              initial={{ scale: 0, rotate: -45 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 20 }}
            >
              <Flower size={24} className="text-[#dc2626]" strokeWidth={3} />
            </motion.div>
          ) : (
            <div className="w-2 h-2 rounded-full bg-[#fed7aa]" />
          )}
        </div>

        <span className={clsx(
          "text-lg sm:text-xl font-bold text-gray-700 transition-all duration-300",
          isCompleted && "line-through text-gray-300 decoration-4 decoration-gray-200"
        )}>
          {task.text}
        </span>
      </div>

      <motion.button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className="p-2 bg-red-50 text-red-400 rounded-full hover:bg-red-100 transition-colors"
        whileHover={{ scale: 1.1, rotate: 15 }}
        whileTap={{ scale: 0.9 }}
      >
        <Trash2 size={24} strokeWidth={2.5} />
      </motion.button>
    </motion.li>
  );
}
