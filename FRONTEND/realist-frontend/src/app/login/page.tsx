"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import NeuronParticles from "@/components/ui/Particles";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleLogin(e: any) {
    e.preventDefault();
    setError("");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!res.ok) {
        const msg = await res.text();
        setError(msg || "Login failed");
        return;
      }

      const data = await res.json();

      // Store JWT + user info
      localStorage.setItem("token", data.token);
      localStorage.setItem("userId", data.userId);
      localStorage.setItem("displayName", data.displayName);

      router.push("/hub");
    } catch (err) {
      setError("Network error");
    }
  }

  return (
    <section className="relative w-full min-h-screen bg-black text-white flex items-center justify-center px-6">

      <NeuronParticles id="loginParticles" className="fixed inset-0 z-0" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md p-8 rounded-2xl bg-[#0A0A0A]/80 border border-[#4CC9F0]/30 shadow-[0_0_30px_rgba(76,201,240,0.3)]"
      >
        <div className="flex justify-center mb-6">
          <Image src="/Realistlogo.png" alt="Realist Logo" width={70} height={70} />
        </div>

        <h2 className="text-3xl font-bold text-center mb-2">Welcome</h2>
        <p className="text-center text-[#A8DADC] mb-8">Connect with the Global Community</p>

        {error && (
          <p className="text-red-400 text-center mb-4">{error}</p>
        )}

        <form onSubmit={handleLogin} className="space-y-5">
          <input
            type="email"
            placeholder="Email"
            className="w-full p-3 rounded-lg bg-black border border-[#4CC9F0]/40 text-white"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <input
            type="password"
            placeholder="Password"
            className="w-full p-3 rounded-lg bg-black border border-[#4CC9F0]/40 text-white"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          <button
            type="submit"
            className="w-full py-3 rounded-lg bg-[#4CC9F0] text-black font-semibold hover:bg-[#72EFDD] transition"
          >
            Login
          </button>
        </form>

        <p className="text-center text-[#A8DADC] mt-6">
          Don’t have an account?{" "}
          <a href="/register" className="text-[#4CC9F0] hover:text-white">
            Register
          </a>
        </p>
      </motion.div>
    </section>
  );
}
