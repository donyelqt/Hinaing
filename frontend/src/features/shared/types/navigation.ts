export type NavigationItem = {
  id: string;
  label: string;
  description: string;
  href: string;
  icon: any; // Lucide icon component
  isActive: boolean;
  isDisabled?: boolean;
};

export type ActivePage = 'sentiment' | 'dashboard' | 'reports' | 'chat' | 'analyze';
