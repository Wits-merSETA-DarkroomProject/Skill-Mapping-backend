"""
ESCO Taxonomy Reference Dataset & Migration Seed
Includes trade and manufacturing occupations mapped to ISCO-08 with Essential & Optional skill breakdowns.
"""

ESCO_OCCUPATIONS = [
    {
        "id": "occ_millwright_3231",
        "concept_uri": "http://data.europa.eu/esco/occupation/94a7e930-b384-4861-8b09-323101",
        "isco_group": "3231",
        "title": "Industrial Machinery Mechanic / Millwright",
        "category": "Trade / Maintenance",
        "description": "Install, adjust, maintain, troubleshoot, and repair industrial equipment, mechanical assemblies, fluid power systems, and automated production machinery.",
        "skills": [
            {
                "id": "sk_plc_01",
                "label": "troubleshoot programmable logic controllers",
                "alt_labels": ["PLC troubleshooting", "Siemens S7 debugging", "PLC fault finding", "PLC programming"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Diagnose PLC software faults, trace I/O sensor signals, and clear ladder logic errors on automated machinery."
            },
            {
                "id": "sk_hyd_02",
                "label": "maintain hydraulic systems",
                "alt_labels": ["hydraulic systems", "hydraulic cylinder repair", "fluid power diagnostics", "hydraulic actuator maintenance"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Inspect and overhaul hydraulic pumps, directional control valves, pressure manifolds, and hydraulic cylinders."
            },
            {
                "id": "sk_pneu_03",
                "label": "maintain pneumatic systems",
                "alt_labels": ["pneumatic systems", "pneumatics", "compressed air lines", "solenoid valve maintenance"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Service pneumatic air preparation units (FRL), solenoid manifolds, and pneumatic actuators."
            },
            {
                "id": "sk_prev_maint_04",
                "label": "perform preventative maintenance",
                "alt_labels": ["preventative maintenance", "PM inspections", "total productive maintenance", "scheduled servicing"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Execute routine lubrication, wear inspection, vibration monitoring, and component replacement according to TPM schedules."
            },
            {
                "id": "sk_weld_05",
                "label": "weld metal structures",
                "alt_labels": ["welding", "arc welding", "MIG welding", "CO2 welding", "TIG welding"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Join and repair steel frames, mounting plates, and machine guards using electric arc or gas metal arc welding."
            },
            {
                "id": "sk_elec_fault_06",
                "label": "diagnose electrical faults",
                "alt_labels": ["electrical fault finding", "electrical diagnostics", "circuit testing", "multimeter diagnostics"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Isolate faults in 3-phase electric motors, contactors, overload relays, and control circuits using digital multimeters."
            },
            {
                "id": "sk_mech_draw_07",
                "label": "interpret technical drawings",
                "alt_labels": ["mechanical drawing interpretation", "blueprint reading", "engineering drawings", "CAD interpretation"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "knowledge",
                "description": "Read mechanical blueprints, assembly sectional drawings, geometric tolerances, and exploded machine diagrams."
            },
            {
                "id": "sk_align_08",
                "label": "align machine shafts and couplings",
                "alt_labels": ["bearing and coupling alignment", "laser shaft alignment", "dial indicator alignment", "bearing fitting"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Perform precise radial and axial alignment of rotating shafts and drive couplings using dial gauges or laser alignment tools."
            },
            {
                "id": "sk_scada_09",
                "label": "operate SCADA systems",
                "alt_labels": ["SCADA interface", "HMI monitoring", "supervisory control"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "skill/competence",
                "description": "Interact with supervisory control and data acquisition HMIs to adjust machine setpoints and diagnose alarms."
            },
            {
                "id": "sk_rigging_10",
                "label": "perform industrial rigging and slinging",
                "alt_labels": ["heavy rigging", "crane slinging", "machinery moving"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "skill/competence",
                "description": "Safely hoist, sling, and rig heavy motors, gearboxes, and press equipment using overhead cranes and shackles."
            }
        ]
    },
    {
        "id": "occ_cnc_operator_3223",
        "concept_uri": "http://data.europa.eu/esco/occupation/73b88132-7634-4061-9122-322301",
        "isco_group": "3223",
        "title": "CNC Machine Tool Setter / Operator",
        "category": "Trade / Machining",
        "description": "Set up, program, and operate computerized numerical control (CNC) lathes, milling machines, and machining centers to produce precision components.",
        "skills": [
            {
                "id": "sk_cnc_prog_01",
                "label": "program CNC machines",
                "alt_labels": ["CNC programming", "Fanuc programming", "Heidenhain programming", "Siemens Sinumerik"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Write and edit CNC machining toolpaths for turning and milling operations."
            },
            {
                "id": "sk_gcode_02",
                "label": "interpret G-code",
                "alt_labels": ["G-code interpretation", "G-code editing", "M-code commands", "manual tool offsetting"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "knowledge",
                "description": "Read, adjust, and optimize G-code blocks, feed rates, spindle speeds, and canned cycles."
            },
            {
                "id": "sk_precision_meas_03",
                "label": "use precision measuring instruments",
                "alt_labels": ["precision measurement", "micrometer inspection", "vernier calipers", "bore gauge checking"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Measure machined parts to within tight micron tolerances using micrometers, verniers, and height gauges."
            },
            {
                "id": "sk_tooling_setup_04",
                "label": "set up machine tooling",
                "alt_labels": ["tooling setup", "carbide insert indexing", "workpiece clamping", "tool presetting"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Mount cutting tools, index carbide inserts, touch off tool offsets, and fixture raw billets."
            },
            {
                "id": "sk_quality_insp_05",
                "label": "inspect manufactured parts",
                "alt_labels": ["quality inspection", "first-off inspection", "dimensional verification"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Perform first-off and in-process dimensional quality checks against engineering drawings."
            },
            {
                "id": "sk_cadcam_06",
                "label": "use CAD-CAM software",
                "alt_labels": ["CAD/CAM software", "Mastercam", "Fusion 360", "SolidCAM"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "skill/competence",
                "description": "Generate automated 3D toolpaths from CAD models using CAM software packages."
            },
            {
                "id": "sk_machine_maint_07",
                "label": "maintain machine tools",
                "alt_labels": ["machine maintenance", "coolant management", "guideway lubrication", "chip conveyor clearing"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "skill/competence",
                "description": "Refill slideway lubrication tanks, monitor cutting fluid concentration, and service chip conveyors."
            }
        ]
    },
    {
        "id": "occ_qa_technician_3119",
        "concept_uri": "http://data.europa.eu/esco/occupation/a8819201-9988-4333-8822-311901",
        "isco_group": "3119",
        "title": "Quality Assurance & Control Technician",
        "category": "Manufacturing / QA",
        "description": "Monitor manufacturing quality standards, perform metrological inspections, conduct root-cause audits, and ensure compliance with ISO standards.",
        "skills": [
            {
                "id": "sk_iso_01",
                "label": "audit according to ISO 9001",
                "alt_labels": ["ISO 9001 auditing", "quality auditing", "QMS compliance", "internal quality audit"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Conduct internal process audits in accordance with ISO 9001 quality management system requirements."
            },
            {
                "id": "sk_spc_02",
                "label": "apply statistical process control",
                "alt_labels": ["statistical process control", "SPC charting", "Cp Cpk calculations", "process capability"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Construct X-bar and R control charts to detect process drifts and calculate process capability indices."
            },
            {
                "id": "sk_rca_03",
                "label": "perform root cause analysis",
                "alt_labels": ["root cause analysis", "5-Why problem solving", "Fishbone diagram", "8D methodology"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Facilitate cross-functional failure investigation using 5-Why, Ishikawa (Fishbone), and 8D defect resolution methods."
            },
            {
                "id": "sk_msa_04",
                "label": "conduct measurement systems analysis",
                "alt_labels": ["measurement systems analysis", "Gage R&R", "metrology calibration", "MSA"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Perform Gage Repeatability and Reproducibility (R&R) studies to quantify inspection equipment variance."
            },
            {
                "id": "sk_ncr_05",
                "label": "manage non-conformance reports",
                "alt_labels": ["non-conformance reporting", "NCR management", "CAPA tracking", "scrap tracking"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Quarantine non-conforming materials, document NCRs, and monitor corrective and preventive actions (CAPA)."
            },
            {
                "id": "sk_sixsigma_06",
                "label": "apply Six Sigma methodology",
                "alt_labels": ["Six Sigma methodology", "Lean Six Sigma", "DMAIC framework", "Green Belt"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "knowledge",
                "description": "Participate in process variation reduction projects using the DMAIC (Define, Measure, Analyze, Improve, Control) framework."
            }
        ]
    },
    {
        "id": "occ_auto_electrician_3241",
        "concept_uri": "http://data.europa.eu/esco/occupation/77221199-8833-4112-9901-324101",
        "isco_group": "3241",
        "title": "Automotive Electrician",
        "category": "Trade / Automotive",
        "description": "Install, diagnose, and repair electrical wiring, electronic control units, sensors, and starting/charging systems in automotive vehicles.",
        "skills": [
            {
                "id": "sk_auto_diag_01",
                "label": "diagnose vehicle electrical systems",
                "alt_labels": ["vehicle electrical diagnostics", "OBD2 diagnostics", "automotive fault finding", "oscilloscope testing"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Scan diagnostic trouble codes (DTCs), test actuator wave patterns, and trace automotive circuit shorts."
            },
            {
                "id": "sk_harness_02",
                "label": "repair wiring harnesses",
                "alt_labels": ["wiring harness repair", "wire crimping", "connector pin extraction", "loom rebuilding"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "De-pin electrical connectors, re-terminate wiring with weather-pack seals, and replace damaged vehicle harnesses."
            },
            {
                "id": "sk_ecu_03",
                "label": "program engine control units",
                "alt_labels": ["ECU programming", "module flashing", "immobilizer coding"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Flash updated calibration maps to ECUs, configure body control modules, and adapt replacement sensor units."
            },
            {
                "id": "sk_canbus_04",
                "label": "troubleshoot CAN bus networks",
                "alt_labels": ["CAN bus systems", "LIN bus diagnostics", "multiplexed network troubleshooting"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Inspect twisted-pair communication lines, measure bus termination resistances, and isolate faulty network nodes."
            },
            {
                "id": "sk_ev_safety_05",
                "label": "work safely on high-voltage vehicle systems",
                "alt_labels": ["Hybrid/EV electrical safety", "high voltage lock-out", "EV battery de-energizing"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "knowledge",
                "description": "Adhere to safety isolation procedures, verify zero energy state, and service high-voltage traction inverter systems."
            }
        ]
    },
    {
        "id": "occ_solar_technician_3131",
        "concept_uri": "http://data.europa.eu/esco/occupation/66112233-4455-6677-8899-313101",
        "isco_group": "3131",
        "title": "Renewable Energy / Solar PV Technician",
        "category": "Energy / Emerging",
        "description": "Design, install, commission, and maintain solar photovoltaic arrays, inverters, and battery energy storage systems.",
        "skills": [
            {
                "id": "sk_solar_pv_01",
                "label": "install solar photovoltaic panels",
                "alt_labels": ["Solar PV installation", "solar array mounting", "PV GreenCard installer", "rooftop solar"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Mount rooftop aluminum racking, interconnect PV string conductors, and wire DC combiner boxes."
            },
            {
                "id": "sk_bms_02",
                "label": "maintain battery energy storage systems",
                "alt_labels": ["Battery storage systems", "Lithium battery maintenance", "BMS configuration", "inverter charging"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "skill/competence",
                "description": "Configure hybrid inverters, balance lithium-iron battery packs, and verify BMS communication protocols."
            },
            {
                "id": "sk_grid_std_03",
                "label": "comply with grid connection standards",
                "alt_labels": ["Grid connection standards", "NRS 097 standards", "SSEG compliance", "anti-islanding test"],
                "relation_type": "essential",
                "importance_score": 1.0,
                "skill_type": "knowledge",
                "description": "Ensure solar embedded generation complies with statutory utility grid feed-in and safety trip standards."
            },
            {
                "id": "sk_site_assess_04",
                "label": "perform solar site assessment",
                "alt_labels": ["Site assessment", "solar irradiance mapping", "shading analysis", "structural load check"],
                "relation_type": "optional",
                "importance_score": 0.5,
                "skill_type": "skill/competence",
                "description": "Analyze roof tilt angles, measure solar irradiance with pyranometers, and calculate shading losses."
            }
        ]
    }
]

# South African Accredited Learning Pathways mapping (for missing skills recommendations)
LEARNING_PATHWAYS_MAP = {
    "sk_plc_01": {
        "course_title": "Siemens S7-1200/1500 Modular Automation & Diagnostics",
        "provider_name": "Accredited TVET Colleges & Siemens Training Partners",
        "nqf_level": "NQF Level 5 module",
        "funding_scheme": "merSETA Category C Training Grant",
        "duration_weeks": 6,
        "description": "Hands-on industrial automation module covering ladder logic, TIA Portal, sensor interfacing, and factory fault isolation."
    },
    "sk_hyd_02": {
        "course_title": "Advanced Fluid Power & Industrial Hydraulics Overhaul",
        "provider_name": "Accredited TVET Technical Centers",
        "nqf_level": "NQF Level 4 module",
        "funding_scheme": "Sector Artisan Development Scheme (SADP)",
        "duration_weeks": 4,
        "description": "Diagnostic maintenance on proportional valves, hydraulic power packs, and hydraulic schematics."
    },
    "sk_pneu_03": {
        "course_title": "Festo Certified Electro-Pneumatics & Solenoid Control",
        "provider_name": "Registered Private Trade Schools & Public TVETs",
        "nqf_level": "NQF Level 4 module",
        "funding_scheme": "Employer Workplace Skills Plan (WSP)",
        "duration_weeks": 3,
        "description": "Pneumatic cylinder timing, vacuum generators, and electro-pneumatic sequencing."
    },
    "sk_align_08": {
        "course_title": "Precision Laser Shaft Alignment & Rotating Machinery Balancing",
        "provider_name": "SKF Reliability Systems / Wits Technical Center",
        "nqf_level": "NQF Level 4 module",
        "funding_scheme": "merSETA Discretionary Grant Category C",
        "duration_weeks": 2,
        "description": "Laser optical alignment methods for electric motors, gearboxes, and centrifugal pumps."
    },
    "sk_mech_draw_07": {
        "course_title": "Engineering Blueprints & Geometric Dimensioning & Tolerancing (GD&T)",
        "provider_name": "Public TVET Colleges (N2 Engineering Theory)",
        "nqf_level": "NQF Level 3 (Trade Test requirement)",
        "funding_scheme": "National Skills Fund (NSF)",
        "duration_weeks": 8,
        "description": "Standard engineering drawing orthographic projection, weld symbols, and tolerance interpretation."
    },
    "sk_cnc_prog_01": {
        "course_title": "Accredited CNC G-Code & Fanuc Machining Center Programming",
        "provider_name": "merSETA Advanced Manufacturing Training Hub",
        "nqf_level": "NQF Level 4 module",
        "funding_scheme": "National Artisan Moderation Body (NAMB)",
        "duration_weeks": 8,
        "description": "Manual G-code writing, cutter radius compensation, and multi-axis milling cycles."
    },
    "sk_iso_01": {
        "course_title": "ISO 9001:2015 Lead Quality Auditor Certification",
        "provider_name": "SAATCA / Wits Enterprise",
        "nqf_level": "NQF Level 5 module",
        "funding_scheme": "merSETA Category C Grant",
        "duration_weeks": 4,
        "description": "Auditing manufacturing operations, clause compliance, and process performance verification."
    },
    "sk_solar_pv_01": {
        "course_title": "SAPVIA Accredited PV GreenCard Installer & Grid Tie Course",
        "provider_name": "SAPVIA Registered Training Centers (e.g. Wits PV Labs)",
        "nqf_level": "NQF Level 4 module",
        "funding_scheme": "Green Economy Skills Development Levy",
        "duration_weeks": 4,
        "description": "Sizing strings, inverter synchronisation, DC isolation safety, and rooftop mounting integrity."
    }
}
