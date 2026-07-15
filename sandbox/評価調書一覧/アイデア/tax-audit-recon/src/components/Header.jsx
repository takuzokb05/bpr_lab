import React from 'react';
import { Search, Bell, User } from 'lucide-react';

const Header = () => {
    return (
        <header className="sticky top-0 z-40 bg-white dark:bg-[#1a1d21] border-b border-[#e8f0f2] dark:border-gray-700 px-6 py-3 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <h2 className="text-lg font-bold text-gray-800 dark:text-white">ダッシュボード</h2>
            </div>

            <div className="flex items-center gap-4">
                <div className="relative hidden md:block">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-[#538393]" size={18} />
                    <input
                        type="text"
                        placeholder="全体検索..."
                        className="bg-[#e8f0f2] dark:bg-gray-800 border-none rounded-lg pl-10 pr-4 py-2 text-sm w-64 focus:ring-2 focus:ring-primary focus:outline-none"
                    />
                </div>

                <div className="flex gap-2">
                    <button className="p-2 rounded-lg bg-[#e8f0f2] dark:bg-gray-800 text-[#0f171a] dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors">
                        <Bell size={20} />
                    </button>
                    <button className="p-2 rounded-lg bg-primary text-white hover:opacity-90 transition-opacity">
                        <User size={20} />
                    </button>
                </div>
            </div>
        </header>
    );
};

export default Header;
