export default function SectionCard({ title, description, children }) {
  return (
    <section className="section-card">
      <div className="section-card__header">
        <div>
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
      </div>
      <div className="section-card__body">{children}</div>
    </section>
  );
}
