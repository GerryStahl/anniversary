from datetime import date

from docx import Document

from src.store import load_store


SELECTIONS = [
    {
        "period": "2006-2015",
        "id": "ijCSCL_2_2_4",
        "rationale": "Foundational script-specification framework (components + mechanisms) used across later CSCL script theory.",
    },
    {
        "period": "2016-2025",
        "id": "2017_v12i1_10.1007_s11412-017-9251-0_Group_practices_a_new_way_of_viewing_CSCL",
        "rationale": "Reframes CSCL analysis around routinized group practices, linking micro interaction and broader culture.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_3_1_1",
        "rationale": "Core theoretical account of how macro-scripts engineer interaction patterns and knowledge work.",
    },
    {
        "period": "2016-2025",
        "id": "2016_v11i3_10.1007_s11412-016-9240-8_Contribution_to_a_theory_of_CSCL_scripts_taking_into_account_the_appropriation_of_scripts_by_learners",
        "rationale": "Extends script theory by centering learner appropriation as a core mechanism.",
    },
    {
        "period": "2016-2025",
        "id": "2021_v16i4_10.1007_s11412-021-09359-1_Educational_dialogues_and_computer_supported_collaborative_learning_critical_analysis_and_research_perspectives",
        "rationale": "Re-specifies theoretical unit of analysis (exchange) and multi-timescale integration.",
    },
    {
        "period": "2016-2025",
        "id": "2025_v20i3_10.1007_s11412-025-09448-5_Collaborative_science_Formalism_and_a_unified_language_Future_directions_for_computer-supported_collaborative_learning",
        "rationale": "High-level formalization proposal for cumulative CSCL knowledge and mechanistic explanation.",
    },
    {
        "period": "2016-2025",
        "id": "2019_v14i2_10.1007_s11412-019-09301-6_Towards_a_micro-ecological_approach_to_CSCL",
        "rationale": "Offers a multi-level theory of orchestration via transecological disruptions.",
    },
    {
        "period": "2016-2025",
        "id": "2020_v15i1_10.1007_s11412-020-09317-3_Learning_in_embodied_activity_framework_a_sociocultural_framework_for_embodied_cognition",
        "rationale": "LEAF integrates embodied cognition with sociocultural/activity-theory constructs for CSCL.",
    },
    {
        "period": "2016-2025",
        "id": "2017_v12i2_10.1007_s11412-017-9256-8_Joint_interactions_in_large_online_knowledge_communities_The_A3C_framework",
        "rationale": "Introduces a scalable typology (Attendance, Coordination, Cooperation, Collaboration) for mass collaboration.",
    },
    {
        "period": "2016-2025",
        "id": "2018_v13i2_10.1007_s11412-018-9277-y_From_Cognitive_Load_Theory_to_Collaborative_Cognitive_Load_Theory",
        "rationale": "Theoretical move from individual to collective working-memory dynamics with transactive costs.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_3_2_5",
        "rationale": "Introduces SPAIRD, a major bridge from script theory to implementable technological design.",
    },
    {
        "period": "2016-2025",
        "id": "2021_v16i2_10.1007_s11412-021-09344-8_Social_sensitivity_a_manifesto_for_CSCL_research",
        "rationale": "Proposes an interdisciplinary integrative construct to bridge fragmented CSCL traditions.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_5_1_1",
        "rationale": "Strong conceptual advance for distributed interaction analysis in CSCL.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_10_3_1",
        "rationale": "Brings communicative action theory directly into CSCL meaning-making and critique of discourse quality.",
    },
    {
        "period": "2016-2025",
        "id": "2019_v14i2_10.1007_s11412-019-09302-5_Learners_agency_and_CSCL_technologies_towards_an_emancipatory_perspective",
        "rationale": "Strong critical-pragmatic reorientation toward learner agency and technology-as-service.",
    },
    {
        "period": "2016-2025",
        "id": "2018_v13i1_10.1007_s11412-018-9273-2_One_framework_to_rule_them_all_Carrying_forward_the_conversation_started_by_Wise_and_Schwarz",
        "rationale": "Proposes a taxonomy-based path to cumulative CSCL theory building rather than one grand theory.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_1_2_2",
        "rationale": "Early formalization of design-principles work for knowledge-building theory in CSCL.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_2_2_9",
        "rationale": "Influential dialogic/argumentation analytic framework grounded in pragma-dialectics.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_3_2_1",
        "rationale": "Integrates systemic and cognitive perspectives for wiki-based collaborative knowledge building.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_5_1_2",
        "rationale": "Integrative synthesis that consolidated argumentation theory strands and shaped later CSCL theory-building.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_7_2_1",
        "rationale": "Important socio-material/theoretical move on agent-artifact co-constitution.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_7_2_3",
        "rationale": "Extends activity-theoretical concepts into CSCL with a strong conceptual innovation agenda.",
    },
    {
        "period": "2006-2015",
        "id": "ijCSCL_9_1_1",
        "rationale": "High-value theoretical contribution reframing sustainability and contradiction analysis in CSCL.",
    },
    {
        "period": "2016-2025",
        "id": "2017_v12i4_10.1007_s11412-017-9267-5_Visions_of_CSCL_eight_provocations_for_the_future_of_the_field",
        "rationale": "Sets a major theoretical agenda on agency, methods, scale, and field-level coherence.",
    },
    {
        "period": "2016-2025",
        "id": "2022_v17i1_10.1007_s11412-022-09364-y_CSsCL_the_performance_of_collaborative_learning",
        "rationale": "Reconceptualizes scripted collaboration, regulation, and group awareness through a performance metaphor.",
    },
    {
        "period": "2016-2025",
        "id": "2023_v18i4_10.1007_s11412-023-09409-w_Co-constructing_knowledge_with_generative_AI_tools_Reflections_from_a_CSCL_perspective",
        "rationale": "Extends knowledge-building theory into human-AI collaboration and generative-AI-supported inquiry.",
    },
]


OUTPUT_PATH = "reports/cscl_theory_article_selections_2006_2025.docx"


def format_authors(authors):
    if isinstance(authors, list):
        return ", ".join(authors)
    return authors or ""


store = load_store()
doc = Document()
doc.add_heading("Selected CSCL Theory Contributions, 2006-2025", level=0)
doc.add_paragraph(
    "This document lists 24 non-editorial articles selected as especially significant contributions to "
    "the theory of CSCL or related educational theories. Entries are presented in ranked order based on "
    "their apparent theoretical significance and influence as inferred from the reviewed summaries."
)
doc.add_paragraph(f"Generated on {date.today().isoformat()}")

doc.add_heading("Selection methodology", level=1)
doc.add_paragraph(
    "These articles were selected through summary-based expert screening of non-editorial papers from "
    "2006-2015 and 2016-2025. The review used article titles, summary text, and coded theory fields to "
    "identify papers that appeared to make especially strong contributions to CSCL theory or related "
    "educational theories."
)
doc.add_paragraph(
    "Priority was given to articles that introduced or substantially extended a theoretical framework, "
    "model, construct, vocabulary, unit of analysis, or integrative perspective. Papers were ranked higher "
    "when they seemed to make field-level conceptual moves, connect multiple theoretical traditions, or "
    "offer explanatory value beyond a single tool, intervention, or local empirical result."
)
doc.add_paragraph(
    "The ranking is a judgment-based ordering derived from the available summaries rather than a formal "
    "bibliometric or citation analysis. It should therefore be interpreted as a theoretically informed "
    "screening of likely significance, not a definitive historical measure of influence."
)

for index, item in enumerate(SELECTIONS, start=1):
    article = store[item["id"]]
    doc.add_heading(f"{index}. {article.title or article.id}", level=2)

    details = doc.add_paragraph()
    details.add_run("Rank: ").bold = True
    details.add_run(str(index))
    details.add_run("\n")
    details.add_run("Period: ").bold = True
    details.add_run(item["period"])
    details.add_run("\n")
    details.add_run("ID: ").bold = True
    details.add_run(article.id)
    details.add_run("\n")
    details.add_run("Year: ").bold = True
    details.add_run(str(article.year or ""))
    details.add_run("\n")
    details.add_run("Authors: ").bold = True
    details.add_run(format_authors(article.authors))
    details.add_run("\n")
    details.add_run("Title: ").bold = True
    details.add_run(article.title or "")
    if article.doi:
        details.add_run("\n")
        details.add_run("DOI: ").bold = True
        details.add_run(article.doi)

    rationale = doc.add_paragraph()
    rationale.add_run("Why selected: ").bold = True
    rationale.add_run(item["rationale"])

    summary = doc.add_paragraph()
    summary.add_run("Summary: ").bold = True
    summary.add_run((article.summary_haiku or "").replace("# Summary ", "").strip())


doc.save(OUTPUT_PATH)
print(f"Saved {OUTPUT_PATH}")
