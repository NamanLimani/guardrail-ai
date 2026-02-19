// "use client";

// import { useState } from "react";
// import { useRouter } from "next/navigation"; // Hook to redirect users

// export default function LoginPage() {
//   const [email, setEmail] = useState("");
//   const [password, setPassword] = useState("");
//   const [error, setError] = useState("");
//   const router = useRouter();

//   const handleLogin = async (e: React.FormEvent) => {
//     e.preventDefault(); // Stop page from refreshing
//     setError("");

//     // 1. Prepare Form Data (OAuth2 requires x-www-form-urlencoded)
//     const formData = new URLSearchParams();
//     formData.append("username", email); // Remember: Backend expects 'username', not 'email'
//     formData.append("password", password);

//     try {
//       const res = await fetch("http://127.0.0.1:8000/token", {
//         method: "POST",
//         headers: { "Content-Type": "application/x-www-form-urlencoded" },
//         body: formData,
//       });

//       if (!res.ok) throw new Error("Invalid credentials");

//       const data = await res.json();
      
//       // 2. Save Token to Local Storage (Like a cookie)
//       localStorage.setItem("token", data.access_token);
      
//       // 3. Redirect to Dashboard (We will build this next)
//       alert("Login Successful! Token saved.");
//       router.push("/dashboard"); 
//     } catch (err) {
//       setError("Login failed. Check your email/password.");
//     }
//   };

//   return (
//     <div className="flex min-h-screen items-center justify-center bg-gray-100 text-black">
//       <div className="w-full max-w-md bg-white p-8 rounded-lg shadow-md">
//         <h2 className="text-2xl font-bold mb-6 text-center text-blue-600">GuardRail Login</h2>
        
//         <form onSubmit={handleLogin} className="space-y-4">
//           <div>
//             <label className="block text-sm font-medium text-gray-700">Email</label>
//             <input 
//               type="email" 
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm focus:border-blue-500 focus:ring-blue-500"
//               required 
//             />
//           </div>
          
//           <div>
//             <label className="block text-sm font-medium text-gray-700">Password</label>
//             <input 
//               type="password" 
//               value={password}
//               onChange={(e) => setPassword(e.target.value)}
//               className="mt-1 block w-full rounded-md border border-gray-300 p-2 shadow-sm"
//               required 
//             />
//           </div>

//           {error && <p className="text-red-500 text-sm">{error}</p>}

//           <button 
//             type="submit"
//             className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition"
//           >
//             Sign In
//           </button>
//         </form>
//       </div>
//     </div>
//   );
// }


"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from '../../utils/api';
import { GoogleLogin } from "@react-oauth/google"; // <--- Import Google Button

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const router = useRouter();

  // 1. Handle Standard Email/Password Login
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    const endpoint = isRegister ? "/users/" : "/token";
    
    try {
      let payload;
      if (isRegister) {
          payload = { email, password_hash: password, role: "user" }; // Register
          await api.post(endpoint, payload);
          alert("Account created! Please log in.");
          setIsRegister(false);
      } else {
          // Login needs URLSearchParams for OAuth2PasswordRequestForm
          const formData = new URLSearchParams();
          formData.append("username", email);
          formData.append("password", password);
          
          const res = await api.post(endpoint, formData, {
              headers: { "Content-Type": "application/x-www-form-urlencoded" }
          });
          
          localStorage.setItem("token", res.data.access_token);
          router.push("/dashboard");
      }
    } catch (err) {
      alert("Authentication failed!");
      console.error(err);
    }
  };

  // 2. Handle Google Login Success
  const handleGoogleSuccess = async (credentialResponse: any) => {
      console.log("Google ID Token:", credentialResponse.credential);
      
      try {
          // Send the Google Token to your Backend
          const res = await api.post("/auth/google", {
              token: credentialResponse.credential
          });

          // Save YOUR backend token (not the Google one)
          localStorage.setItem("token", res.data.access_token);
          router.push("/dashboard");

      } catch (err) {
          console.error("Google Login Failed on Backend", err);
          alert("Google Login failed.");
      }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-md">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          {isRegister ? "Create Account" : "Welcome Back"}
        </h2>
        
        {/* GOOGLE LOGIN BUTTON */}
        <div className="flex justify-center mb-6">
            <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => console.log('Login Failed')}
                useOneTap
            />
        </div>

        <div className="relative mb-6">
            <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
                <span className="bg-white px-2 text-gray-500">Or continue with email</span>
            </div>
        </div>

        <form onSubmit={handleAuth} className="space-y-4">
          <input
            className="w-full p-3 border rounded text-black"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <input
            className="w-full p-3 border rounded text-black"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="w-full bg-blue-600 text-white p-3 rounded hover:bg-blue-700 font-bold transition">
            {isRegister ? "Sign Up" : "Login"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          {isRegister ? "Already have an account?" : "Don't have an account?"}{" "}
          <button 
            onClick={() => setIsRegister(!isRegister)} 
            className="text-blue-600 font-bold hover:underline"
          >
            {isRegister ? "Login" : "Register"}
          </button>
        </p>
      </div>
    </div>
  );
}