import React, { useState, useEffect, useCallback } from 'react';
import dashboardService from '../services/dashboardService';
import {
  LayoutDashboard, Activity, Bot, GitBranch, BookOpen, Server,
  TrendingUp, Zap, CheckCircle, AlertCircle, Clock, ArrowRight,
  Cpu, Boxes, Globe, Shield, Eye, ChevronRight
} from 'lucide-react';
import { Card, StatCard, Badge, StatusDot, Button, Tabs, LoadingState, PageHeader, ProgressBar } from '../components/ui/UI';

function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchOverview = useCallback(async () => {
    try {
      const resp = await dashboardService.overview();
      setOverview(resp.data);
    } catch (err) {
      console.error('Failed', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchOverview(); }, [fetchOverview]);

  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(fetchOverview, 10000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchOverview]);

  if (loading) return <LoadingState />;

  const subsystems = overview?.subsystems || {};
  const healthyCount = Object.values(subsystems).filter(s => s.status === 'healthy').length;
  const totalCount = Object.keys(subsystems).length;
  const healthPct = totalCount > 0 ? (healthyCount / totalCount) * 100 : 0;

  const quickStats = [
    { icon: Activity, label: 'System Health', value: `${healthyCount}/${totalCount}`, color: healthPct === 100 ? 'text-emerald-400' : 'text-amber-400', sublabel: `${Math.round(healthPct)}% healthy` },
    { icon: GitBranch, label: 'Pipelines', value: overview?.pipeline_stats?.total || 0, color: 'text-white', sublabel: `${overview?.pipeline_stats?.running || 0} running` },
    { icon: Bot, label: 'AI Agents', value: `${overview?.agent_stats?.enabled || 0}/${overview?.agent_stats?.total_agents || 0}`, color: 'text-teal-400', sublabel: 'active agents' },
    { icon: BookOpen, label: 'Knowledge', value: overview?.knowledge_stats?.total_entries || 0, color: 'text-cyan-400', sublabel: 'entries' },
    { icon: TrendingUp, label: 'API Requests', value: overview?.performance_stats?.total_requests || 0, color: 'text-white', sublabel: 'total requests' },
    { icon: Clock, label: 'Activity', value: overview?.activity_stats?.total_entries || 0, color: 'text-white', sublabel: 'log entries' },
  ];

  const subsystemList = Object.entries(subsystems).slice(0, 16);

  const recentActivity = overview?.recent_activity || [];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <PageHeader
        icon={LayoutDashboard}
        title="System Dashboard"
        subtitle={new Date(overview?.timestamp || '').toLocaleString()}
        actions={
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 text-xs text-gray-500 cursor-pointer">
              <input type="checkbox" checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} className="accent-teal-400" />
              Auto-refresh
            </label>
            <Button size="sm" variant="secondary" onClick={fetchOverview}>Refresh</Button>
          </div>
        }
      />

      <Tabs
        tabs={[
          { id: 'overview', label: 'Overview' },
          { id: 'subsystems', label: 'Subsystems', count: totalCount },
          { id: 'activity', label: 'Activity' },
        ]}
        active={activeTab}
        onChange={setActiveTab}
      />

      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Quick Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {quickStats.map((stat, i) => (
                <StatCard key={i} {...stat} />
              ))}
            </div>

            {/* Two-column layout */}
            <div className="grid lg:grid-cols-3 gap-4">
              {/* System Health */}
              <Card className="p-5 lg:col-span-2">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                    <Shield className="w-4 h-4 text-teal-400" />
                    Subsystem Health
                  </h3>
                  <Badge variant={healthPct === 100 ? 'success' : 'warning'}>
                    {healthyCount}/{totalCount} healthy
                  </Badge>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {subsystemList.map(([name, info]) => (
                    <div key={name} className="flex items-center gap-2 p-2.5 rounded-md bg-[#0a0a0b] border border-[#1f1f23]">
                      <StatusDot status={info.status === 'healthy' ? 'online' : info.status === 'degraded' ? 'warning' : 'error'} />
                      <span className="text-xs text-gray-400 truncate">{name}</span>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Quick Actions */}
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-teal-400" />
                  Quick Actions
                </h3>
                <div className="space-y-2">
                  {[
                    { icon: Bot, label: 'View AI Agents', path: '/agents' },
                    { icon: GitBranch, label: 'Create Pipeline', path: '/pipelines' },
                    { icon: Boxes, label: 'Verdis Blockchain', path: '/verdis' },
                    { icon: Eye, label: 'Block Explorer', path: '/block-explorer' },
                    { icon: Shield, label: 'Security Center', path: '/security' },
                  ].map((action, i) => (
                    <a key={i} href={action.path} className="flex items-center gap-3 p-2.5 rounded-md bg-[#0a0a0b] border border-[#1f1f23] hover:border-teal-400/20 hover:bg-[#161618] transition-all group">
                      <action.icon className="w-4 h-4 text-gray-500 group-hover:text-teal-400 transition-colors" />
                      <span className="text-xs text-gray-400 group-hover:text-white transition-colors">{action.label}</span>
                      <ChevronRight className="w-3.5 h-3.5 text-gray-700 group-hover:text-gray-400 ml-auto transition-colors" />
                    </a>
                  ))}
                </div>
              </Card>
            </div>

            {/* Pipeline Stats + Performance */}
            <div className="grid lg:grid-cols-2 gap-4">
              <Card className="p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <GitBranch className="w-4 h-4 text-teal-400" />
                  Pipeline Status
                </h3>
                {overview?.pipeline_stats ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Running</span>
                      <span className="text-white font-medium">{overview.pipeline_stats.running || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Completed</span>
                      <span className="text-emerald-400 font-medium">{overview.pipeline_stats.completed || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Failed</span>
                      <span className="text-red-400 font-medium">{overview.pipeline_stats.failed || 0}</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-gray-500">Total</span>
                      <span className="text-white font-medium">{overview.pipeline_stats.total || 0}</span>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-gray-600">No pipeline data</p>
                )}
              </Card>

              <Card className="p-5">
                <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-teal-400" />
                  Performance
                </h3>
                {overview?.performance_stats ? (
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span className="text-gray-500">Total Requests</span>
                        <span className="text-white font-medium">{overview.performance_stats.total_requests || 0}</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span className="text-gray-500">Avg Response Time</span>
                        <span className="text-teal-400 font-medium">{overview.performance_stats.avg_response_time || '0ms'}</span>
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <span className="text-gray-500">Error Rate</span>
                        <span className="text-gray-300 font-medium">{overview.performance_stats.error_rate || '0%'}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-gray-600">No performance data</p>
                )}
              </Card>
            </div>
          </div>
        )}

        {activeTab === 'subsystems' && (
          <div className="space-y-3">
            {subsystemList.map(([name, info]) => (
              <Card key={name} className="p-4" hover>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <StatusDot status={info.status === 'healthy' ? 'online' : info.status === 'degraded' ? 'warning' : 'error'} />
                    <div>
                      <div className="text-sm text-white font-medium">{name}</div>
                      <div className="text-xs text-gray-500">{info.message || info.status}</div>
                    </div>
                  </div>
                  <Badge variant={info.status === 'healthy' ? 'success' : info.status === 'degraded' ? 'warning' : 'danger'}>
                    {info.status}
                  </Badge>
                </div>
              </Card>
            ))}
          </div>
        )}

        {activeTab === 'activity' && (
          <Card className="p-5">
            <h3 className="text-sm font-semibold text-white mb-4">Recent Activity</h3>
            {recentActivity.length > 0 ? (
              <div className="space-y-2">
                {recentActivity.map((activity, i) => (
                  <div key={i} className="flex items-start gap-3 p-2 rounded-md hover:bg-[#161618] transition-colors">
                    <div className="w-7 h-7 rounded-md bg-teal-400/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Activity className="w-3.5 h-3.5 text-teal-400" />
                    </div>
                    <div className="flex-1">
                      <div className="text-xs text-gray-300">{activity.action || activity.description || 'Activity'}</div>
                      <div className="text-[10px] text-gray-600 mt-0.5">
                        {activity.timestamp ? new Date(activity.timestamp).toLocaleString() : ''}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gray-600 text-center py-8">No recent activity</p>
            )}
          </Card>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
