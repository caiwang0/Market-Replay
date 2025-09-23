"use client";

import Link from "next/link";
import { PATHS } from "@/constants/fe_config";

export default function WaitingPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-5 p-8 rounded-lg border space-y-6 border-gray-800">
        <h1 className="text-3xl font-bold text-center">Check Your Lark Messages</h1>
        <p className="text-center">
          We've sent a magic link to your Lark.<br />
          Please click the link to verify your email and log in.
        </p>

        <div className="text-center text-sm text-gray-400">
          Didn't get the message? Please wait a while or{" "}
          <Link href={ PATHS.LOGIN } className="text-blue-600 hover:underline">
            try again
          </Link>
          .
        </div>
      </div>
    </div>
  );
}

