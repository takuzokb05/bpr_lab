import { useState, useEffect } from 'react';
import type { Task } from './types';
import { motion, AnimatePresence } from 'framer-motion';
import { Check, ShoppingCart, Shirt, Trash2, SprayCan, Flower, Sparkles, Leaf } from 'lucide-react';
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
    <div className="min-h-screen bg-[#FFFDF5] text-[#374151] pb-40 font-sans font-bold">
      {/* Jackpot Modal - FIX: Force Fullscreen Centering */}
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

      <div className="max-w-md mx-auto p-6 pt-12 overflow-x-hidden">
        {/* Header */}
        <header className="mb-8 text-center flex flex-col items-center">
          <LogoTitle />

          <div className="mx-auto w-fit min-w-[12rem] bg-white border-4 border-[#fbcfe8] rounded-full px-8 py-3 shadow-sm whitespace-nowrap mt-6">
            <span className="font-bold text-gray-500 tracking-widest text-lg">
              {new Date().toLocaleDateString('ja-JP', { month: 'long', day: 'numeric', weekday: 'short' })}
            </span>
          </div>
        </header>

        {/* Quick Add Buttons */}
        <div className="flex gap-4 justify-between mb-10 w-full">
          <QuickAddButton label="洗濯" color="bg-[#dbeafe] text-[#2563eb]" icon={<Shirt size={28} />} onClick={() => addTask('洗濯')} />
          <QuickAddButton label="掃除" color="bg-[#fef9c3] text-[#a16207]" icon={<SprayCan size={28} />} onClick={() => addTask('掃除')} />
          <QuickAddButton label="買い物" color="bg-[#fee2e2] text-[#dc2626]" icon={<ShoppingCart size={28} />} onClick={() => addTask('買い物')} />
        </div>

        {/* Input Area */}
        <div className="mb-12">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && addTask(inputValue)}
            placeholder="入力してえらい～"
            className="w-full h-16 bg-white border-4 border-[#fed7aa] rounded-full px-8 text-xl font-bold outline-none text-gray-700 placeholder:text-[#fed7aa] focus:border-[#fb923c] transition-colors shadow-sm text-center"
          />
        </div>

        {/* Active List */}
        <div className="mb-10">
          <h2 className="text-2xl font-black text-gray-700 ml-4 mb-4">がんばる！</h2>
          <ul className="space-y-6">
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
        <div>
          <h2 className="text-2xl font-black text-gray-400 ml-4 mb-4">がんばったこと</h2>
          <ul className="space-y-6 opacity-60">
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
      </div>

      {/* Floating Footer */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-max max-w-[90%]">
        <div className="bg-white/90 backdrop-blur-md border-4 border-[#fbcfe8] rounded-full px-8 py-3 shadow-lg flex items-center gap-4">
          <span className="font-bold text-gray-600 whitespace-nowrap text-lg">今日のがんばり</span>
          <motion.span
            key={completedTasks.length}
            initial={{ scale: 1.5, rotate: -20 }}
            animate={{ scale: 1, rotate: 0 }}
            className="text-4xl font-black text-[#f472b6]"
          >
            {completedTasks.length}
          </motion.span>
          <span className="text-3xl">🌸</span>
        </div>
      </div>
    </div>
  );
}

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
            // Thick white outline + Soft Shadow
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
        "flex-1 flex flex-col items-center justify-center gap-1 px-2 py-4 rounded-full font-bold shadow-sm transition-transform min-w-0",
        color
      )}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
    >
      {icon}
      <span className="text-sm">{label}</span>
    </motion.button>
  );
}

function TaskCard({ task, onToggle, onDelete, isCompleted }: { task: Task, onToggle: () => void, onDelete: () => void, isCompleted?: boolean }) {
  return (
    <motion.li
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className={clsx(
        "bg-white rounded-[2rem] border-4 p-4 flex items-center justify-between shadow-sm group",
        isCompleted ? "border-[#f3f4f6]" : "border-[#ffedd5]"
      )}
    >
      <div className="flex items-center gap-4 flex-1 min-w-0">
        <motion.button
          className={clsx(
            "w-12 h-12 rounded-full border-4 flex items-center justify-center cursor-pointer flex-shrink-0 transition-colors",
            isCompleted ? "border-[#fecaca] bg-[#fecaca]" : "border-[#fed7aa] bg-white hover:bg-[#fff7ed]"
          )}
          onClick={onToggle}
          whileTap={{ scale: 0.8 }}
        >
          {isCompleted ? (
            <Flower size={24} className="text-[#dc2626]" strokeWidth={3} />
          ) : (
            <div className="w-2 h-2 rounded-full bg-[#fed7aa]" />
          )}
        </motion.button>

        <span className={clsx("text-xl font-bold truncate tracking-wide text-gray-700", isCompleted && "line-through text-gray-300")}>
          {task.text}
        </span>
      </div>

      <motion.button
        onClick={(e) => { e.stopPropagation(); onDelete(); }}
        className="text-gray-300 hover:text-red-400 transition-colors p-2 shrink-0"
        whileTap={{ scale: 0.9 }}
      >
        <Trash2 size={28} />
      </motion.button>
    </motion.li>
  );
}
