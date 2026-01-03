"""Healthcare Diagnostics AI - Business Logic Service"""

import logging
from typing import List
from sqlalchemy.orm import Session

from app.tier_1.infrastructure.config import Settings
from app.tier_1.llm.llm_service import LLMService
from .healthcare_diagnostics_schemas import *

logger = logging.getLogger(__name__)


class HealthcareDiagnosticsService:
    """Service for AI-powered medical diagnostics"""

    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        self.llm_service = LLMService(db, settings)

        # Import DocumentService for extracting patient data
        from app.tier_1.document_processing.document_service import DocumentService
        self.document_service = DocumentService(db, settings)

    async def analyze_symptoms(self, request: AnalyzeSymptomsRequest) -> AnalyzeSymptomsResponse:
        """Analyze patient symptoms with AI-powered diagnostics"""
        try:
            logger.info(f"Analyzing symptoms for patient {request.patient.patient_id}")

            # Extract patient data from uploaded medical records if document_id provided
            patient_data = request.patient
            if request.document_id:
                extracted_patient = await self._extract_patient_data(request.document_id)
                if extracted_patient:
                    patient_data = extracted_patient

            # Generate diagnostic hypotheses
            diagnoses = await self._generate_diagnoses_llm(patient_data, request.category)

            # Generate treatment recommendations
            treatments = []
            if request.include_recommendations:
                treatments = self._generate_treatments(diagnoses[:3])  # Top 3

            # Assess urgency
            urgency = None
            if request.urgency_assessment:
                urgency = self._assess_urgency(request.patient, diagnoses)

            # Generate AI insights
            ai_insights = await self._generate_ai_insights(request.patient, diagnoses)

            return AnalyzeSymptomsResponse(
                success=True,
                diagnoses=diagnoses,
                treatment_recommendations=treatments,
                urgency=urgency,
                ai_insights=ai_insights
            )

        except Exception as e:
            logger.error(f"Error analyzing symptoms: {e}", exc_info=True)
            raise

    async def _extract_patient_data(self, document_id: str) -> Optional[PatientData]:
        """Extract patient data from uploaded medical record"""
        try:
            chunks = await self.document_service.get_chunks_for_document(document_id)
            medical_record = " ".join([chunk.get('content', '') for chunk in chunks[:5]])

            prompt = f"""Extract patient information from this medical record:

{medical_record[:3000]}

Return JSON:
{{
  "patient_id": "id",
  "age": 45,
  "gender": "male/female/other",
  "symptoms": ["symptom1", "symptom2"],
  "medical_history": ["condition1"],
  "current_medications": ["medication1"],
  "allergies": ["allergy1"],
  "vital_signs": {{"blood_pressure": "120/80"}}
}}

Return ONLY valid JSON."""

            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.0,
                max_tokens=500
            )

            data = json.loads(response.strip())

            return PatientData(
                patient_id=data.get("patient_id", document_id),
                age=data.get("age"),
                gender=data.get("gender", "unknown"),
                symptoms=data.get("symptoms", []),
                medical_history=data.get("medical_history", []),
                current_medications=data.get("current_medications", []),
                allergies=data.get("allergies", []),
                vital_signs=data.get("vital_signs", {})
            )

        except Exception as e:
            logger.warning(f"Patient data extraction failed: {e}")
            return None

    async def _generate_diagnoses_llm(
        self, patient: PatientData, category: DiagnosticCategory
    ) -> List[DiagnosticHypothesis]:
        """Generate diagnostic hypotheses using LLM-based analysis"""
        symptoms_str = ", ".join(patient.symptoms)
        medical_history_str = ", ".join(patient.medical_history) if patient.medical_history else "None"

        prompt = f"""As a medical expert, analyze this patient case and provide differential diagnoses:

Patient: Age {patient.age}, Gender: {patient.gender}
Symptoms: {symptoms_str}
Medical History: {medical_history_str}
Category: {category.value}

Return JSON array:
[
  {{
    "condition": "Condition Name",
    "probability": 70.0,
    "severity": "low/moderate/high/critical",
    "confidence": "low/moderate/high/very_high",
    "supporting_evidence": ["evidence1", "evidence2"],
    "differential_diagnosis": ["alternative1", "alternative2"],
    "recommended_tests": ["test1", "test2"]
  }}
]

Provide top 5 diagnoses. Return ONLY valid JSON array."""

        try:
            response = await self.llm_service.generate_response(
                prompt=prompt,
                model="gpt-4o-mini",
                temperature=0.2,
                max_tokens=1000
            )

            diagnoses_data = json.loads(response.strip())

            diagnoses = []
            for diag in diagnoses_data:
                diagnoses.append(DiagnosticHypothesis(
                    condition=diag.get("condition", ""),
                    probability=float(diag.get("probability", 50)),
                    severity=SeverityLevel(diag.get("severity", "moderate")),
                    confidence=ConfidenceLevel(diag.get("confidence", "moderate")),
                    supporting_evidence=diag.get("supporting_evidence", []),
                    differential_diagnosis=diag.get("differential_diagnosis", []),
                    recommended_tests=diag.get("recommended_tests", [])
                ))

            return diagnoses[:5]

        except Exception as e:
            logger.warning(f"LLM diagnosis generation failed: {e}, using rule-based fallback")
            return self._generate_diagnoses_fallback(patient, category)

    def _generate_diagnoses_fallback(
        self, patient: PatientData, category: DiagnosticCategory
    ) -> List[DiagnosticHypothesis]:
        """Generate diagnostic hypotheses based on symptoms"""
        diagnoses = []

        # Symptom-based diagnostic logic
        symptoms_lower = [s.lower() for s in patient.symptoms]

        # Example diagnostic rules (simplified medical decision tree)
        if any(s in symptoms_lower for s in ["chest pain", "shortness of breath"]):
            prob = 70.0 if "chest pain" in symptoms_lower else 50.0
            diagnoses.append(DiagnosticHypothesis(
                condition="Coronary Artery Disease",
                probability=prob,
                severity=SeverityLevel.HIGH,
                confidence=ConfidenceLevel.HIGH,
                supporting_evidence=["Chest pain reported", "Age-related risk factors"],
                differential_diagnosis=["Angina", "Myocardial Infarction", "Aortic Dissection"],
                recommended_tests=["ECG", "Cardiac Enzymes", "Stress Test", "Angiography"]
            ))

        if any(s in symptoms_lower for s in ["fever", "cough", "fatigue"]):
            prob = 60.0
            diagnoses.append(DiagnosticHypothesis(
                condition="Respiratory Infection",
                probability=prob,
                severity=SeverityLevel.MODERATE,
                confidence=ConfidenceLevel.MODERATE,
                supporting_evidence=["Multiple respiratory symptoms", "Fever present"],
                differential_diagnosis=["COVID-19", "Influenza", "Pneumonia", "Bronchitis"],
                recommended_tests=["Chest X-Ray", "PCR Test", "Complete Blood Count"]
            ))

        if any(s in symptoms_lower for s in ["headache", "dizziness", "confusion"]):
            prob = 55.0
            diagnoses.append(DiagnosticHypothesis(
                condition="Neurological Disorder",
                probability=prob,
                severity=SeverityLevel.MODERATE,
                confidence=ConfidenceLevel.MODERATE,
                supporting_evidence=["Neurological symptoms reported"],
                differential_diagnosis=["Migraine", "Stroke", "Concussion", "Brain Tumor"],
                recommended_tests=["CT Scan", "MRI", "Neurological Exam"]
            ))

        # Sort by probability
        diagnoses.sort(key=lambda d: d.probability, reverse=True)
        return diagnoses[:5]

    def _generate_treatments(
        self, diagnoses: List[DiagnosticHypothesis]
    ) -> List[TreatmentRecommendation]:
        """Generate treatment recommendations"""
        treatments = []

        for diagnosis in diagnoses:
            if "Coronary" in diagnosis.condition:
                treatments.append(TreatmentRecommendation(
                    treatment_type="Pharmacological",
                    description="Antiplatelet therapy, Beta-blockers, Statins",
                    priority=1,
                    expected_outcome="Reduced cardiac events, improved symptoms",
                    contraindications=["Active bleeding", "Severe liver disease"]
                ))

            elif "Respiratory" in diagnosis.condition:
                treatments.append(TreatmentRecommendation(
                    treatment_type="Supportive Care",
                    description="Rest, hydration, antipyretics, respiratory support as needed",
                    priority=2,
                    expected_outcome="Symptom resolution within 7-14 days",
                    contraindications=[]
                ))

            elif "Neurological" in diagnosis.condition:
                treatments.append(TreatmentRecommendation(
                    treatment_type="Specialist Referral",
                    description="Immediate neurologist consultation and advanced imaging",
                    priority=1,
                    expected_outcome="Accurate diagnosis and timely intervention",
                    contraindications=[]
                ))

        return treatments[:3]

    def _assess_urgency(
        self, patient: PatientData, diagnoses: List[DiagnosticHypothesis]
    ) -> UrgencyAssessment:
        """Assess patient urgency level"""
        urgency_score = 30.0  # Base score

        # High severity diagnoses increase urgency
        critical_diagnoses = [d for d in diagnoses if d.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]]
        urgency_score += len(critical_diagnoses) * 20

        # Specific symptoms increase urgency
        symptoms_lower = [s.lower() for s in patient.symptoms]
        critical_symptoms = ["chest pain", "difficulty breathing", "severe bleeding", "loss of consciousness"]
        for symptom in critical_symptoms:
            if symptom in ' '.join(symptoms_lower):
                urgency_score += 15

        urgency_score = min(100.0, urgency_score)

        # Determine severity
        if urgency_score >= 80:
            severity = SeverityLevel.CRITICAL
        elif urgency_score >= 60:
            severity = SeverityLevel.HIGH
        elif urgency_score >= 40:
            severity = SeverityLevel.MODERATE
        else:
            severity = SeverityLevel.LOW

        # Time sensitive?
        time_sensitive = urgency_score >= 60

        # Immediate actions
        actions = []
        if urgency_score >= 80:
            actions.append("Call emergency services immediately")
            actions.append("Do not delay transport to emergency department")
        elif urgency_score >= 60:
            actions.append("Seek emergency medical attention within 1 hour")
            actions.append("Monitor vital signs continuously")
        else:
            actions.append("Schedule urgent appointment with primary care physician")

        # Warning signs
        warnings = [
            "Worsening symptoms",
            "New chest pain or difficulty breathing",
            "Altered mental status",
            "Uncontrolled bleeding"
        ]

        return UrgencyAssessment(
            urgency_score=int(urgency_score),
            severity_level=severity,
            time_sensitive=time_sensitive,
            immediate_actions=actions,
            warning_signs=warnings
        )

    async def _generate_ai_insights(
        self, patient: PatientData, diagnoses: List[DiagnosticHypothesis]
    ) -> str:
        """Generate AI-powered medical insights"""
        try:
            symptoms_str = ", ".join(patient.symptoms)
            top_diagnosis = diagnoses[0].condition if diagnoses else "No specific diagnosis"

            prompt = f"""Analyze this patient case:

Age: {patient.age}, Gender: {patient.gender}
Symptoms: {symptoms_str}
Top Diagnosis: {top_diagnosis}

Provide 2-3 sentences of expert medical insights on diagnostic considerations and recommended next steps."""

            response = await self.llm_service.generate_response(
                prompt=prompt, model="gpt-4o-mini", temperature=0.3
            )
            return response.strip()

        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return "Diagnostic analysis complete. Recommend comprehensive clinical evaluation and appropriate testing."

    async def search_diagnoses(self, request: SearchDiagnosesRequest) -> SearchDiagnosesResponse:
        """Search historical diagnoses"""
        return SearchDiagnosesResponse(
            success=True,
            diagnoses=[],
            total_count=0,
            summary_stats={"message": "Historical diagnosis search - database integration pending"}
        )

    async def export_diagnoses(self, request: ExportDiagnosesRequest) -> ExportDiagnosesResponse:
        """Export diagnostic data"""
        return ExportDiagnosesResponse(
            success=True,
            export_data={"message": "Diagnosis export", "format": request.format},
            format=request.format,
            record_count=0
        )

    async def get_stats(self) -> DiagnosticStatsResponse:
        """Get diagnostic statistics"""
        return DiagnosticStatsResponse(
            success=True,
            total_diagnoses=0,
            total_patients=0,
            category_distribution={},
            average_confidence=0.0,
            critical_cases=0,
            most_common_condition="respiratory_infection"
        )

    async def get_status(self) -> StatusResponse:
        """Get service status"""
        return StatusResponse(
            success=True,
            status="operational",
            capabilities=[
                "Symptom Analysis",
                "Differential Diagnosis",
                "Treatment Recommendations",
                "Urgency Assessment",
                "AI-Powered Medical Insights",
                "Multi-Specialty Support"
            ]
        )
