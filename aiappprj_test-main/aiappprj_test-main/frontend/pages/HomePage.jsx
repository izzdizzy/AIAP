import PrimaryButton from '../components/PrimaryButton';
import Disclaimer from '../components/Disclaimer';
import SectionCard from '../components/SectionCard';

export default function HomePage({ onStartAssessment }) {
  return (
    <div className="page-stack">
      <SectionCard
        title="Heart health screening"
        description="Estimate coronary artery disease (CAD) risk from standard clinical information."
      >
        <div className="hero-copy">
          <p>
            Answer a short set of questions about your age, symptoms, and any clinic results you already have.
            ECG and lab fields are optional.
          </p>
          <div className="hero-actions">
            <PrimaryButton onClick={onStartAssessment}>Start Assessment</PrimaryButton>
          </div>
        </div>
      </SectionCard>

      <Disclaimer />
    </div>
  );
}
