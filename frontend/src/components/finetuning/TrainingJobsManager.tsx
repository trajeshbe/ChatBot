import React from 'react';
import TrainingJobsManagerEnhanced from './TrainingJobsManagerEnhanced';

export default function TrainingJobsManager({ userRole }: { userRole: string }) {
  return <TrainingJobsManagerEnhanced userRole={userRole} />;
}
