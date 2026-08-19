import React, { useState } from 'react';

export default function TriageChecklistWidget({ data, onUpdateWidgetData }) {
  if (!data) return null;

  const { title = "Post-Discharge Care Tasks", urgency, tasks = [] } = data;
  const [taskList, setTaskList] = useState(
    tasks.map((t, idx) => ({ id: t.id || idx, task: t.task || t, completed: Boolean(t.completed) }))
  );

  function toggleTask(id) {
    const updated = taskList.map(item =>
      item.id === id ? { ...item, completed: !item.completed } : item
    );
    setTaskList(updated);
    if (onUpdateWidgetData) {
      onUpdateWidgetData({
        ...data,
        tasks: updated
      });
    }
  }

  const completedCount = taskList.filter(t => t.completed).length;

  return (
    <div style={{
      marginTop: '12px',
      marginBottom: '12px',
      padding: '16px',
      borderRadius: '12px',
      background: 'var(--surface-muted)',
      border: '1px solid var(--border)',
      color: 'var(--text)',
      boxShadow: 'var(--shadow)'
    }}>
      <div style={{
        display: 'flex',
        justify: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
        borderBottom: '1px solid var(--border)',
        paddingBottom: '8px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '1.2rem' }}>📋</span>
          <strong style={{ fontSize: '0.95rem' }}>{title}</strong>
        </div>
        {urgency && (
          <span style={{
            padding: '3px 8px',
            borderRadius: '10px',
            fontSize: '0.7rem',
            fontWeight: '700',
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            color: '#60a5fa',
            border: '1px solid #3b82f6'
          }}>
            {urgency}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {taskList.map((item) => (
          <label
            key={item.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 10px',
              borderRadius: '6px',
              background: item.completed ? 'rgba(16, 185, 129, 0.12)' : 'var(--surface)',
              border: '1px solid var(--border)',
              cursor: 'pointer',
              userSelect: 'none',
              transition: 'background 0.2s ease'
            }}
          >
            <input
              type="checkbox"
              checked={item.completed}
              onChange={() => toggleTask(item.id)}
              style={{ width: '16px', height: '16px', accentColor: '#10b981', cursor: 'pointer' }}
            />
            <span style={{
              fontSize: '0.85rem',
              textDecoration: item.completed ? 'line-through' : 'none',
              opacity: item.completed ? 0.65 : 1,
              color: item.completed ? 'var(--text-muted)' : 'var(--text)'
            }}>
              {item.task}
            </span>
          </label>
        ))}
      </div>

      <div style={{ marginTop: '10px', fontSize: '0.75rem', opacity: 0.7, textAlign: 'right' }}>
        {completedCount} of {taskList.length} tasks completed
      </div>
    </div>
  );
}
