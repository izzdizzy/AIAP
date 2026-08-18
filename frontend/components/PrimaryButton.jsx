import React from 'react';
import { Play, Sparkles, ArrowLeft, Database, Activity } from 'lucide-react';

/**
 * Tiered Button Component following Clinical UI/UX visual hierarchy:
 * - 'primary' / 'solid': High-contrast teal (#0D9488) execution button
 * - 'ai': Indigo/Purple (#6366F1) AI assistant trigger
 * - 'secondary' / 'slate': Dark slate (#334155) navigation button
 * - 'utility' / 'ghost': Ghost/Outlined sample data / import button
 */
export default function PrimaryButton({
  children,
  type = 'button',
  onClick,
  disabled = false,
  variant = 'primary',
  icon: CustomIcon = null,
  style = {},
  className = ''
}) {
  let btnClass = 'btn-primary-teal';
  let DefaultIcon = null;

  if (variant === 'ai') {
    btnClass = 'btn-ai-indigo';
    DefaultIcon = Sparkles;
  } else if (variant === 'secondary' || variant === 'slate') {
    btnClass = 'btn-secondary-slate';
    DefaultIcon = ArrowLeft;
  } else if (variant === 'utility' || variant === 'ghost') {
    btnClass = 'btn-utility-ghost';
    DefaultIcon = Database;
  } else {
    // default / primary
    btnClass = 'btn-primary-teal';
    DefaultIcon = Play;
  }

  const IconComponent = CustomIcon || DefaultIcon;

  return (
    <button
      type={type}
      className={`${btnClass} ${className}`.trim()}
      onClick={onClick}
      disabled={disabled}
      style={style}
    >
      {IconComponent && <IconComponent style={{ width: '18px', height: '18px', flexShrink: 0 }} />}
      <span>{children}</span>
    </button>
  );
}

