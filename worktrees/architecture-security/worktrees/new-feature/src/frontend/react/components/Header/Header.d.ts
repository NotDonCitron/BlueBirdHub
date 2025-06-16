import React from 'react';
import './Header.css';
interface HeaderProps {
    currentView: string;
    apiStatus: 'connected' | 'disconnected' | 'checking';
    onSidebarToggle: () => void;
}
declare const Header: React.FC<HeaderProps>;
export default Header;
