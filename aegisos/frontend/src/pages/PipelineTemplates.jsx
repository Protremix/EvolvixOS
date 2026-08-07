import React, { useState, useEffect, useCallback } from 'react';
import templateService from '../services/pipelineTemplateService';

function PipelineTemplates() {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [tplResp, catResp, notifResp] = await Promise.all([
        templateService.list(selectedCategory),
        templateService.categories(),
        templateService.getNotifications(false),
      ]);
      setTemplates(tplResp.data);
      setCategories(catResp.data);
      setNotifications(notifResp.data.notifications || []);
      setUnreadCount(notifResp.data.unread_count || 0);
    } catch (err) { console.error('Failed to load', err); }
    finally { setLoading(false); }
  }, [selectedCategory]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleCreatePipeline = async (templateId, title, description) => {
    try {
      await templateService.createPipeline(templateId, title, description);
      alert('Pipeline created! Check the Feature Pipeline page to execute it.');
    } catch (err) { console.error('Failed', err); }
  };

  const handleMarkAllRead = async () => {
    await templateService.markAllRead();
    fetchAll();
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading templates...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, margin: 0 }}>Pipeline Templates</h1>
          <p style={{ color: '#888', marginTop: '4px' }}>
            Pre-configured pipelines for common feature types
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {unreadCount > 0 && (
            <button onClick={handleMarkAllRead} style={{ ...btnSmall, background: '#3D2A0D', color: '#FFA500' }}>
              🔔 {unreadCount} unread
            </button>
          )}
          <button onClick={() => setShowCreate(!showCreate)} style={btnPrimary}>
            {showCreate ? 'Cancel' : '+ Custom Template'}
          </button>
        </div>
      </div>

      {/* Category Filter */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button onClick={() => setSelectedCategory(null)} style={selectedCategory === null ? catActive : catBtn}>All</button>
        {categories.map(cat => (
          <button key={cat.name} onClick={() => setSelectedCategory(cat.name)} style={selectedCategory === cat.name ? catActive : catBtn}>
            {cat.name} ({cat.count})
          </button>
        ))}
      </div>

      {showCreate && <CreateTemplateForm onCreate={async (tpl) => { await templateService.create(tpl); setShowCreate(false); fetchAll(); }} />}

      {/* Template Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '16px' }}>
        {templates.map(tpl => (
          <TemplateCard key={tpl.id} template={tpl} onCreatePipeline={handleCreatePipeline} />
        ))}
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h2 style={{ fontSize: '20px', marginBottom: '12px' }}>Notifications ({unreadCount} unread)</h2>
          <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '12px', maxHeight: '300px', overflowY: 'auto' }}>
            {notifications.slice().reverse().map((n, i) => (
              <div key={i} style={{
                padding: '8px', marginBottom: '4px', borderRadius: '6px',
                background: n.read ? 'transparent' : '#0D0D0F',
                borderLeft: `3px solid ${notifColor(n.severity)}`,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontWeight: 600, color: notifColor(n.severity) }}>{n.title}</span>
                  <span style={{ fontSize: '11px', color: '#666' }}>{new Date(n.created_at).toLocaleString()}</span>
                </div>
                <div style={{ fontSize: '13px', color: '#999', marginTop: '4px' }}>{n.message}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function TemplateCard({ template, onCreatePipeline }) {
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');

  const complexityColors = { low: '#22C55E', medium: '#FFA500', high: '#FF6B6B', critical: '#EF4444' };
  const priorityColors = { low: '#666', medium: '#FFA500', high: '#FF6B6B', critical: '#EF4444' };

  return (
    <div style={{ background: '#1A1A1E', borderRadius: '10px', padding: '20px', border: '1px solid #333' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
        <div>
          <span style={{ fontSize: '24px' }}>{template.icon}</span>
          <span style={{ fontSize: '18px', fontWeight: 700, marginLeft: '8px' }}>{template.name}</span>
        </div>
        <div style={{ display: 'flex', gap: '4px', flexDirection: 'column', alignItems: 'flex-end' }}>
          <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: complexityColors[template.complexity] + '22', color: complexityColors[template.complexity] }}>{template.complexity}</span>
          <span style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: priorityColors[template.default_priority] + '22', color: priorityColors[template.default_priority] }}>{template.default_priority}</span>
        </div>
      </div>
      <p style={{ fontSize: '13px', color: '#888', marginBottom: '12px' }}>{template.description}</p>

      <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#666', marginBottom: '8px' }}>
        <span>⏱ {template.estimated_duration_hours}h</span>
        {template.skip_stages.length > 0 && <span>⏭ skips {template.skip_stages.length}</span>}
        <span>📦 {template.default_project_type}</span>
      </div>

      {template.default_constraints.length > 0 && (
        <div style={{ marginBottom: '8px' }}>
          <div style={{ fontSize: '11px', color: '#666', marginBottom: '4px' }}>Constraints:</div>
          {template.default_constraints.slice(0, 3).map((c, i) => (
            <div key={i} style={{ fontSize: '12px', color: '#FFA500' }}>• {c}</div>
          ))}
        </div>
      )}

      {template.tags.length > 0 && (
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap', marginBottom: '12px' }}>
          {template.tags.map((tag, i) => (
            <span key={i} style={{ fontSize: '10px', padding: '2px 6px', background: '#2A2A2E', borderRadius: '4px', color: '#888' }}>{tag}</span>
          ))}
        </div>
      )}

      {showForm ? (
        <div>
          <input placeholder="Feature title" value={title} onChange={e => setTitle(e.target.value)} style={{ ...inputStyle, width: '100%', marginBottom: '8px' }} />
          <textarea placeholder="Description" value={desc} onChange={e => setDesc(e.target.value)} style={{ ...inputStyle, width: '100%', minHeight: '60px', marginBottom: '8px', resize: 'vertical' }} />
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={() => onCreatePipeline(template.id, title, desc)} style={btnSmall}>Create Pipeline</button>
            <button onClick={() => setShowForm(false)} style={{ ...btnSmall, background: '#333' }}>Cancel</button>
          </div>
        </div>
      ) : (
        <button onClick={() => setShowForm(true)} style={{ ...btnSmall, width: '100%' }}>Use Template</button>
      )}
    </div>
  );
}

function CreateTemplateForm({ onCreate }) {
  const [tpl, setTpl] = useState({ id: '', name: '', description: '', category: 'general', default_priority: 'medium', complexity: 'medium' });

  return (
    <form onSubmit={e => { e.preventDefault(); onCreate(tpl); }} style={{ background: '#1A1A1E', padding: '20px', borderRadius: '10px', marginBottom: '24px' }}>
      <h2 style={{ fontSize: '18px', marginBottom: '12px' }}>Create Custom Template</h2>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <input placeholder="Template ID" value={tpl.id} onChange={e => setTpl({...tpl, id: e.target.value})} style={inputStyle} required />
        <input placeholder="Template Name" value={tpl.name} onChange={e => setTpl({...tpl, name: e.target.value})} style={inputStyle} required />
      </div>
      <input placeholder="Description" value={tpl.description} onChange={e => setTpl({...tpl, description: e.target.value})} style={{ ...inputStyle, width: '100%', marginTop: '12px' }} required />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
        <select value={tpl.category} onChange={e => setTpl({...tpl, category: e.target.value})} style={inputStyle}>
          <option value="general">General</option><option value="bugfix">Bugfix</option><option value="feature">Feature</option><option value="infra">Infrastructure</option><option value="security">Security</option>
        </select>
        <select value={tpl.complexity} onChange={e => setTpl({...tpl, complexity: e.target.value})} style={inputStyle}>
          <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
        </select>
      </div>
      <button type="submit" style={{ marginTop: '12px', ...btnPrimary }}>Create Template</button>
    </form>
  );
}

function notifColor(severity) {
  const colors = { info: '#4F46E5', success: '#22C55E', warning: '#FFA500', error: '#EF4444' };
  return colors[severity] || '#888';
}

const inputStyle = { padding: '8px 12px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '6px', color: '#fff', fontSize: '14px' };
const btnPrimary = { padding: '8px 16px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer' };
const btnSmall = { padding: '6px 12px', background: '#4F46E5', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };
const catBtn = { padding: '6px 14px', background: '#1A1A1E', border: '1px solid #333', borderRadius: '6px', color: '#888', cursor: 'pointer', fontSize: '13px' };
const catActive = { ...catBtn, background: '#4F46E5', color: '#fff', border: '1px solid #4F46E5' };

export default PipelineTemplates;
