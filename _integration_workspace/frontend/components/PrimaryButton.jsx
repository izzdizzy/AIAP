export default function PrimaryButton({ children, type = 'button', onClick, disabled, variant = 'solid' }) {
  const className = variant === 'ghost' ? 'primary-button primary-button--ghost' : 'primary-button';

  return (
    <button type={type} className={className} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
