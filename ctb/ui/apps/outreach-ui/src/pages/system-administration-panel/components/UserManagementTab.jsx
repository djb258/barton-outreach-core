import React, { useState, useMemo } from 'react';
import Icon from '../../../components/AppIcon';
import Button from '../../../components/ui/Button';
import Input from '../../../components/ui/Input';
import Select from '../../../components/ui/Select';
import { Checkbox } from '../../../components/ui/Checkbox';

const UserManagementTab = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [sortField, setSortField] = useState('name');
  const [sortDirection, setSortDirection] = useState('asc');

  // Mock user data
  const users = [
    {
      id: 1,
      name: "Sarah Johnson",
      email: "sarah.johnson@company.com",
      role: "admin",
      permissions: ["read", "write", "admin"],
      lastActivity: "2025-09-19T14:30:00Z",
      status: "active",
      avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b786?w=150&h=150&fit=crop&crop=face"
    },
    {
      id: 2,
      name: "Michael Chen",
      email: "michael.chen@company.com",
      role: "manager",
      permissions: ["read", "write"],
      lastActivity: "2025-09-19T13:45:00Z",
      status: "active",
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face"
    },
    {
      id: 3,
      name: "Emily Rodriguez",
      email: "emily.rodriguez@company.com",
      role: "analyst",
      permissions: ["read"],
      lastActivity: "2025-09-19T12:15:00Z",
      status: "active",
      avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face"
    },
    {
      id: 4,
      name: "David Thompson",
      email: "david.thompson@company.com",
      role: "manager",
      permissions: ["read", "write"],
      lastActivity: "2025-09-18T16:20:00Z",
      status: "inactive",
      avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
    },
    {
      id: 5,
      name: "Lisa Wang",
      email: "lisa.wang@company.com",
      role: "analyst",
      permissions: ["read"],
      lastActivity: "2025-09-19T11:30:00Z",
      status: "active",
      avatar: "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=150&h=150&fit=crop&crop=face"
    }
  ];

  const roleOptions = [
    { value: '', label: 'All Roles' },
    { value: 'admin', label: 'Administrator' },
    { value: 'manager', label: 'Manager' },
    { value: 'analyst', label: 'Analyst' }
  ];

  const filteredUsers = useMemo(() => {
    return users?.filter(user => {
      const matchesSearch = user?.name?.toLowerCase()?.includes(searchTerm?.toLowerCase()) ||
                           user?.email?.toLowerCase()?.includes(searchTerm?.toLowerCase());
      const matchesRole = !selectedRole || user?.role === selectedRole;
      return matchesSearch && matchesRole;
    })?.sort((a, b) => {
      const aValue = a?.[sortField];
      const bValue = b?.[sortField];
      const direction = sortDirection === 'asc' ? 1 : -1;
      return aValue < bValue ? -direction : aValue > bValue ? direction : 0;
    });
  }, [users, searchTerm, selectedRole, sortField, sortDirection]);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const handleSelectUser = (userId) => {
    setSelectedUsers(prev => 
      prev?.includes(userId) 
        ? prev?.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    if (selectedUsers?.length === filteredUsers?.length) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(filteredUsers?.map(user => user?.id));
    }
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-primary text-primary-foreground';
      case 'manager': return 'bg-accent text-accent-foreground';
      case 'analyst': return 'bg-secondary text-secondary-foreground';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getStatusColor = (status) => {
    return status === 'active' ? 'text-success' : 'text-muted-foreground';
  };

  const formatLastActivity = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffHours = Math.floor((now - date) / (1000 * 60 * 60));
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    return date?.toLocaleDateString();
  };

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex flex-col sm:flex-row gap-4 flex-1">
          <Input
            type="search"
            placeholder="Search users by name or email..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e?.target?.value)}
            className="flex-1 max-w-md"
          />
          <Select
            options={roleOptions}
            value={selectedRole}
            onChange={setSelectedRole}
            placeholder="Filter by role"
            className="w-full sm:w-48"
          />
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" iconName="Download" iconPosition="left">
            Export
          </Button>
          <Button variant="default" iconName="Plus" iconPosition="left">
            Add User
          </Button>
        </div>
      </div>
      {/* Bulk Actions */}
      {selectedUsers?.length > 0 && (
        <div className="flex items-center justify-between p-4 bg-accent/10 border border-accent/20 rounded-lg">
          <span className="text-sm font-medium text-accent">
            {selectedUsers?.length} user{selectedUsers?.length > 1 ? 's' : ''} selected
          </span>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" iconName="Mail">
              Send Email
            </Button>
            <Button variant="outline" size="sm" iconName="Settings">
              Update Roles
            </Button>
            <Button variant="destructive" size="sm" iconName="Trash2">
              Deactivate
            </Button>
          </div>
        </div>
      )}
      {/* Users Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50 border-b border-border">
              <tr>
                <th className="w-12 p-4">
                  <Checkbox
                    checked={selectedUsers?.length === filteredUsers?.length && filteredUsers?.length > 0}
                    onChange={handleSelectAll}
                    indeterminate={selectedUsers?.length > 0 && selectedUsers?.length < filteredUsers?.length}
                  />
                </th>
                <th className="text-left p-4 font-medium text-foreground">
                  <button
                    onClick={() => handleSort('name')}
                    className="flex items-center space-x-1 hover:text-accent transition-colors"
                  >
                    <span>User</span>
                    <Icon name="ArrowUpDown" size={14} />
                  </button>
                </th>
                <th className="text-left p-4 font-medium text-foreground">
                  <button
                    onClick={() => handleSort('role')}
                    className="flex items-center space-x-1 hover:text-accent transition-colors"
                  >
                    <span>Role</span>
                    <Icon name="ArrowUpDown" size={14} />
                  </button>
                </th>
                <th className="text-left p-4 font-medium text-foreground">Permissions</th>
                <th className="text-left p-4 font-medium text-foreground">
                  <button
                    onClick={() => handleSort('lastActivity')}
                    className="flex items-center space-x-1 hover:text-accent transition-colors"
                  >
                    <span>Last Activity</span>
                    <Icon name="ArrowUpDown" size={14} />
                  </button>
                </th>
                <th className="text-left p-4 font-medium text-foreground">Status</th>
                <th className="w-24 p-4 font-medium text-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers?.map((user) => (
                <tr key={user?.id} className="border-b border-border hover:bg-muted/30 transition-colors">
                  <td className="p-4">
                    <Checkbox
                      checked={selectedUsers?.includes(user?.id)}
                      onChange={() => handleSelectUser(user?.id)}
                    />
                  </td>
                  <td className="p-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-full overflow-hidden bg-muted">
                        <img
                          src={user?.avatar}
                          alt={user?.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            e.target.src = '/assets/images/no_image.png';
                          }}
                        />
                      </div>
                      <div>
                        <div className="font-medium text-foreground">{user?.name}</div>
                        <div className="text-sm text-muted-foreground">{user?.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(user?.role)}`}>
                      {user?.role?.charAt(0)?.toUpperCase() + user?.role?.slice(1)}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-1">
                      {user?.permissions?.map((permission) => (
                        <span
                          key={permission}
                          className="inline-flex items-center px-2 py-1 rounded text-xs bg-muted text-muted-foreground"
                        >
                          {permission}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="p-4">
                    <span className="text-sm text-muted-foreground">
                      {formatLastActivity(user?.lastActivity)}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${user?.status === 'active' ? 'bg-success' : 'bg-muted-foreground'}`} />
                      <span className={`text-sm font-medium ${getStatusColor(user?.status)}`}>
                        {user?.status?.charAt(0)?.toUpperCase() + user?.status?.slice(1)}
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center space-x-1">
                      <Button variant="ghost" size="icon" iconName="Edit" />
                      <Button variant="ghost" size="icon" iconName="MoreHorizontal" />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          Showing {filteredUsers?.length} of {users?.length} users
        </div>
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" iconName="ChevronLeft" disabled>
            Previous
          </Button>
          <Button variant="outline" size="sm" iconName="ChevronRight" disabled>
            Next
          </Button>
        </div>
      </div>
    </div>
  );
};

export default UserManagementTab;