"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Sidebar } from "../../shared/components";
import type { ActivePage } from "../../shared/types/navigation";
import { 
  FileText, 
  Download, 
  Eye, 
  Calendar, 
  Filter,
  Search,
  MoreHorizontal,
  Archive,
  Share2,
  Trash2,
  Menu,
  X
} from "lucide-react";

type SavedReportsPageProps = {
  activePage?: ActivePage;
  onNavigate?: (page: ActivePage) => void;
};

const SAMPLE_REPORTS = [
  {
    id: 1,
    title: "Daily Operations Report",
    description: "Traffic, utilities, and safety updates for Nov 15, 2025",
    date: "2025-11-15",
    type: "Daily Operations",
    status: "completed",
    size: "2.4 MB",
    downloadCount: 12,
    platforms: ["Facebook", "Reddit"],
    focusAreas: ["Infrastructure", "Safety", "Environment"]
  },
  {
    id: 2,
    title: "Health Watch Analysis",
    description: "Hospital and clinic sentiment monitoring - Weekly digest",
    date: "2025-11-14",
    type: "Health Watch",
    status: "completed", 
    size: "1.8 MB",
    downloadCount: 8,
    platforms: ["Facebook"],
    focusAreas: ["Health", "Environment"]
  },
  {
    id: 3,
    title: "Tourism Pulse Report",
    description: "Visitor sentiment and events analysis for weekend",
    date: "2025-11-13",
    type: "Tourism Pulse",
    status: "processing",
    size: "3.1 MB",
    downloadCount: 25,
    platforms: ["Facebook", "Reddit"],
    focusAreas: ["Tourism", "Economy"]
  },
  {
    id: 4,
    title: "Emergency Response Alert",
    description: "Landslide risk and water outage response analysis",
    date: "2025-11-12",
    type: "Emergency",
    status: "completed",
    size: "892 KB",
    downloadCount: 45,
    platforms: ["Facebook", "Reddit"],
    focusAreas: ["Safety", "Infrastructure", "Environment"]
  },
  {
    id: 5,
    title: "Weekly Infrastructure Review",
    description: "Session Road construction impact and community feedback",
    date: "2025-11-10",
    type: "Infrastructure",
    status: "completed",
    size: "4.2 MB",
    downloadCount: 31,
    platforms: ["Facebook", "Reddit"],
    focusAreas: ["Infrastructure", "Safety"]
  }
];

export function SavedReportsPage({ activePage = 'reports', onNavigate }: SavedReportsPageProps = {}) {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 bg-grid-pattern">
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
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Saved Reports</h1>
              <p className="text-slate-600">Access and manage your generated sentiment analysis reports</p>
            </div>
            
            <div className="flex gap-3">
              <button className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">
                <Filter className="h-4 w-4" />
                Filter
              </button>
              <button className="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50">
                <Calendar className="h-4 w-4" />
                Date Range
              </button>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <Card className="p-6">
              <div className="flex items-center gap-4">
                <div className="rounded-full bg-hinaing-blue-500/10 p-3">
                  <FileText className="h-6 w-6 text-hinaing-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600">Total Reports</p>
                  <p className="text-2xl font-bold text-slate-900">{SAMPLE_REPORTS.length}</p>
                </div>
              </div>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center gap-4">
                <div className="rounded-full bg-green-500/10 p-3">
                  <Download className="h-6 w-6 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600">Total Downloads</p>
                  <p className="text-2xl font-bold text-slate-900">{SAMPLE_REPORTS.reduce((acc, report) => acc + report.downloadCount, 0)}</p>
                </div>
              </div>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center gap-4">
                <div className="rounded-full bg-amber-500/10 p-3">
                  <Archive className="h-6 w-6 text-amber-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600">This Month</p>
                  <p className="text-2xl font-bold text-slate-900">12</p>
                </div>
              </div>
            </Card>
            
            <Card className="p-6">
              <div className="flex items-center gap-4">
                <div className="rounded-full bg-purple-500/10 p-3">
                  <Eye className="h-6 w-6 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-600">Most Viewed</p>
                  <p className="text-2xl font-bold text-slate-900">45</p>
                </div>
              </div>
            </Card>
          </div>

          {/* Search and Actions */}
          <Card className="p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search reports by title, type, or date..."
                  className="w-full rounded-lg border border-slate-200 pl-10 pr-4 py-2 text-sm focus:border-hinaing-blue-500 focus:outline-none focus:ring-2 focus:ring-hinaing-blue-500/20"
                />
              </div>
              <button className="inline-flex items-center gap-2 rounded-lg bg-gradient-to-r from-hinaing-blue-600 via-hinaing-blue-500 to-violet-500 px-4 py-2 text-sm font-semibold text-white hover:brightness-110">
                <FileText className="h-4 w-4" />
                Generate New Report
              </button>
            </div>
          </Card>

          {/* Reports List */}
          <Card className="overflow-hidden">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-900">Recent Reports</h2>
            </div>
            
            <div className="divide-y divide-slate-200">
              {SAMPLE_REPORTS.map((report) => (
                <div key={report.id} className="p-6 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-3">
                        <div className="rounded-lg bg-blue-500/10 p-2 mt-1">
                          <FileText className="h-5 w-5 text-blue-600" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-semibold text-slate-900 truncate">{report.title}</h3>
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                              report.status === 'completed' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-amber-100 text-amber-800'
                            }`}>
                              {report.status}
                            </span>
                          </div>
                          <p className="text-sm text-slate-600 mb-2">{report.description}</p>
                          
                          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500">
                            <span className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              {new Date(report.date).toLocaleDateString('en-US', { 
                                year: 'numeric', 
                                month: 'short', 
                                day: 'numeric' 
                              })}
                            </span>
                            <span>Type: {report.type}</span>
                            <span>Size: {report.size}</span>
                            <span>{report.downloadCount} downloads</span>
                          </div>
                          
                          <div className="flex flex-wrap gap-2 mt-3">
                            <div className="flex gap-1">
                              <span className="text-xs font-medium text-slate-600">Platforms:</span>
                              {report.platforms.map((platform) => (
                                <span key={platform} className="px-2 py-1 rounded-full bg-slate-100 text-xs text-slate-600">
                                  {platform}
                                </span>
                              ))}
                            </div>
                            <div className="flex gap-1">
                              <span className="text-xs font-medium text-slate-600">Focus:</span>
                              {report.focusAreas.slice(0, 2).map((area) => (
                                <span key={area} className="px-2 py-1 rounded-full bg-hinaing-blue-100 text-xs text-hinaing-blue-700">
                                  {area}
                                </span>
                              ))}
                              {report.focusAreas.length > 2 && (
                                <span className="px-2 py-1 rounded-full bg-slate-100 text-xs text-slate-600">
                                  +{report.focusAreas.length - 2} more
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button className="p-2 text-slate-400 hover:text-hinaing-blue-600 hover:bg-hinaing-blue-50 rounded-lg transition-colors">
                        <Eye className="h-4 w-4" />
                      </button>
                      <button className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 rounded-lg transition-colors">
                        <Download className="h-4 w-4" />
                      </button>
                      <button className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                        <Share2 className="h-4 w-4" />
                      </button>
                      <button className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                        <Trash2 className="h-4 w-4" />
                      </button>
                      <button className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                        <MoreHorizontal className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="p-6 border-t border-slate-200 bg-slate-50">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-600">
                  Showing {SAMPLE_REPORTS.length} of {SAMPLE_REPORTS.length} reports
                </p>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-sm text-slate-600 hover:text-slate-900">Previous</button>
                  <button className="px-3 py-1 text-sm text-slate-600 hover:text-slate-900">Next</button>
                </div>
              </div>
            </div>
          </Card>
        </main>
      </div>
    </div>
  );
}
