from datetime import date

from docx import Document

from src.store import load_store


SELECTIONS = [
    {
        "rank": 1,
        "period": "2010",
        "id": "ijCSCL_5_1_1",
        "rationale": "Major framework paper introducing uptake analysis and contingency graphs for distributed technology-mediated interaction.",
    },
    {
        "rank": 2,
        "period": "2009",
        "id": "ijCSCL_4_2_1",
        "rationale": "Foundational sequential analysis of how chat and shared workspace actions are jointly organized in multimodal CSCL.",
    },
    {
        "rank": 3,
        "period": "2021",
        "id": "2021_v16i4_10.1007_s11412-021-09359-1_Educational_dialogues_and_computer_supported_collaborative_learning_critical_analysis_and_research_perspectives",
        "rationale": "Major synthesis arguing for theoretically grounded, multi-timescale analysis of educational dialogue in CSCL.",
    },
    {
        "rank": 4,
        "period": "2018",
        "id": "2018_v13i4_10.1007_s11412-018-9292-z_When_coding-and-counting_is_not_enough_using_epistemic_network_analysis_ENA_to_analyze_verbal_data_in_CSCL_research",
        "rationale": "High-value method paper demonstrating why temporal and relational structure matters beyond frequency counts.",
    },
    {
        "rank": 5,
        "period": "2014",
        "id": "ijCSCL_9_2_1",
        "rationale": "Important automation step for dialogic chat analysis using NLP and social network methods.",
    },
    {
        "rank": 6,
        "period": "2011",
        "id": "ijCSCL_6_2_2",
        "rationale": "Strong dialogic account of how wiki-supported interaction creates a space for thinking together across modalities.",
    },
    {
        "rank": 7,
        "period": "2017",
        "id": "2017_v12i2_10.1007_s11412-017-9255-9_Life_history_of_a_topic_in_an_online_discussion_a_complex_systems_theory_perspective_on_how_one_message_attracts_class_m",
        "rationale": "Tracks topic emergence longitudinally and models interaction as a complex, evolving meaning-making process.",
    },
    {
        "rank": 8,
        "period": "2024",
        "id": "2024_v19i2_10.1007_s11412-024-09420-9_Dialogues_across_time_and_space_in_a_video-based_collaborative_learning_environment",
        "rationale": "Strong analysis of how interaction persists across synchronous and asynchronous spaces and scales.",
    },
    {
        "rank": 9,
        "period": "2007",
        "id": "ijCSCL_2_2_1",
        "rationale": "Influential methodology for analyzing collaborative knowledge construction via thematic structure, communicative function, and context.",
    },
    {
        "rank": 10,
        "period": "2014",
        "id": "ijCSCL_9_2_3",
        "rationale": "Innovatively operationalizes online 'listening' from clickstream traces rather than only posted discourse.",
    },
    {
        "rank": 11,
        "period": "2020",
        "id": "2020_v15i3_10.1007_s11412-020-09328-0_Dialogic_intervisualizing_in_multimodal_inquiry",
        "rationale": "Introduces a strong construct for analyzing how talk and visual representations interact in collaborative inquiry.",
    },
    {
        "rank": 12,
        "period": "2023",
        "id": "2023_v18i1_10.1007_s11412-023-09387-z_An_artificial_intelligence-driven_learning_analytics_method_to_examine_the_collaborative_p",
        "rationale": "Significant analytical framework combining AI, dynamic pattern detection, and multimodal collaborative process analysis.",
    },
    {
        "rank": 13,
        "period": "2019",
        "id": "2019_v14i3_10.1007_s11412-019-09306-1_Supporting_classroom_orchestration_with_real-time_feedback_A_role_for_teacher_dashboards_and_real-time_agents",
        "rationale": "Important interaction-analytics contribution linking real-time traces to orchestration decisions in classrooms.",
    },
    {
        "rank": 14,
        "period": "2021",
        "id": "2021_v16i3_10.1007_s11412-021-09351-9_Deconstructing_orchestration_load_comparing_teacher_support_through_mirroring_and_guiding",
        "rationale": "Useful analytic decomposition of orchestration load into interpretable dimensions for teacher support.",
    },
    {
        "rank": 15,
        "period": "2022",
        "id": "2022_v17i3_10.1007_s11412-022-09377-7_Implementing_learning_analytics_in_wiki-supported_collaborative_learning_in_secondary_education_A_framework-motivated_em",
        "rationale": "Framework-driven analytics for contribution, participation, transactivity, and social dynamics in wiki-supported CSCL.",
    },
    {
        "rank": 16,
        "period": "2006",
        "id": "ijCSCL_1_3_4",
        "rationale": "Early integration of social network analysis with qualitative and quantitative evidence for CSCL participation analysis.",
    },
    {
        "rank": 17,
        "period": "2016",
        "id": "2016_v11i4_10.1007_s11412-016-9245-3_Toward_a_classification_of_discourse_patterns_in_asynchronous_online_discussions",
        "rationale": "Strong typology of discourse patterns spanning knowledge sharing, construction, and knowledge building.",
    },
    {
        "rank": 18,
        "period": "2009",
        "id": "ijCSCL_4_3_2",
        "rationale": "Important discourse scheme separating knowledge sharing, knowledge construction, and knowledge creation modes.",
    },
    {
        "rank": 19,
        "period": "2018",
        "id": "2018_v13i3_10.1007_s11412-018-9281-2_Leveraging_mobile_eye-trackers_to_capture_joint_visual_attention_in_co-located_collaborative_learning_groups",
        "rationale": "Significant multimodal measurement innovation for joint visual attention and collaborative coordination.",
    },
    {
        "rank": 20,
        "period": "2020",
        "id": "2020_v15i2_10.1007_s11412-020-09322-6_Capturing_the_participation_and_social_dimensions_of_computer-supported_collaborative_lear",
        "rationale": "Validates network centrality choices for analyzing participation and social position in CSCL datasets.",
    },
    {
        "rank": 21,
        "period": "2022",
        "id": "2022_v17i3_10.1007_s11412-022-09374-w_iTalkiSee_A_participatory_visual_learning_analytical_tool_for_productive_peer_talk",
        "rationale": "Translates dialogic theory into a participatory analytics tool for visible, interpretable peer-talk analysis.",
    },
    {
        "rank": 22,
        "period": "2023",
        "id": "2023_v18i4_10.1007_s11412-023-09414-z_Studying_teacher_withitness_in_the_wild_comparing_a_mirroring_and_an_alerting_amp_guiding_",
        "rationale": "Extends dashboard-based interaction analysis to authentic classroom withitness and intervention workload.",
    },
    {
        "rank": 23,
        "period": "2025",
        "id": "2025_v20i4_10.1007_s11412-025-09451-w_Accomplishing_collaboration_at_scale_How_professionals_jointly_frame_problems_on_Stack_Ove",
        "rationale": "Shows how large-scale asynchronous collaboration can be analyzed through trace ethnography and sequential framing practices.",
    },
    {
        "rank": 24,
        "period": "2014",
        "id": "ijCSCL_9_4_4",
        "rationale": "Innovative coding of uncertainty as an interactional resource linked to learning in computer-mediated discourse.",
    },
]

OUTPUT_PATH = "reports/cscl_interaction_analysis_article_selections_2006_2025.docx"


def format_authors(authors):
    if isinstance(authors, list):
        return ", ".join(authors)
    return authors or ""


store = load_store()
doc = Document()
doc.add_heading("Selected Contributions to the Analysis of Collaborative Interaction, 2006-2025", level=0)
doc.add_paragraph(
    "This document lists 24 non-editorial articles selected as especially significant contributions to "
    "the analysis of collaborative interaction in computer-supported settings. Entries are presented in "
    "ranked order based on their apparent analytic significance and influence as inferred from the reviewed summaries."
)
doc.add_paragraph(f"Generated on {date.today().isoformat()}")

doc.add_heading("Selection methodology", level=1)
doc.add_paragraph(
    "These articles were selected through summary-based expert screening of non-editorial papers from 2006-2025. "
    "The review used article titles, summaries, and coded methodology, unit-of-analysis, technology, and theory fields "
    "to identify papers that appeared to make especially strong contributions to analyzing collaborative interaction in computer-supported settings."
)
doc.add_paragraph(
    "Priority was given to articles that introduced or substantially advanced analytic frameworks, coding schemes, "
    "multimodal or sequential methods, network-analytic or learning-analytics approaches, orchestration analytics, "
    "or new constructs for interpreting collaborative discourse and interaction. Papers were ranked higher when they "
    "appeared to change how researchers can represent, trace, compare, or explain collaborative interaction processes."
)
doc.add_paragraph(
    "The ranking is judgment-based and derived from the available summaries rather than from citation counts or a formal "
    "bibliometric review. It should be interpreted as a theoretically and methodologically informed screening of likely significance, "
    "not a definitive historical measure of influence."
)

for item in SELECTIONS:
    article = store[item["id"]]
    doc.add_heading(f"{item['rank']}. {article.title or article.id}", level=2)

    details = doc.add_paragraph()
    details.add_run("Rank: ").bold = True
    details.add_run(str(item["rank"]))
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
    details.add_run("\n")
    details.add_run("Methodology: ").bold = True
    details.add_run(article.methodology_primary or "")
    if article.methodology_secondary:
        details.add_run(f" ({', '.join(article.methodology_secondary)})")
    details.add_run("\n")
    details.add_run("Unit of analysis: ").bold = True
    details.add_run(article.unit_of_analysis_primary or "")
    if article.unit_of_analysis_secondary:
        details.add_run(f" ({', '.join(article.unit_of_analysis_secondary)})")
    details.add_run("\n")
    details.add_run("Technology: ").bold = True
    details.add_run(article.technology_primary or "")
    if article.technology_secondary:
        details.add_run(f" ({', '.join(article.technology_secondary)})")

    rationale = doc.add_paragraph()
    rationale.add_run("Why selected: ").bold = True
    rationale.add_run(item["rationale"])

    summary = doc.add_paragraph()
    summary.add_run("Summary: ").bold = True
    summary.add_run((article.summary_haiku or "").replace("# Summary ", "").strip())


doc.save(OUTPUT_PATH)
print(f"Saved {OUTPUT_PATH}")
