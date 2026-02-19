"use client";

import { usePathname } from "next/navigation";
import { Nav } from "./Nav";

export function ConditionalNav() {
  const pathname = usePathname();
  const isInmateRoute = pathname?.startsWith("/inmate");
  if (isInmateRoute) return null;
  return <Nav />;
}
