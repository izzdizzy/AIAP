import React from 'react';
import ShapFactorCardWidget from './ShapFactorCardWidget';
import TriageChecklistWidget from './TriageChecklistWidget';
import CopyableQuestionsWidget from './CopyableQuestionsWidget';
import ClinicMapLinkWidget from './ClinicMapLinkWidget';
import GoogleMapsActionButton from './GoogleMapsActionButton';
import TabNavigationWidget from './TabNavigationWidget';

export default function WidgetRenderer({ widget, onUpdateWidgetData, onNavigateTab }) {
  if (!widget || !widget.type) return null;

  const widgetType = widget.type.toUpperCase();

  switch (widgetType) {
    case 'SHAP_FACTOR_CARD':
      return <ShapFactorCardWidget data={widget.data} />;
    case 'TRIAGE_CHECKLIST':
      return <TriageChecklistWidget data={widget.data} onUpdateWidgetData={onUpdateWidgetData} />;
    case 'COPYABLE_DOCTOR_QUESTIONS':
      return <CopyableQuestionsWidget data={widget.data} />;
    case 'CLINIC_MAP_LINK':
    case 'GOOGLE_MAPS_ACTION':
      return <GoogleMapsActionButton data={widget.data} />;
    case 'TAB_NAVIGATION_ACTION':
    case 'TAB_NAVIGATION_WIDGET':
      return <TabNavigationWidget data={widget.data} onNavigateTab={onNavigateTab} />;
    default:
      return null;
  }
}
