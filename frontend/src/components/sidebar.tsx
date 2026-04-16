"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore, useUIStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  HiOutlineChartPie,
  HiOutlineChatBubbleLeftRight,
  HiOutlineShieldCheck,
  HiOutlineBanknotes,
  HiOutlineBriefcase,
  HiOutlineBeaker,
  HiOutlineArrowRightOnRectangle,
  HiOutlineBars3,
  HiOutlineXMark,
} from "react-icons/hi2";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: HiOutlineChartPie },
  { href: "/ask", label: "Ask Engine", icon: HiOutlineChatBubbleLeftRight },
  { href: "/loans", label: "Loans", icon: HiOutlineBanknotes },
  { href: "/portfolio", label: "Portfolio", icon: HiOutlineBriefcase },
  { href: "/insurance", label: "Insurance", icon: HiOutlineShieldCheck },
  { href: "/scenarios", label: "Scenarios", icon: HiOutlineBeaker },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const { user, logout } = useAuthStore();

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 left-0 h-screen z-50 flex flex-col",
          "bg-surface-900/95 backdrop-blur-xl border-r border-white/[0.06]",
          "transition-all duration-300 ease-in-out",
          sidebarOpen ? "w-64" : "w-0 lg:w-20",
          !sidebarOpen && "overflow-hidden lg:overflow-visible"
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-white/[0.06]">
          {sidebarOpen && (
            <Link href="/dashboard" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-600 flex items-center justify-center shadow-glow">
                <span className="text-white font-bold text-sm">FI</span>
              </div>
              <span className="text-white font-bold text-lg tracking-tight">
                Fin<span className="text-brand-400">Engine</span>
              </span>
            </Link>
          )}
          <button
            id="sidebar-toggle"
            onClick={toggleSidebar}
            className="p-1.5 rounded-lg hover:bg-white/[0.05] text-gray-400 hover:text-white transition-colors"
          >
            {sidebarOpen ? (
              <HiOutlineXMark className="w-5 h-5" />
            ) : (
              <HiOutlineBars3 className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                id={`nav-${item.label.toLowerCase().replace(/\s/g, "-")}`}
                className={cn(
                  "nav-link group",
                  isActive && "nav-link-active"
                )}
              >
                <item.icon
                  className={cn(
                    "w-5 h-5 flex-shrink-0",
                    isActive ? "text-brand-400" : "text-gray-500 group-hover:text-gray-300"
                  )}
                />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-white/[0.06] p-3">
          {sidebarOpen && user && (
            <div className="px-3 py-2 mb-2">
              <p className="text-sm font-medium text-gray-200 truncate">
                {user.full_name}
              </p>
              <p className="text-xs text-gray-500 truncate">{user.email}</p>
            </div>
          )}
          <button
            id="logout-btn"
            onClick={logout}
            className="nav-link w-full text-rose-400/80 hover:text-rose-400 hover:bg-rose-500/10"
          >
            <HiOutlineArrowRightOnRectangle className="w-5 h-5" />
            {sidebarOpen && <span>Sign Out</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
