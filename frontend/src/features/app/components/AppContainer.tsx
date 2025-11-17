"use client";

import { useState, useEffect } from "react";
import type { ActivePage } from "../../shared/types/navigation";
import { SentimentGeneratorPage } from "../../sentiment/components/sentiment-generator-page";
import { DashboardPage } from "../../dashboard/components/DashboardPage";
import { SavedReportsPage } from "../../reports/components/SavedReportsPage";

export function AppContainer() {
  // Get initial page from URL
  const getInitialPage = (): ActivePage => {
    if (typeof window === 'undefined') return 'sentiment';
    const path = window.location.pathname;
    if (path.includes('/dashboard')) return 'dashboard';
    if (path.includes('/reports')) return 'reports';
    return 'sentiment';
  };

  const [activePage, setActivePage] = useState<ActivePage>(getInitialPage);
  
  console.log('🚀 AppContainer Debug - Current activePage:', activePage);

  // Handle navigation with URL updates
  const handleNavigate = (page: ActivePage) => {
    setActivePage(page);
    
    // Update browser URL
    const newUrl = page === 'sentiment' ? '/' : `/${page}`;
    window.history.pushState({}, '', newUrl);
  };

  // Handle browser back/forward buttons
  useEffect(() => {
    const handlePopState = () => {
      setActivePage(getInitialPage());
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const renderActivePage = () => {
    switch (activePage) {
      case 'sentiment':
        return <SentimentGeneratorPage activePage={activePage} onNavigate={handleNavigate} />;
      case 'dashboard':
        return <DashboardPage activePage={activePage} onNavigate={handleNavigate} />;
      case 'reports':
        return <SavedReportsPage activePage={activePage} onNavigate={handleNavigate} />;
      default:
        return <SentimentGeneratorPage activePage={activePage} onNavigate={handleNavigate} />;
    }
  };

  return (
    <div>
      {renderActivePage()}
    </div>
  );
}
