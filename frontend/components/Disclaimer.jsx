export default function Disclaimer({ compact = false, message = null }) {
  const defaultText = 'This clinical decision support prototype is for educational and screening purposes only. It does not replace professional medical diagnosis, urgent care, or specialist evaluation.';

  return (
    <aside className={compact ? 'disclaimer disclaimer--compact' : 'disclaimer'}>
      <strong>Clinical Disclaimer:</strong> {message || defaultText}
    </aside>
  );
}
