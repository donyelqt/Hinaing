"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Sidebar } from "../../shared/components";
import type { ActivePage } from "../../shared/types/navigation";
import {
  BarChart3,
  TrendingUp,
  Activity,
  Users,
  AlertCircle,
  Calendar,
  Filter,
  Menu,
  X
} from "lucide-react";

type DashboardPageProps = {
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
};

export function DashboardPage({ activePage = 'dashboard', onNavigate }: DashboardPageProps = {}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile Hamburger Toggle */}
      <button
        type="button"
        onClick={() => setIsSidebarOpen((prev) => !prev)}
        className="fixed top-4 right-4 z-50 inline-flex items-center justify-center rounded-full bg-white p-3 text-slate-700 shadow-lg ring-1 ring-slate-200 hover:bg-slate-50 active:scale-95 transition-all lg:hidden"
        aria-label={isSidebarOpen ? "Close menu" : "Open menu"}
        aria-expanded={isSidebarOpen}
      >
        {isSidebarOpen ? (
          <X className="h-6 w-6" aria-hidden="true" />
        ) : (
          <Menu className="h-6 w-6" aria-hidden="true" />
        )}
      </button>

      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-0 sm:px-6 lg:flex-row lg:gap-8 lg:px-8 lg:py-10 xl:px-12">
        
        <Sidebar 
          onOpenMobileFilters={() => {}} 
          activePage={activePage}
          onNavigate={onNavigate}
          isSidebarOpen={isSidebarOpen}
          onCloseSidebar={() => setIsSidebarOpen(false)}
        />

        <main className="order-1 flex w-full flex-col gap-6 lg:order-2 lg:flex-1 lg:gap-8">
          {/* Header */}
          <div className="space-y-4">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
              <p className="text-slate-600">Monitor real-time sentiment trends across Baguio City</p>
            </div>
            
            {/* Quick Stats */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <Card className="p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-blue-500/10 p-3">
                    <BarChart3 className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-600">Total Reports</p>
                    <p className="text-2xl font-bold text-slate-900">127</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-green-500/10 p-3">
                    <TrendingUp className="h-6 w-6 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-600">Positive Trend</p>
                    <p className="text-2xl font-bold text-slate-900">+12%</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-amber-500/10 p-3">
                    <Activity className="h-6 w-6 text-amber-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-600">Active Monitoring</p>
                    <p className="text-2xl font-bold text-slate-900">24/7</p>
                  </div>
                </div>
              </Card>
              
              <Card className="p-6">
                <div className="flex items-center gap-4">
                  <div className="rounded-full bg-purple-500/10 p-3">
                    <Users className="h-6 w-6 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-600">Active Users</p>
                    <p className="text-2xl font-bold text-slate-900">1.2K</p>
                  </div>
                </div>
              </Card>
            </div>
          </div>

          {/* Main Dashboard Content */}
          <div className="grid gap-6 xl:grid-cols-[2fr_1fr]">
            {/* Main Chart Area */}
            <div className="space-y-6">
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-semibold text-slate-900">Sentiment Trends</h2>
                    <p className="text-sm text-slate-600">Last 7 days across all platforms</p>
                  </div>
                  <div className="flex gap-2">
                    <button className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">
                      <Calendar className="h-4 w-4" />
                      7 days
                    </button>
                    <button className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">
                      <Filter className="h-4 w-4" />
                      Filter
                    </button>
                  </div>
                </div>
                
                {/* Placeholder for chart */}
                <div className="h-80 rounded-lg bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                    <p className="text-slate-600 font-medium">Interactive Sentiment Chart</p>
                    <p className="text-sm text-slate-500">Chart visualization will be implemented here</p>
                  </div>
                </div>
              </Card>

              {/* Recent Activity */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
                <div className="space-y-4">
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-slate-50">
                    <div className="rounded-full bg-blue-500/10 p-2 mt-1">
                      <Activity className="h-4 w-4 text-blue-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900">New sentiment report generated</p>
                      <p className="text-xs text-slate-600">Infrastructure concerns in Session Road area</p>
                      <p className="text-xs text-slate-500 mt-1">2 minutes ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-slate-50">
                    <div className="rounded-full bg-amber-500/10 p-2 mt-1">
                      <AlertCircle className="h-4 w-4 text-amber-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900">Alert threshold reached</p>
                      <p className="text-xs text-slate-600">Water outage reports exceeding normal levels</p>
                      <p className="text-xs text-slate-500 mt-1">15 minutes ago</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-slate-50">
                    <div className="rounded-full bg-green-500/10 p-2 mt-1">
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900">Positive trend detected</p>
                      <p className="text-xs text-slate-600">Burnham Park cleanup initiative gaining traction</p>
                      <p className="text-xs text-slate-500 mt-1">1 hour ago</p>
                    </div>
                  </div>
                </div>
              </Card>
            </div>

            {/* Sidebar Content */}
            <div className="space-y-6">
              {/* Quick Actions */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button className="w-full text-left p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
                    <p className="font-medium text-slate-900">Generate New Report</p>
                    <p className="text-xs text-slate-600">Create sentiment analysis</p>
                  </button>
                  <button className="w-full text-left p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
                    <p className="font-medium text-slate-900">View All Alerts</p>
                    <p className="text-xs text-slate-600">3 active alerts</p>
                  </button>
                  <button className="w-full text-left p-3 rounded-lg border border-slate-200 hover:bg-slate-50 transition-colors">
                    <p className="font-medium text-slate-900">Export Data</p>
                    <p className="text-xs text-slate-600">Download reports</p>
                  </button>
                </div>
              </Card>

              {/* Top Issues */}
              <Card className="p-6">
                <h3 className="text-lg font-semibold text-slate-900 mb-4">Top Issues Today</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-900">Traffic Congestion</p>
                      <p className="text-xs text-slate-600">Session Road</p>
                    </div>
                    <span className="px-2 py-1 rounded-full bg-red-100 text-red-800 text-xs font-medium">
                      High
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-900">Water Supply</p>
                      <p className="text-xs text-slate-600">La Trinidad</p>
                    </div>
                    <span className="px-2 py-1 rounded-full bg-amber-100 text-amber-800 text-xs font-medium">
                      Medium
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-slate-900">Park Maintenance</p>
                      <p className="text-xs text-slate-600">Burnham Park</p>
                    </div>
                    <span className="px-2 py-1 rounded-full bg-green-100 text-green-800 text-xs font-medium">
                      Positive
                    </span>
                  </div>
                </div>
              </Card>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
