import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, Plus, Send, User, Search, Hash } from "lucide-react";
import { useThreads, useCreateThread, useThreadComments, useCreateComment } from "@/hooks/useCommunity";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

export default function CommunityPage() {
  const { data: threads, isLoading } = useThreads();
  const { mutate: createThread } = useCreateThread();
  const [selectedThreadId, setSelectedThreadId] = useState<number | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Create Form State
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newCategory, setNewCategory] = useState("General");

  const handleSubmitThread = (e: React.FormEvent) => {
    e.preventDefault();
    createThread(
      { title: newTitle, content: newContent, category: newCategory },
      { onSuccess: () => setIsDialogOpen(false) }
    );
  };

  const filteredThreads = threads?.filter((t: any) => 
    t.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col h-[calc(100vh-120px)] gap-6"
    >
      {/* Page Header */}
      <div className="flex flex-col md:flex-row justify-between items-end md:items-center bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Community Forum</h1>
          <p className="text-slate-500 mt-1">Connect, discuss, and resolve issues with your neighbors.</p>
        </div>
        
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <motion.button 
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="bg-blue-600 text-white px-5 py-2.5 rounded-xl font-medium flex items-center gap-2 shadow-lg shadow-blue-600/20 hover:bg-blue-700 transition-all"
            >
              <Plus className="w-5 h-5" /> New Topic
            </motion.button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md bg-white rounded-2xl">
            <DialogHeader>
              <DialogTitle className="text-xl">Start a Discussion</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmitThread} className="space-y-4 mt-2">
              <input 
                placeholder="Topic Title" 
                className="w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
              />
              <select 
                className="w-full p-3 bg-slate-50 border-none rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              >
                <option>General</option>
                <option>Issue Reporting</option>
                <option>Suggestion</option>
                <option>Event</option>
              </select>
              <textarea 
                placeholder="What's on your mind?" 
                className="w-full p-3 bg-slate-50 border-none rounded-xl h-32 resize-none focus:ring-2 focus:ring-blue-500 outline-none"
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
              />
              <button type="submit" className="w-full bg-blue-600 text-white py-3 rounded-xl font-bold hover:bg-blue-700 transition">Post Discussion</button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Main Content Area */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-full min-h-0">
        
        {/* Sidebar: Thread List */}
        <div className="lg:col-span-4 flex flex-col gap-4 h-full min-h-0">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-slate-400" />
            <input 
              placeholder="Search topics..." 
              className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto pr-2 space-y-3 custom-scrollbar">
            {isLoading ? (
              <div className="text-center py-10 text-slate-400">Loading threads...</div>
            ) : filteredThreads?.map((thread: any) => (
              <motion.div 
                key={thread.id} 
                onClick={() => setSelectedThreadId(thread.id)}
                whileHover={{ scale: 1.01 }}
                className={`p-5 rounded-xl border cursor-pointer transition-all duration-200 ${
                  selectedThreadId === thread.id 
                    ? 'bg-blue-50 border-blue-200 shadow-inner' 
                    : 'bg-white border-slate-100 hover:border-blue-100 hover:shadow-md'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <span className={`text-[10px] font-bold px-2 py-1 rounded-full uppercase tracking-wider ${
                    thread.category === 'Issue Reporting' ? 'bg-red-100 text-red-600' : 
                    thread.category === 'Suggestion' ? 'bg-green-100 text-green-600' : 
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {thread.category}
                  </span>
                  <span className="text-xs text-slate-400">{new Date(thread.created_at).toLocaleDateString()}</span>
                </div>
                <h3 className={`font-bold text-md mb-1 ${selectedThreadId === thread.id ? 'text-blue-700' : 'text-slate-800'}`}>
                  {thread.title}
                </h3>
                <p className="text-sm text-slate-500 line-clamp-2">{thread.content}</p>
                <div className="flex items-center gap-3 mt-4 text-xs text-slate-400">
                  <div className="flex items-center gap-1">
                    <User className="w-3 h-3" /> {thread.author}
                  </div>
                  <div className="flex items-center gap-1">
                    <MessageSquare className="w-3 h-3" /> {thread.comment_count}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Main: Chat View */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col h-full">
          {selectedThreadId ? (
            <ThreadDetailView threadId={selectedThreadId} />
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-300 bg-slate-50/50">
              <Hash className="w-16 h-16 mb-4 opacity-20" />
              <p className="text-lg font-medium">Select a discussion to start reading</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}

// --- Chat Component ---
function ThreadDetailView({ threadId }: { threadId: number }) {
  const { data: comments, isLoading } = useThreadComments(threadId);
  const { mutate: addComment } = useCreateComment();
  const [reply, setReply] = useState("");

  // Auto-scroll to bottom ref could be added here

  const handleSend = () => {
    if (!reply.trim()) return;
    addComment({ threadId, content: reply });
    setReply("");
  };

  return (
    <>
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-slate-50/30">
        {isLoading ? (
          <div className="flex justify-center p-10"><div className="animate-spin w-6 h-6 border-2 border-blue-500 rounded-full border-t-transparent"></div></div>
        ) : (
          <AnimatePresence>
            {comments?.map((comment: any) => (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                key={comment.id} 
                className="flex gap-4 group"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-blue-500/20 shrink-0">
                  {comment.author[0].toUpperCase()}
                </div>
                <div className="flex-1 max-w-[85%]">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-bold text-sm text-slate-800">{comment.author}</span>
                    <span className="text-[10px] text-slate-400">{new Date(comment.created_at).toLocaleString()}</span>
                  </div>
                  <div className="bg-white p-4 rounded-2xl rounded-tl-none text-slate-700 text-sm shadow-sm border border-slate-100 leading-relaxed">
                    {comment.content}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-100">
        <div className="flex gap-3 bg-slate-50 p-2 rounded-xl border border-slate-200 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-400 transition-all">
          <input 
            className="flex-1 bg-transparent border-none px-3 py-2 text-sm focus:outline-none text-slate-800 placeholder:text-slate-400"
            placeholder="Type your reply..."
            value={reply}
            onChange={(e) => setReply(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <motion.button 
            whileTap={{ scale: 0.9 }}
            onClick={handleSend} 
            className="bg-blue-600 text-white p-2.5 rounded-lg shadow-md hover:bg-blue-700 transition-colors"
          >
            <Send className="w-4 h-4" />
          </motion.button>
        </div>
        <p className="text-[10px] text-slate-400 mt-2 text-center">
          Remember to keep discussions respectful and relevant to the community.
        </p>
      </div>
    </>
  );
}