import React from 'react';
import SectionCard from './SectionCard';

/**
 * Reusable Progress Sidebar
 * Shows real-time completion status across form groups (answered vs total).
 */
export default function ProgressSidebar({
  answeredCount = 0,
  totalCount = 0,
  groups = []
}) {
  return (
    <aside className="assessment-progress" aria-label="Assessment Form Progress">
      <SectionCard title="Form Progress" description="Field completion tracking">
        <div className="progress-metric">
          <strong>{answeredCount}</strong>
          <span>of {totalCount} completed</span>
        </div>

        {groups.length > 0 && (
          <div className="progress-list">
            {groups.map((group) => (
              <div key={group.id || group.title} className={`progress-group ${group.statusClass || 'progress-group--orange'}`}>
                <div className="progress-group__header">
                  <strong>{group.title}</strong>
                  <span className="progress-group__count">
                    {group.answeredCount ?? 0}/{group.totalCount ?? 0}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </SectionCard>
    </aside>
  );
}
