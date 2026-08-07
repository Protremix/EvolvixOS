import React, { useState, useEffect, useCallback } from 'react';
import systemSettingsService from '../services/systemSettingsService';

function SystemSettings() {
  const [settings, setSettings] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    try {
      const [settingsResp, catsResp] = await Promise.all([
        systemSettingsService.list(selectedCategory || undefined),
        systemSettingsService.categories(),
      ]);
      setSettings(settingsResp.data);
      setCategories(catsResp.data);
    } catch (err) { console.error('Failed', err); }
    finally { setLoading(false); }
  }, [selectedCategory]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleSave = async (key, value) => {
    try {
      await systemSettingsService.set(key, value);
      setEditing(null);
      fetchAll();
    } catch (err) { alert('Failed: ' + (err.response?.data?.detail || err.message)); }
  };

  const handleReset = async (key) => {
    try {
      await systemSettingsService.reset(key);
      fetchAll();
    } catch (err) { console.error(err); }
  };

  if (loading) return <div style={{ padding: '24px', color: '#888' }}>Loading settings...</div>;

  return (
    <div style={{ padding: '24px' }}>
      <h1 style={{ fontSize: '28px', fontWeight: 700, margin: '0 0 8px' }}>System Settings</h1>
      <p style={{ color: '#888', marginBottom: '24px' }}>Configure system-wide EvolvixOS behavior</p>

      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', flexWrap: 'wrap' }}>
        <button onClick={() => setSelectedCategory(null)} style={selectedCategory === null ? catActive : catBtn}>All ({settings.length})</button>
        {categories.map(cat => (
          <button key={cat} onClick={() => setSelectedCategory(cat)} style={selectedCategory === cat ? catActive : catBtn}>
            {cat}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {settings.map(s => (
          <div key={s.key} style={{ background: '#1A1A1E', borderRadius: '6px', padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderLeft: `3px solid ${s.overridden ? '#FFA500' : '#333'}` }}>
            <div>
              <span style={{ fontSize: '13px', fontWeight: 600 }}>{s.key}</span>
              <span style={{ fontSize: '11px', color: '#555', marginLeft: '8px' }}>{s.description}</span>
              {s.overridden && <span style={{ fontSize: '10px', padding: '1px 4px', borderRadius: '3px', background: '#FFA50022', color: '#FFA500', marginLeft: '4px' }}>overridden</span>}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {editing === s.key ? (
                <EditControl setting={s} onSave={(v) => handleSave(s.key, v)} onCancel={() => setEditing(null)} />
              ) : (
                <>
                  <span style={{ fontSize: '14px', fontFamily: 'monospace', color: s.overridden ? '#FFA500' : '#4F46E5' }}>
                    {String(s.value)}
                  </span>
                  <button onClick={() => setEditing(s.key)} style={btnSmall}>Edit</button>
                  {s.overridden && <button onClick={() => handleReset(s.key)} style={{ ...btnSmall, background: '#5C1A1A' }}>Reset</button>}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EditControl({ setting, onSave, onCancel }) {
  const [value, setValue] = useState(setting.value);

  const renderInput = () => {
    if (setting.type === 'bool') {
      return <input type="checkbox" checked={value} onChange={e => setValue(e.target.checked)} />;
    } else if (setting.type === 'int') {
      return <input type="number" value={value} onChange={e => setValue(parseInt(e.target.value) || 0)} style={inputStyle} />;
    } else if (setting.type === 'float') {
      return <input type="number" step="0.1" value={value} onChange={e => setValue(parseFloat(e.target.value) || 0)} style={inputStyle} />;
    }
    return <input type="text" value={value} onChange={e => setValue(e.target.value)} style={inputStyle} />;
  };

  return (
    <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
      {renderInput()}
      <button onClick={() => onSave(value)} style={{ ...btnSmall, background: '#22C55E', color: '#fff' }}>Save</button>
      <button onClick={onCancel} style={btnSmall}>Cancel</button>
    </div>
  );
}

const inputStyle = { padding: '4px 8px', background: '#0D0D0F', border: '1px solid #333', borderRadius: '4px', color: '#fff', fontSize: '13px', width: '100px' };
const btnSmall = { padding: '4px 12px', background: '#2A2A2E', color: '#CCC', border: '1px solid #333', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' };
const catBtn = { padding: '6px 14px', background: '#1A1A1E', border: '1px solid #333', borderRadius: '6px', color: '#888', cursor: 'pointer', fontSize: '13px' };
const catActive = { ...catBtn, background: '#4F46E5', color: '#fff', border: '1px solid #4F46E5' };

export default SystemSettings;
