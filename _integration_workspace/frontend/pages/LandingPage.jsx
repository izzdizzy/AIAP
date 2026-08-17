import React from 'react';

/**
 * Landing Page - Healthcare Risk Assessment Portal
 * 
 * This is the main entry point for users to choose between:
 * 1. CAD Risk Assessment (Coronary Artery Disease screening)
 * 2. Hospital Readmission Predictor
 * 
 * Route: #/ or #/home (default landing page)
 */
export default function LandingPage({ onStartCADAssessment, onStartReadmissionAssessment }) {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#111827',
      padding: '2rem'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        {/* Header */}
        <header style={{
          textAlign: 'center',
          marginBottom: '3rem'
        }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: 'bold',
            color: '#f3f4f6',
            marginBottom: '0.5rem'
          }}>
            Healthcare Risk Assessment Portal
          </h1>
          <p style={{
            color: '#9ca3af',
            fontSize: '1.1rem'
          }}>
            Select a module below to begin your clinical risk assessment
          </p>
        </header>

        {/* Module Selection Cards */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))',
          gap: '2rem',
          marginTop: '2rem'
        }}>
          {/* CAD Risk Assessment Card */}
          <div
            onClick={onStartCADAssessment}
            style={{
              backgroundColor: '#1f2937',
              borderRadius: '12px',
              padding: '2rem',
              border: '2px solid #374151',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#3b82f6';
              e.currentTarget.style.transform = 'translateY(-4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#374151';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{
              width: '60px',
              height: '60px',
              backgroundColor: '#3b82f6',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem'
            }}>
              <svg style={{ width: '32px', height: '32px', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
              </svg>
            </div>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              color: '#f3f4f6',
              marginBottom: '0.75rem'
            }}>
              CAD Risk Assessment
            </h2>
            <p style={{
              color: '#9ca3af',
              lineHeight: '1.6',
              marginBottom: '1.5rem'
            }}>
              Estimate coronary artery disease (CAD) risk from standard clinical information. 
              Answer questions about age, symptoms, and clinic results. ECG and lab fields are optional.
            </p>
            <button
              onClick={onStartCADAssessment}
              style={{
                width: '100%',
                padding: '0.75rem 1.5rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer'
              }}
            >
              Start CAD Assessment
            </button>
          </div>

          {/* Hospital Readmission Predictor Card */}
          <div
            onClick={onStartReadmissionAssessment}
            style={{
              backgroundColor: '#1f2937',
              borderRadius: '12px',
              padding: '2rem',
              border: '2px solid #374151',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = '#10b981';
              e.currentTarget.style.transform = 'translateY(-4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = '#374151';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{
              width: '60px',
              height: '60px',
              backgroundColor: '#10b981',
              borderRadius: '12px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1.5rem'
            }}>
              <svg style={{ width: '32px', height: '32px', color: 'white' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
              </svg>
            </div>
            <h2 style={{
              fontSize: '1.5rem',
              fontWeight: '600',
              color: '#f3f4f6',
              marginBottom: '0.75rem'
            }}>
              Hospital Readmission Predictor
            </h2>
            <p style={{
              color: '#9ca3af',
              lineHeight: '1.6',
              marginBottom: '1.5rem'
            }}>
              Predict hospital readmission risk using ML-powered clinical decision support. 
              Analyze patient history, admissions, comorbidities, and medications to assess readmission probability.
            </p>
            <button
              onClick={onStartReadmissionAssessment}
              style={{
                width: '100%',
                padding: '0.75rem 1.5rem',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontWeight: '600',
                fontSize: '1rem',
                cursor: 'pointer'
              }}
            >
              Start Readmission Assessment
            </button>
          </div>
        </div>

        {/* Medical Disclaimer */}
        <div style={{
          marginTop: '3rem',
          padding: '1rem',
          backgroundColor: 'rgba(234, 179, 8, 0.1)',
          borderLeft: '4px solid #eab308',
          borderRadius: '8px'
        }}>
          <p style={{
            fontSize: '0.875rem',
            color: '#fef08a',
            lineHeight: '1.5'
          }}>
            <strong>Medical Disclaimer:</strong> This tool is for educational and demonstration purposes only. 
            It does not provide medical advice, diagnosis, or treatment. Always consult qualified healthcare professionals 
            for medical decisions.
          </p>
        </div>
      </div>
    </div>
  );
}
