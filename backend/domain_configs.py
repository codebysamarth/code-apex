
DOMAIN_CONFIGS = {
    "software": {
        "mode": "Product Architect",
        "parameters": ["Functional Requirements", "Non-Functional Requirements", "Technical Decisions", "Stakeholders", "Timeline", "Scope"],
        "nfr_categories": ["Performance", "Security", "Scalability", "Availability", "Usability"],
        "priority_system": "MoSCoW (Must, Should, Could, Won’t)",
        "scoring": ["Completeness Score", "Confidence Score", "Value vs Effort"],
        "compliance": ["ISO 27001", "SOC2", "GDPR"],
        "terminology": {"user": "user", "system": "system", "feature": "feature", "requirement": "requirement"},
        "summary_labels": {
            "card1": "Functional",
            "card2": "Non-Functional",
            "card3": "Stakeholders",
            "card4": "Decisions"
        }
    },
    "healthcare": {
        "mode": "Clinical Systems Architect",
        "parameters": [
            "Clinical Requirements", 
            "Patient Safety & Risk Mitigation", 
            "Care Workflow & EHR Integration", 
            "Data Privacy (PHI / HIPAA / GDPR)", 
            "Compliance & FDA Regulatory", 
            "Clinical Decision Support (CDS)", 
            "Stakeholders (Care Teams/IT)", 
            "Implementation Roadmap"
        ],
        "priority_system": "Life-Criticality (NASA/FDA)",
        "scoring": ["Safety Index", "Regulatory Readiness", "Clinical Utility", "Interoperability"],
        "compliance": ["HIPAA", "FHIR", "HL7", "FDA Class II", "GDPR"],
        "terminology": {
            "user": "clinician/practitioner/patient", 
            "system": "clinical platform/EMR", 
            "feature": "medical capability/intervention", 
            "requirement": "clinical specification",
            "app": "clinical workflow tool",
            "database": "secure PHI repository",
            "login": "biometric/SSO authentication"
        },
        "summary_labels": {
            "card1": "Clinical",
            "card2": "Safety & HIPAA",
            "card3": "Medical Staff",
            "card4": "Integrations"
        },
        "special_rules": "MUST detect: Medical device classification, PHI exposure risks, and patient safety alerts."
    },
    "mechanical": {
        "mode": "Senior Systems Engineer (Hardware)",
        "parameters": [
            "Mechanical Design Specifications", 
            "Material Properties & Stress Analysis", 
            "Manufacturing & Assembly (DFM/DFA)", 
            "Tolerances & Precision Metrics", 
            "Safety Factors & Structural Integrity", 
            "Environmental Operating Conditions",
            "BOM (Bill of Materials) Constraints",
            "Project Timeline & Prototyping"
        ],
        "priority_system": "Safety Factor / Yield Strength",
        "scoring": ["Structural Integrity", "Manufacturability", "Cost Efficiency", "Reliability"],
        "compliance": ["ISO 9001", "ASME", "OSHA", "NIST", "ASTM"],
        "terminology": {
            "user": "operator/technician", 
            "system": "assembly/mechanical system", 
            "feature": "specification/mechanical sub-system", 
            "requirement": "design parameter",
            "software": "embedded control logic",
            "interface": "mechanical coupling/linkage",
            "bug": "mechanical failure/fatigue"
        },
        "summary_labels": {
            "card1": "Specs",
            "card2": "Materials",
            "card3": "Assembly",
            "card4": "Safety"
        },
        "special_rules": "MUST detect: Units (PSI, mm, °C), Tolerances (± values), Materials (steel, alloy, etc.), and Safety Factors."
    },
    "business": {
        "mode": "Strategic Business Consultant",
        "parameters": [
            "Market Entry Strategy",
            "Business Objectives & KPIs",
            "ROI & Financial Projections",
            "Strategic Risk & Mitigation",
            "Market Drivers & Competition",
            "Operational Requirements",
            "Regulatory & Compliance",
            "Strategic Roadmap"
        ],
        "priority_system": "Strategic, Compliance, Operational, Nice-to-Have",
        "scoring": ["ROI Score", "Risk Exposure Score", "Business Value Score"],
        "compliance": ["SOX", "GDPR", "IFRS", "SEC"],
        "special_rules": "MUST detect: Revenue impact, Cost savings, KPIs, Compliance (GDPR, SOX, etc.).",
        "terminology": {"user": "stakeholder", "system": "business solution", "feature": "business capability", "requirement": "business objective"},
        "summary_labels": {
            "card1": "Capabilities",
            "card2": "Risk & ROI",
            "card3": "Stakeholders",
            "card4": "Compliance"
        }
    }
}
