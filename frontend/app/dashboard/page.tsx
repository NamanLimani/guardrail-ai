// "use client";

// import { useEffect, useState, useRef } from "react";
// import { useRouter } from "next/navigation";

// interface Message {
//   role: "user" | "assistant";
//   content: string;
// }

// interface Document {
//   id: string;
//   filename: string;
//   status: string;
//   risk_score?: number;
//   created_at: string;
// }

// export default function Dashboard() {
//   const [docs, setDocs] = useState<Document[]>([]);
//   const [query, setQuery] = useState("");
//   const [messages, setMessages] = useState<Message[]>([]); // <-- Chat History
//   const [searching, setSearching] = useState(false);
//   const [uploading, setUploading] = useState(false);
//   const [recording, setRecording] = useState(false);
//   const mediaRecorderRef = useRef<MediaRecorder | null>(null);
//   const router = useRouter();
//   const [showDebug, setShowDebug] = useState(false); // Toggle switch
//   const [debugData, setDebugData] = useState<any>(null); // Store the scores/context
  
//   // Auto-scroll to bottom of chat
//   const chatEndRef = useRef<HTMLDivElement>(null);

//   useEffect(() => {
//     const token = localStorage.getItem("token");
//     if (!token) {
//       router.push("/login");
//       return;
//     }
//     fetchDocuments(token);
//   }, []);

//   useEffect(() => {
//     // Scroll to bottom whenever messages change
//     chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   }, [messages]);

//   const fetchDocuments = async (token: string) => {
//     try {
//       const res = await fetch("http://localhost:8000/documents/", {
//         headers: { Authorization: `Bearer ${token}` },
//       });
//       if (res.ok) {
//         const data = await res.json();
//         setDocs(data);
//       }
//     } catch (err) {
//       console.error(err);
//     }
//   };



//   const handleSearch = async (e: React.FormEvent) => {
//     e.preventDefault();
//     if (!query.trim()) return;

//     // Reset UI
//     const newHistory = [...messages, { role: "user", content: query } as Message];
//     setMessages(newHistory);
//     setQuery("");
//     setSearching(true);
//     setDebugData(null); // Clear old debug info

//     // Add Placeholder
//     setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

//     const token = localStorage.getItem("token");

//     try {
//       const res = await fetch("http://localhost:8000/chat/", {
//         method: "POST",
//         headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
//         body: JSON.stringify({ query: query, history: messages }),
//       });

//       if (!res.body) throw new Error("No body");

//       const reader = res.body.getReader();
//       const decoder = new TextDecoder();
//       let done = false;
//       let aiText = "";

//       while (!done) {
//         const { value, done: doneReading } = await reader.read();
//         done = doneReading;
//         const chunkValue = decoder.decode(value, { stream: !done });
        
//         // Split by newline because we might get multiple JSON objects in one chunk
//         const lines = chunkValue.split("\n").filter(line => line.trim() !== "");

//         for (const line of lines) {
//             try {
//                 const json = JSON.parse(line);

//                 if (json.type === "debug") {
//                     // MAGIC: We found the hidden data!
//                     setDebugData(json.data);
//                 } else if (json.type === "token") {
//                     // Standard text token
//                     aiText += json.content;
//                     setMessages((prev) => {
//                         const updated = [...prev];
//                         updated[updated.length - 1] = { role: "assistant", content: aiText };
//                         return updated;
//                     });
//                 }
//             } catch (e) {
//                 console.error("Error parsing JSON chunk", e);
//             }
//         }
//       }
//     } catch (err) {
//       console.error(err);
//     } finally {
//       setSearching(false);
//     }
//   };

  

//   const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
//     if (!e.target.files) return;
//     setUploading(true);
//     const file = e.target.files[0];
//     const token = localStorage.getItem("token");
//     const formData = new FormData();
//     formData.append("file", file);

//     try {
//       await fetch("http://localhost:8000/upload/", {
//         method: "POST",
//         headers: { Authorization: `Bearer ${token}` },
//         body: formData,
//       });
//       setTimeout(() => fetchDocuments(token!), 2000);
//     } catch (err) {
//       console.error(err);
//     } finally {
//       setUploading(false);
//     }
//   };

//   const startRecording = async () => {
//     try {
//       const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
//       const mediaRecorder = new MediaRecorder(stream);
//       mediaRecorderRef.current = mediaRecorder;
//       const chunks: BlobPart[] = [];

//       mediaRecorder.ondataavailable = (e) => {
//         if (e.data.size > 0) chunks.push(e.data);
//       };

//       mediaRecorder.onstop = async () => {
//         const audioBlob = new Blob(chunks, { type: "audio/webm" });
//         const formData = new FormData();
//         formData.append("file", audioBlob, "voice_command.webm");
        
//         // Send to Backend
//         setRecording(false);
//         const token = localStorage.getItem("token");
//         try {
//             const res = await fetch("http://localhost:8000/transcribe/", {
//                 method: "POST",
//                 body: formData, // No Authorization header needed for this simple test, or add it if you want security
//             });
//             const data = await res.json();
//             setQuery(data.text); // <--- MAGIC: Puts the text into the input box!
//         } catch (err) {
//             console.error("Transcription failed", err);
//         }
//       };

//       mediaRecorder.start();
//       setRecording(true);
//     } catch (err) {
//       alert("Microphone permission denied!");
//       console.error(err);
//     }
//   };

//   const stopRecording = () => {
//     if (mediaRecorderRef.current && recording) {
//       mediaRecorderRef.current.stop();
//       // Stop all audio tracks to release the mic
//       mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
//     }
//   };

//   return (
//     <div className="min-h-screen bg-gray-50 flex flex-col">
//       {/* Navbar */}
//       <nav className="bg-white shadow-sm p-4 px-8 flex justify-between items-center">
//         <h1 className="text-2xl font-bold text-blue-600">GuardRail AI</h1>
//         <button 
//           onClick={() => { localStorage.removeItem("token"); router.push("/login"); }}
//           className="text-red-500 hover:text-red-700 font-medium"
//         >
//           Logout
//         </button>
//       </nav>

//       {/* Developer Mode Toggle Bar */}
//       <div className="bg-gray-100 p-2 px-8 flex justify-end items-center gap-2 border-b border-gray-200">
//         <span className="text-sm font-medium text-gray-600">🛠️ Developer Mode</span>
//         <button 
//             onClick={() => setShowDebug(!showDebug)}
//             className={`w-12 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out ${showDebug ? 'bg-blue-600' : 'bg-gray-300'}`}
//         >
//             <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${showDebug ? 'translate-x-6' : ''}`} />
//         </button>
//       </div>

//       {/* MAIN GRID CONTAINER */}
//       {/* Dynamic Grid: 3 cols normally, 4 cols if debug is open */}
//       <div className={`flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-1 gap-6 ${showDebug ? 'md:grid-cols-4' : 'md:grid-cols-3'}`}>
        
//         {/* --- LEFT COLUMN: Documents (Always col-span-1) --- */}
//         <div className="bg-white p-6 rounded-xl shadow-md h-fit md:col-span-1">
//           <h2 className="text-xl font-semibold mb-4">Your Knowledge Base</h2>
          
//           {/* Upload Box */}
//           <div className="mb-6 p-4 border-2 border-dashed border-gray-200 rounded-lg text-center hover:bg-gray-50 transition cursor-pointer">
//              <input type="file" onChange={handleUpload} disabled={uploading} className="hidden" id="file-upload" />
//              <label htmlFor="file-upload" className="cursor-pointer block w-full h-full">
//                 {uploading ? <span className="text-blue-500 animate-pulse">Uploading...</span> : <span className="text-gray-500">Click to Upload PDF</span>}
//              </label>
//           </div>

//           {/* Document List */}
//           <div className="space-y-2">
//                 {docs.map((doc) => (
//                 <div key={doc.id} className="flex justify-between items-center p-2 bg-gray-50 rounded text-xs">
//                     <div className="flex flex-col">
//                         <span className="truncate w-24 font-medium">{doc.filename}</span>
//                         {/* RISK BADGE */}
//                         {doc.risk_score !== undefined && (
//                             <span className={`text-[10px] font-bold ${
//                                 doc.risk_score >= 100 ? 'text-red-600' : 
//                                 doc.risk_score >= 20 ? 'text-yellow-600' : 'text-green-600'
//                             }`}>
//                                 {doc.risk_score >= 100 ? '🔴 HIGH RISK' : 
//                                  doc.risk_score >= 20 ? '🟡 MED RISK' : '🟢 SAFE'}
//                             </span>
//                         )}
//                     </div>
//                     <span className="text-gray-400">{doc.status}</span>
//                 </div>
//                 ))}
//             </div>
//         </div>

//         {/* --- MIDDLE COLUMN: Chat Interface (Always col-span-2) --- */}
//         <div className="bg-white rounded-xl shadow-md flex flex-col h-[600px] md:col-span-2">
//           {/* Messages Area */}
//           <div className="flex-1 overflow-y-auto p-6 space-y-4">
//             {messages.length === 0 && (
//                 <div className="text-center text-gray-400 mt-20">
//                     <p>👋 Ask me anything about your documents!</p>
//                 </div>
//             )}
//             {messages.map((msg, i) => (
//               <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
//                 <div className={`max-w-[85%] p-4 rounded-xl whitespace-pre-wrap leading-relaxed shadow-sm ${
//                   msg.role === 'user' 
//                     ? 'bg-blue-600 text-white rounded-tr-none' 
//                     : 'bg-gray-100 text-gray-800 rounded-tl-none'
//                 }`}>
//                   {msg.content}
//                 </div>
//               </div>
//             ))}
//             {searching && (
//                 <div className="flex justify-start animate-pulse">
//                     <div className="bg-gray-100 p-4 rounded-xl rounded-tl-none text-gray-500">Thinking...</div>
//                 </div>
//             )}
//             <div ref={chatEndRef} />
//           </div>

//           {/* Input Area */}
//           <form onSubmit={handleSearch} className="p-4 border-t border-gray-100 flex gap-2">
//             <input 
//               type="text" 
//               value={query}
//               onChange={(e) => setQuery(e.target.value)}
//               placeholder="Ask a follow-up question..."
//               className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black placeholder-gray-500"
//             />

//             {/* Microphone Button */}
//             <button
//                 type="button" 
//                 onClick={recording ? stopRecording : startRecording}
//                 className={`p-3 rounded-full transition-all border ${
//                     recording 
//                     ? "bg-red-500 border-red-600 animate-pulse text-white shadow-lg shadow-red-300" 
//                     : "bg-white border-gray-300 text-gray-600 hover:bg-gray-100"
//                 }`}
//                 title="Voice Input"
//             >
//                 <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
//                     <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
//                     <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
//                     <line x1="12" y1="19" x2="12" y2="23"/>
//                     <line x1="8" y1="23" x2="16" y2="23"/>
//                 </svg>
//             </button>

//             <button 
//               type="submit" 
//               disabled={searching}
//               className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium shadow-sm transition-colors"
//             >
//               Send
//             </button>
//           </form>
//         </div>

//         {/* --- RIGHT COLUMN: Developer Panel (Only visible if showDebug is true) --- */}
//         {showDebug && (
//             <div className="bg-gray-900 text-green-400 p-4 rounded-xl shadow-xl h-[600px] overflow-y-auto font-mono text-xs md:col-span-1 border border-gray-700">
//                 <h3 className="text-white font-bold border-b border-gray-700 pb-2 mb-4 flex items-center gap-2">
//                     <span>🔍 Inspection Panel</span>
//                     <span className="text-[10px] bg-green-900 text-green-300 px-1 rounded">LIVE</span>
//                 </h3>
                
//                 {debugData ? (
//                     <div className="space-y-6">
//                         {/* 1. Vector Scores */}
//                         <div>
//                             <h4 className="text-gray-500 mb-2 uppercase tracking-wider font-semibold text-[10px]">Vector Matches (Relevance)</h4>
//                             <div className="space-y-3">
//                                 {debugData.vector_matches.map((m: any, i: number) => (
//                                     <div key={i} className="bg-gray-800 p-2 rounded border border-gray-700">
//                                         <div className="flex justify-between mb-1 items-center">
//                                             <span className="truncate text-white max-w-[70%]" title={m.filename}>{m.filename}</span>
//                                             <span className="text-yellow-400 font-bold">{m.score.toFixed(4)}</span>
//                                         </div>
//                                         {/* Score Bar */}
//                                         <div className="w-full bg-gray-700 h-1.5 rounded-full overflow-hidden">
//                                             <div 
//                                                 className={`h-full rounded-full ${m.score > 0.5 ? 'bg-green-500' : 'bg-yellow-500'}`} 
//                                                 style={{ width: `${Math.min(m.score * 100, 100)}%` }}
//                                             ></div>
//                                         </div>
//                                     </div>
//                                 ))}
//                             </div>
//                         </div>

//                         {/* 2. Redacted Context */}
//                         <div>
//                             <h4 className="text-gray-500 mb-2 uppercase tracking-wider font-semibold text-[10px]">LLM Input (Redacted)</h4>
//                             <div className="bg-black p-3 rounded border border-green-900 h-80 overflow-y-auto whitespace-pre-wrap leading-tight text-gray-300 shadow-inner">
//                                 {debugData.context_sent_to_llm}
//                             </div>
//                         </div>
//                     </div>
//                 ) : (
//                     <div className="flex flex-col items-center justify-center h-full text-gray-600">
//                         <p className="italic">Waiting for query...</p>
//                         <p className="text-[10px] mt-2">Toggle panel to inspect RAG pipeline</p>
//                     </div>
//                 )}
//             </div>
//         )}

//       </div>
//     </div>
//   );
// }


"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { api } from '../../utils/api'; // Correct import
import axios from 'axios'; // For error types

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Document {
  id: string;
  filename: string;
  status: string;
  risk_score?: number;
  created_at: string;
}

export default function Dashboard() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [searching, setSearching] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [recording, setRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const router = useRouter();
  const [showDebug, setShowDebug] = useState(false);
  const [debugData, setDebugData] = useState<any>(null);
  
  // Auto-scroll to bottom of chat
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 1. Define fetchDocuments FIRST so it can be used in useEffect
  const fetchDocuments = async () => {
    try {
      // The 'api' client handles the URL and Token automatically
      const res = await api.get("/documents/");
      setDocs(res.data);
    } catch (error) {
      console.error("Error fetching documents:", error);
      // Optional: Redirect to login if 401
      if (axios.isAxiosError(error) && error.response?.status === 401) {
        router.push("/login");
      }
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      router.push("/login");
      return;
    }
    fetchDocuments(); // No arguments needed now
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 2. Updated handleSearch using the new API client
  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    // UI Updates
    const newHistory = [...messages, { role: "user", content: query } as Message];
    setMessages(newHistory);
    setQuery("");
    setSearching(true);
    setDebugData(null);
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const response = await api.post('/chat/', { 
          query: query, 
          history: messages 
      }, {
          responseType: 'stream',
          adapter: 'fetch', // Required for streaming to work with Axios in browser
      });

      const reader = response.data.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let aiText = "";

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value, { stream: !done });
        
        const lines = chunkValue.split("\n").filter((line: string) => line.trim() !== "");
        for (const line of lines) {
            try {
                const json = JSON.parse(line);
                if (json.type === "debug") {
                    setDebugData(json.data);
                } else if (json.type === "token") {
                    aiText += json.content;
                    setMessages((prev) => {
                        const updated = [...prev];
                        updated[updated.length - 1] = { role: "assistant", content: aiText };
                        return updated;
                    });
                }
            } catch (e) {
                console.error("Error parsing JSON chunk", e);
            }
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setSearching(false);
    }
  };

  // 3. Updated handleUpload using api.post
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0]) return;
    setUploading(true);

    const formData = new FormData();
    formData.append("file", e.target.files[0]);

    try {
      await api.post("/upload/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      
      // Refresh the list (No arguments needed!)
      await fetchDocuments(); 
    } catch (error) {
      console.error("Upload failed", error);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  // 4. Updated startRecording to use dynamic API
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      const chunks: BlobPart[] = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("file", audioBlob, "voice_command.webm");
        
        setRecording(false);
        try {
            // Updated to use api.post (no manual localhost URL)
            const res = await api.post("/transcribe/", formData, {
                 headers: { "Content-Type": "multipart/form-data" },
            });
            setQuery(res.data.text);
        } catch (err) {
            console.error("Transcription failed", err);
        }
      };

      mediaRecorder.start();
      setRecording(true);
    } catch (err) {
      alert("Microphone permission denied!");
      console.error(err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Navbar */}
      <nav className="bg-white shadow-sm p-4 px-8 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-blue-600">GuardRail AI</h1>
        <button 
          onClick={() => { localStorage.removeItem("token"); router.push("/login"); }}
          className="text-red-500 hover:text-red-700 font-medium"
        >
          Logout
        </button>
      </nav>

      {/* Developer Mode Toggle Bar */}
      <div className="bg-gray-100 p-2 px-8 flex justify-end items-center gap-2 border-b border-gray-200">
        <span className="text-sm font-medium text-gray-600">🛠️ Developer Mode</span>
        <button 
            onClick={() => setShowDebug(!showDebug)}
            className={`w-12 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out ${showDebug ? 'bg-blue-600' : 'bg-gray-300'}`}
        >
            <div className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform duration-200 ease-in-out ${showDebug ? 'translate-x-6' : ''}`} />
        </button>
      </div>

      {/* MAIN GRID CONTAINER */}
      <div className={`flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-1 gap-6 ${showDebug ? 'md:grid-cols-4' : 'md:grid-cols-3'}`}>
        
        {/* --- LEFT COLUMN: Documents --- */}
        <div className="bg-white p-6 rounded-xl shadow-md h-fit md:col-span-1">
          <h2 className="text-xl font-semibold mb-4">Your Knowledge Base</h2>
          
          <div className="mb-6 p-4 border-2 border-dashed border-gray-200 rounded-lg text-center hover:bg-gray-50 transition cursor-pointer">
             <input type="file" onChange={handleUpload} disabled={uploading} className="hidden" id="file-upload" />
             <label htmlFor="file-upload" className="cursor-pointer block w-full h-full">
                {uploading ? <span className="text-blue-500 animate-pulse">Uploading...</span> : <span className="text-gray-500">Click to Upload PDF</span>}
             </label>
          </div>

          <div className="space-y-2">
                {docs.map((doc) => (
                <div key={doc.id} className="flex justify-between items-center p-2 bg-gray-50 rounded text-xs">
                    <div className="flex flex-col">
                        <span className="truncate w-24 font-medium">{doc.filename}</span>
                        {doc.risk_score !== undefined && (
                            <span className={`text-[10px] font-bold ${
                                doc.risk_score >= 100 ? 'text-red-600' : 
                                doc.risk_score >= 20 ? 'text-yellow-600' : 'text-green-600'
                            }`}>
                                {doc.risk_score >= 100 ? '🔴 HIGH RISK' : 
                                 doc.risk_score >= 20 ? '🟡 MED RISK' : '🟢 SAFE'}
                            </span>
                        )}
                    </div>
                    <span className="text-gray-400">{doc.status}</span>
                </div>
                ))}
            </div>
        </div>

        {/* --- MIDDLE COLUMN: Chat Interface --- */}
        <div className="bg-white rounded-xl shadow-md flex flex-col h-[600px] md:col-span-2">
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
                <div className="text-center text-gray-400 mt-20">
                    <p>👋 Ask me anything about your documents!</p>
                </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] p-4 rounded-xl whitespace-pre-wrap leading-relaxed shadow-sm ${
                  msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-tr-none' 
                    : 'bg-gray-100 text-gray-800 rounded-tl-none'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {searching && (
                <div className="flex justify-start animate-pulse">
                    <div className="bg-gray-100 p-4 rounded-xl rounded-tl-none text-gray-500">Thinking...</div>
                </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <form onSubmit={handleSearch} className="p-4 border-t border-gray-100 flex gap-2">
            <input 
              type="text" 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a follow-up question..."
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black placeholder-gray-500"
            />
            <button
                type="button" 
                onClick={recording ? stopRecording : startRecording}
                className={`p-3 rounded-full transition-all border ${
                    recording 
                    ? "bg-red-500 border-red-600 animate-pulse text-white shadow-lg shadow-red-300" 
                    : "bg-white border-gray-300 text-gray-600 hover:bg-gray-100"
                }`}
                title="Voice Input"
            >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
            </button>
            <button 
              type="submit" 
              disabled={searching}
              className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium shadow-sm transition-colors"
            >
              Send
            </button>
          </form>
        </div>

        {/* --- RIGHT COLUMN: Developer Panel --- */}
        {showDebug && (
            <div className="bg-gray-900 text-green-400 p-4 rounded-xl shadow-xl h-[600px] overflow-y-auto font-mono text-xs md:col-span-1 border border-gray-700">
                <h3 className="text-white font-bold border-b border-gray-700 pb-2 mb-4 flex items-center gap-2">
                    <span>🔍 Inspection Panel</span>
                    <span className="text-[10px] bg-green-900 text-green-300 px-1 rounded">LIVE</span>
                </h3>
                
                {debugData ? (
                    <div className="space-y-6">
                        <div>
                            <h4 className="text-gray-500 mb-2 uppercase tracking-wider font-semibold text-[10px]">Vector Matches (Relevance)</h4>
                            <div className="space-y-3">
                                {debugData.vector_matches.map((m: any, i: number) => (
                                    <div key={i} className="bg-gray-800 p-2 rounded border border-gray-700">
                                        <div className="flex justify-between mb-1 items-center">
                                            <span className="truncate text-white max-w-[70%]" title={m.filename}>{m.filename}</span>
                                            <span className="text-yellow-400 font-bold">{m.score.toFixed(4)}</span>
                                        </div>
                                        <div className="w-full bg-gray-700 h-1.5 rounded-full overflow-hidden">
                                            <div 
                                                className={`h-full rounded-full ${m.score > 0.5 ? 'bg-green-500' : 'bg-yellow-500'}`} 
                                                style={{ width: `${Math.min(m.score * 100, 100)}%` }}
                                            ></div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div>
                            <h4 className="text-gray-500 mb-2 uppercase tracking-wider font-semibold text-[10px]">LLM Input (Redacted)</h4>
                            <div className="bg-black p-3 rounded border border-green-900 h-80 overflow-y-auto whitespace-pre-wrap leading-tight text-gray-300 shadow-inner">
                                {debugData.context_sent_to_llm}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600">
                        <p className="italic">Waiting for query...</p>
                        <p className="text-[10px] mt-2">Toggle panel to inspect RAG pipeline</p>
                    </div>
                )}
            </div>
        )}

      </div>
    </div>
  );
}