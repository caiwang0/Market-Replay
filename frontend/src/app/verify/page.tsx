"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { verifyMagicLink } from "@/api/auth";
import { PATHS } from "@/constants/fe_config";

export default function VerifyMagicLinkPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email");
  const verifyToken = searchParams.get("verifyToken");

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");

  useEffect(() => {
    const verify = async () => {
      if (!email || !verifyToken) {
        setStatus("error");
        return;
      }

      try {
        const res = await verifyMagicLink(email, verifyToken);
        if (!res.ok) {
          setStatus("error");
          return;
        }

        setStatus("success");

        // Wait a moment to show success message, then redirect
        setTimeout(() => {
          router.push(PATHS.CHAT_HOME);
        }, 1000);
      } catch (err) {
        console.error(err);
        setStatus("error");
      }
    };

    verify();
  }, [email, verifyToken]);

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-5 p-8 rounded-lg border space-y-6 border-gray-800">
        {status === "verifying" && (
          <>
            <h1 className="text-3xl font-bold text-center">Verifying your link...</h1>
            <p className="text-center text-sm text-gray-400">Please wait.</p>
          </>
        )}

        {status === "success" && (
          <>
            <h1 className="text-3xl font-bold text-center">✅ You're verified!</h1>
            <p className="text-center text-sm text-gray-400">Redirecting to your dashboard...</p>
          </>
        )}

        {status === "error" && (
          <>
            <h1 className="text-3xl font-bold text-center text-red-600">Invalid or expired link</h1>
            <p className="text-center text-sm text-gray-400">
              Please try signing in again from the{" "}
              <a href="/signin" className="text-blue-600 hover:underline">
                login page
              </a>.
            </p>
          </>
        )}
      </div>
    </div>
  );
}