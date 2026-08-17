export default function ResultCard({ title, children, tone = 'neutral' }) {
  return (
    <section className={`result-card result-card--${tone}`}>
      <h3>{title}</h3>
      <div>{children}</div>
    </section>
  );
}
