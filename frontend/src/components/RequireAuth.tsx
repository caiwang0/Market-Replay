"use client";

import { checkSession } from "@/api/auth";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { PATHS, PUBLIC_PATHS } from "@/constants/fe_config";

export default function RequireAuth({ children }: { children: React.ReactNode }) {
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // need to adjust the /agent in frontt
    if (PUBLIC_PATHS.includes(pathname)) {
      setLoading(false);
      return;
    }

    const checkAuth = async () => {
      try {
        const res = await checkSession();
        if (!res.ok) {
          router.push(PATHS.LOGIN);
        }
      } catch {
        router.push(PATHS.LOGIN);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [pathname, router]);

  if (loading) return <p className="text-center mt-10">Checking authentication...</p>;
  return <>{children}</>;
}