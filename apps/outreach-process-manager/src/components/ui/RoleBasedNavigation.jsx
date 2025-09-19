import React, { useContext } from 'react';
import { Link, useLocation } from 'react-router-dom';
import Icon from '../AppIcon';

// Mock user context - replace with actual auth context
const UserContext = React.createContext({
  user: { role: 'admin', permissions: ['read', 'write', 'admin'] }
});

const RoleBasedNavigation = ({ className = '' }) => {
  const { user } = useContext(UserContext);
  const location = useLocation();

  const navigationItems = [
    {
      label: 'Data Intake Dashboard',
      path: '/data-intake-dashboard',
      icon: 'Database',
      roles: ['admin', 'analyst', 'manager'],
      permissions: ['read'],
      tooltip: 'Manage data intake operations and monitor ingestion status',
      category: 'workflow'
    },
    {
      label: 'Data Validation Console',
      path: '/data-validation-console',
      icon: 'CheckCircle',
      roles: ['admin', 'analyst', 'manager'],
      permissions: ['read', 'write'],
      tooltip: 'Validate data quality and process validation rules',
      category: 'workflow'
    },
    {
      label: 'System Administration',
      path: '/system-administration-panel',
      icon: 'Settings',
      roles: ['admin'],
      permissions: ['admin'],
      tooltip: 'Configure system settings and manage user access',
      category: 'administration'
    }
  ];

  const hasAccess = (item) => {
    // Check role-based access
    const hasRole = item?.roles?.includes(user?.role);
    
    // Check permission-based access
    const hasPermission = item?.permissions?.some(permission => 
      user?.permissions?.includes(permission)
    );
    
    return hasRole && hasPermission;
  };

  const isActivePath = (path) => {
    return location?.pathname === path;
  };

  const getVisibleItems = () => {
    return navigationItems?.filter(hasAccess);
  };

  const groupItemsByCategory = (items) => {
    return items?.reduce((groups, item) => {
      const category = item?.category || 'general';
      if (!groups?.[category]) {
        groups[category] = [];
      }
      groups?.[category]?.push(item);
      return groups;
    }, {});
  };

  const visibleItems = getVisibleItems();
  const groupedItems = groupItemsByCategory(visibleItems);

  if (visibleItems?.length === 0) {
    return (
      <div className={`flex items-center justify-center p-4 ${className}`}>
        <div className="text-sm text-muted-foreground">
          No accessible navigation items
        </div>
      </div>
    );
  }

  return (
    <nav className={`flex items-center space-x-1 ${className}`}>
      {/* Workflow Items */}
      {groupedItems?.workflow?.map((item) => (
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
          <span className="hidden lg:inline">{item?.label}</span>
          <span className="lg:hidden">{item?.label?.split(' ')?.[0]}</span>
        </Link>
      ))}
      {/* Separator for different categories */}
      {groupedItems?.workflow && groupedItems?.administration && (
        <div className="w-px h-6 bg-border mx-2" />
      )}
      {/* Administration Items */}
      {groupedItems?.administration?.map((item) => (
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
          <span className="hidden lg:inline">{item?.label}</span>
          <span className="lg:hidden">Admin</span>
        </Link>
      ))}
      {/* Role Indicator */}
      {user?.role && (
        <div className="hidden xl:flex items-center space-x-2 ml-4 px-3 py-1.5 bg-primary/10 text-primary rounded-md">
          <Icon name="User" size={12} />
          <span className="text-xs font-medium capitalize">
            {user?.role}
          </span>
        </div>
      )}
    </nav>
  );
};

// Provider component for user context
export const UserProvider = ({ children, user = { role: 'admin', permissions: ['read', 'write', 'admin'] } }) => {
  return (
    <UserContext.Provider value={{ user }}>
      {children}
    </UserContext.Provider>
  );
};

export default RoleBasedNavigation;