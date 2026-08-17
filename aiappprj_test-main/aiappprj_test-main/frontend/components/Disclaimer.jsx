export default function Disclaimer({ compact = false }) {
  return (
    <aside className={compact ? 'disclaimer disclaimer--compact' : 'disclaimer'}>
      <strong>Medical disclaimer.</strong> This prototype is for educational screening only. It does not diagnose coronary artery disease, and it should not replace professional medical advice, urgent care, or follow-up testing.
    </aside>
  );
}
