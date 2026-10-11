"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, FileText, LogOut, FileUp, Sparkles, User, Loader2, Library, FileSearch } from "lucide-react";

const BACKEND_URL = "http://localhost:8000";
const SUPPORTED_EXTENSIONS = ["pdf", "docx", "txt", "md", "csv"];

export default function DocAssistChat() {
  const [sessionId, setSessionId] = useState(null);
  const [file, setFile] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollTo({
        top: scrollContainerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages, loading]);

  const handleFileChange = (e) => {
    setUploadError("");
    const selectedFile = e.target.files?.[0];
    
    if (!selectedFile) {
      setFile(null);
      return;
    }

    const fileExtension = selectedFile.name.split('.').pop().toLowerCase();
    
    if (!SUPPORTED_EXTENSIONS.includes(fileExtension)) {
      setUploadError(`Unsupported format (.${fileExtension}). Please use PDF, DOCX, TXT, MD, or CSV.`);
      setFile(null);
      e.target.value = null; // Clear the input
      return;
    }

    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setUploadError("");
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: "POST",
        body: formData,
      });
      
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to upload document");
      }
      
      const data = await res.json();
      setSessionId(data.session_id);
    } catch (err) {
      console.error("Upload failed", err);
      setUploadError(err.message || "An error occurred during upload.");
    } finally {
      setUploading(false);
    }
  };

  const pollJobResult = async (jobId) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/result/${jobId}`);
        const data = await res.json();

        if (data.status === "finished") {
          clearInterval(interval);
          setMessages((prev) => [...prev, { id: crypto.randomUUID(), sender: "bot", text: data.result }]);
          setLoading(false);
        } else if (data.status === "failed") {
          clearInterval(interval);
          setMessages((prev) => [...prev, { id: crypto.randomUUID(), sender: "bot", text: "Error generating answer." }]);
          setLoading(false);
        }
      } catch (err) {
        clearInterval(interval);
        setLoading(false);
      }
    }, 1000);
  };

  const handleSendMessage = async () => {
    if (!query.trim() || !sessionId || loading) return;

    const userText = query;
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), sender: "user", text: userText }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, query: userText }),
      });
      const data = await res.json();
      pollJobResult(data.job_id);
    } catch (err) {
      setMessages((prev) => [...prev, { id: crypto.randomUUID(), sender: "bot", text: "Failed to queue question." }]);
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    if (!sessionId) return;
    try {
      await fetch(`${BACKEND_URL}/session/${sessionId}`, { method: "DELETE" });
    } catch (err) {
      console.error("Cleanup failed", err);
    } finally {
      setSessionId(null);
      setMessages([]);
      setFile(null);
      setUploadError("");
    }
  };

  return (
    <div className="h-screen w-screen overflow-hidden fixed inset-0 flex flex-col bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-800 via-zinc-950 to-black text-zinc-100 font-sans selection:bg-blue-500/30">
      
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-purple-600/20 rounded-full blur-[120px] pointer-events-none" />

      <header className="shrink-0 h-16 w-full px-6 flex justify-between items-center bg-black/20 backdrop-blur-xl border-b border-white/5 shadow-sm z-50">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl shadow-lg shadow-blue-500/20">
            <Library className="w-5 h-5 text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-zinc-100 to-zinc-400">
            DocAssist
          </h1>
        </div>
        {sessionId && (
          <button
            onClick={handleLogout}
            className="group flex items-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-full text-sm font-medium transition-all duration-300 ease-out hover:shadow-[0_0_20px_rgba(255,255,255,0.05)]"
          >
            <LogOut className="w-4 h-4 text-zinc-400 group-hover:text-red-400 transition-colors" />
            End Session
          </button>
        )}
      </header>

      <main className="flex-1 min-h-0 overflow-hidden flex flex-col relative z-10 w-full">
        <AnimatePresence mode="wait">
          {!sessionId ? (
            <motion.div
              key="upload"
              className="flex-1 flex flex-col items-center justify-center p-4 w-full h-full"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              transition={{ duration: 0.4, ease: [0.23, 1, 0.32, 1] }}
            >
              <div className="w-full max-w-md p-8 bg-white/[0.03] backdrop-blur-2xl border border-white/10 rounded-3xl shadow-2xl relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 pointer-events-none" />
                <div className="relative z-10 flex flex-col items-center text-center">
                  <div className="w-20 h-20 mb-6 rounded-full bg-white/5 flex items-center justify-center border border-white/10 shadow-inner">
                    <FileUp className="w-10 h-10 text-blue-400" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">Upload Knowledge</h2>
                  <p className="text-zinc-400 text-sm mb-6">
                    Initialize an isolated DocAssist workspace by uploading a document. <br/>
                    <span className="text-xs text-blue-400 font-semibold mt-2 block tracking-wide uppercase">
                      Supported: PDF, DOCX, TXT, MD, CSV
                    </span>
                  </p>

                  {uploadError && (
                    <motion.div 
                      initial={{ opacity: 0, y: -10 }} 
                      animate={{ opacity: 1, y: 0 }} 
                      className="w-full mb-4 px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs text-left flex items-center gap-2"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-red-400 shrink-0" />
                      {uploadError}
                    </motion.div>
                  )}

                  <label className="w-full relative group cursor-pointer">
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt,.md,.csv"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                    <div className={`w-full p-4 border-2 border-dashed rounded-xl bg-black/20 transition-all duration-300 flex items-center gap-4
                      ${file ? "border-blue-500/50 bg-blue-500/5" : "border-white/10 group-hover:bg-white/5 group-hover:border-blue-500/50"}
                    `}>
                      <FileText className={`w-6 h-6 shrink-0 ${file ? "text-blue-400" : "text-zinc-500"}`} />
                      <span className={`text-sm truncate ${file ? "text-blue-100 font-medium" : "text-zinc-400"}`}>
                        {file ? file.name : "Select a document file..."}
                      </span>
                    </div>
                  </label>

                  <button
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    className="mt-6 w-full py-3.5 px-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl text-sm font-bold shadow-lg shadow-blue-900/20 transition-all duration-300 flex items-center justify-center gap-2"
                  >
                    {uploading ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Ingesting Document...
                      </>
                    ) : (
                      "Initialize Session"
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.4 }}
              className="flex-1 flex flex-col min-h-0 w-full"
            >
              <div 
                ref={scrollContainerRef} 
                className="flex-1 overflow-y-auto w-full p-4 md:p-6 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent"
              >
                <div className="max-w-4xl mx-auto space-y-6 pb-4">
                  {messages.length === 0 && (
                    <div className="h-[50vh] flex flex-col items-center justify-center text-zinc-500 gap-3">
                      <FileSearch className="w-12 h-12 opacity-50" />
                      <p>Document embedded. Ask DocAssist a question to begin.</p>
                    </div>
                  )}
                  
                  <AnimatePresence initial={false}>
                    {messages.map((m) => (
                      <motion.div
                        key={m.id}
                        initial={{ opacity: 0, y: 15, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ type: "spring", stiffness: 260, damping: 25 }}
                        className={`flex gap-4 ${m.sender === "user" ? "flex-row-reverse" : "flex-row"}`}
                      >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 shadow-sm ${
                          m.sender === "user" ? "bg-gradient-to-br from-blue-500 to-blue-600" : "bg-white/10 border border-white/5"
                        }`}>
                          {m.sender === "user" ? <User className="w-4 h-4 text-white" /> : <Sparkles className="w-4 h-4 text-zinc-300" />}
                        </div>
                        
                        <div className={`px-5 py-3.5 rounded-2xl max-w-[80%] text-sm leading-relaxed shadow-sm ${
                          m.sender === "user" 
                            ? "bg-blue-600/20 border border-blue-500/20 text-blue-50 rounded-tr-sm" 
                            : "bg-black/40 border border-white/5 text-zinc-200 rounded-tl-sm backdrop-blur-md"
                        }`}>
                          {m.text}
                        </div>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                  
                  {loading && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="flex gap-4">
                      <div className="w-8 h-8 rounded-full bg-white/10 border border-white/5 flex items-center justify-center shrink-0">
                        <Loader2 className="w-4 h-4 text-zinc-400 animate-spin" />
                      </div>
                      <div className="px-5 py-4 rounded-2xl bg-black/40 border border-white/5 rounded-tl-sm flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.3s]" />
                        <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce [animation-delay:-0.15s]" />
                        <div className="w-2 h-2 rounded-full bg-zinc-500 animate-bounce" />
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>

              <div className="shrink-0 w-full p-4 bg-black/40 border-t border-white/5 backdrop-blur-xl">
                <div className="max-w-4xl mx-auto">
                  <div className="relative flex items-end gap-2 bg-white/5 border border-white/10 rounded-2xl p-2 shadow-inner focus-within:border-blue-500/50 focus-within:bg-white/10 transition-all duration-300">
                    <textarea
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                          e.preventDefault();
                          handleSendMessage();
                        }
                      }}
                      placeholder="Ask about your document..."
                      rows={1}
                      className="w-full max-h-32 min-h-[44px] bg-transparent text-zinc-100 placeholder-zinc-500 px-3 py-2.5 resize-none outline-none text-sm"
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={loading || !query.trim()}
                      className="shrink-0 p-3 bg-blue-600 hover:bg-blue-500 disabled:bg-white/5 disabled:text-zinc-600 text-white rounded-xl transition-all duration-200"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                  <div className="text-center mt-2">
                    <span className="text-[10px] text-zinc-600 uppercase tracking-widest font-semibold">
                      Shift + Enter for new line
                    </span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}