import React from 'react';
import './Sidebar.css';
interface SidebarProps {
    collapsed: boolean;
    currentView: string;
    onViewChange: (view: string) => void;
    onToggle: () => void;
}
declare const Sidebar: React.FC<SidebarProps>;
export default Sidebar;
