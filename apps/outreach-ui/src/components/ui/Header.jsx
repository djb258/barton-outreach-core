import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Icon from '../AppIcon';
import Button from './Button';

const Header = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const location = useLocation();

  const navigationItems = [
    {
      label: 'Data Intake',
      path: '/data-intake-dashboard',
      icon: 'Database',
      roles: ['admin', 'analyst', 'manager'],
      tooltip: 'Manage data intake operations'
    },
    {
      label: 'Data Validation',
      path: '/data-validation-console',
      icon: 'CheckCircle',
      roles: ['admin', 'analyst', 'manager'],
      tooltip: 'Validate and process data'
    },
    {
      label: 'Administration',
      path: '/system-administration-panel',
      icon: 'Settings',
      roles: ['admin'],
      tooltip: 'System administration panel'
    }
  ];

  const isActivePath = (path) => {
    return location?.pathname === path;
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-[1000] bg-card border-b border-border shadow-elevation-1">
      <div className="flex items-center justify-between h-16 px-6">
        {/* Logo Section */}
        <div className="flex items-center">
          <Link to="/" className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-md">
              <Icon name="Workflow" size={20} color="white" />
            </div>
            <div className="flex flex-col">
              <span className="text-lg font-semibold text-foreground leading-tight">
                Outreach Process
              </span>
              <span className="text-xs text-muted-foreground leading-tight">
                Manager
              </span>
            </div>
          </Link>
        </div>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex items-center space-x-1">
          {navigationItems?.map((item) => (
            <Link
              key={item?.path}
              to={item?.path}
              className={`
                flex items-center space-x-2 px-4 py-2 rounded-md text-sm font-medium
                transition-all duration-200 ease-micro
                ${isActivePath(item?.path)
                  ? 'bg-accent text-accent-foreground shadow-elevation-1'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                }
              `}
              title={item?.tooltip}
            >
              <Icon name={item?.icon} size={16} />
              <span>{item?.label}</span>
            </Link>
          ))}
        </nav>

        {/* Workflow Progress Tracker */}
        <div className="hidden lg:flex items-center space-x-4">
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-muted rounded-md">
            <Icon name="Activity" size={14} color="var(--color-muted-foreground)" />
            <span className="text-xs font-data text-muted-foreground">
              ID: WF-2025-001
            </span>
          </div>
          <div className="flex items-center space-x-2 px-3 py-1.5 bg-success/10 text-success rounded-md">
            <Icon name="CheckCircle" size={14} />
            <span className="text-xs font-medium">
              Step 2/9
            </span>
          </div>
        </div>

        {/* User Actions */}
        <div className="flex items-center space-x-2">
          <div className="hidden sm:flex items-center space-x-2">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse-gentle" title="System Online" />
            <span className="text-xs text-muted-foreground">Online</span>
          </div>
          
          {/* Mobile Menu Button */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMenu}
            className="md:hidden"
            aria-label="Toggle navigation menu"
          >
            <Icon name={isMenuOpen ? "X" : "Menu"} size={20} />
          </Button>
        </div>
      </div>
      {/* Mobile Navigation Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-card border-t border-border shadow-elevation-2 animate-slide-in">
          <nav className="px-4 py-3 space-y-1">
            {navigationItems?.map((item) => (
              <Link
                key={item?.path}
                to={item?.path}
                onClick={() => setIsMenuOpen(false)}
                className={`
                  flex items-center space-x-3 px-3 py-2.5 rounded-md text-sm font-medium
                  transition-all duration-200 ease-micro
                  ${isActivePath(item?.path)
                    ? 'bg-accent text-accent-foreground'
                    : 'text-muted-foreground hover:text-foreground hover:bg-muted'
                  }
                `}
              >
                <Icon name={item?.icon} size={18} />
                <span>{item?.label}</span>
              </Link>
            ))}
            
            {/* Mobile Workflow Info */}
            <div className="pt-3 mt-3 border-t border-border">
              <div className="flex items-center justify-between px-3 py-2">
                <div className="flex items-center space-x-2">
                  <Icon name="Activity" size={14} color="var(--color-muted-foreground)" />
                  <span className="text-xs font-data text-muted-foreground">
                    WF-2025-001
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-success">
                  <Icon name="CheckCircle" size={14} />
                  <span className="text-xs font-medium">Step 2/9</span>
                </div>
              </div>
            </div>
          </nav>
        </div>
      )}
    </header>
  );
};

export default Header;