from dataclasses import dataclass


@dataclass(frozen=True)
class TaxonomyDimension:
    name: str
    options: tuple[str, ...]
    glosses: dict = None  # type: ignore[assignment]

    def prompt_block(self) -> str:
        """Return a formatted options+gloss list for use in LLM prompts."""
        lines = []
        for option in self.options:
            gloss = (self.glosses or {}).get(option, "")
            suffix = f": {gloss}" if gloss else ""
            lines.append(f"    - {option}{suffix}")
        return "\n".join(lines)


METHODOLOGY = TaxonomyDimension(
    name="analysis_methodology",
    options=(
        "descriptive_statistics",
        "inferential_statistics",
        "multilevel_modeling",
        "social_network_analysis",
        "discourse_analysis",
        "interaction_analysis",
        "computational_linguistics_nlp",
        "sequence_process_mining",
        "learning_analytics",
        "experimental_quasi_experimental",
        "design_based_research",
        "ethnographic_case_study",
        "mixed_methods",
        "content_analysis",
        "other",
    ),
    glosses={
        "descriptive_statistics": "Frequencies, means, distributions; no inferential testing",
        "inferential_statistics": "Hypothesis testing, ANOVA, regression, correlation with significance",
        "multilevel_modeling": "Hierarchical or mixed-effects models accounting for nested data",
        "social_network_analysis": "Graph-based analysis of interaction ties and centrality",
        "discourse_analysis": "Linguistic or rhetorical analysis of talk and text",
        "interaction_analysis": "Micro-analytic coding of moment-by-moment collaborative episodes",
        "computational_linguistics_nlp": "Automated text processing: topic models, embeddings, NLP pipelines",
        "sequence_process_mining": "Temporal or sequential pattern extraction from log/trace data",
        "learning_analytics": "Trace data from digital platforms used to model or predict learning",
        "experimental_quasi_experimental": "Controlled or quasi-controlled comparison of conditions or groups",
        "design_based_research": "Iterative design and study of an intervention in naturalistic settings",
        "ethnographic_case_study": "In-depth qualitative study of a bounded context with observation or interview",
        "mixed_methods": "Combines quantitative and qualitative data collection and analysis",
        "content_analysis": "Systematic coding of documents, posts, or artifacts using a scheme",
        "other": "Does not fit any above; explain in coding_notes",
    },
)

UNIT_OF_ANALYSIS = TaxonomyDimension(
    name="unit_of_analysis",
    options=(
        "individual_learner",
        "dyad_small_group",
        "classroom_cohort",
        "teacher_facilitation",
        "community_network",
        "artifact_discourse_trace",
        "cross_level_multilevel",
        "other",
    ),
    glosses={
        "individual_learner": "Outcomes or behaviors of single students",
        "dyad_small_group": "Pairs or groups of 2–6 collaborating learners",
        "classroom_cohort": "A whole class or cohort treated as the analytical unit",
        "teacher_facilitation": "Teacher moves, awareness, or orchestration decisions",
        "community_network": "Large-scale community, online network, or population of actors",
        "artifact_discourse_trace": "Documents, posts, scripts, or logs analyzed as the primary object",
        "cross_level_multilevel": "Simultaneously analyzes individual and group (or group and class) levels",
        "other": "Does not fit any above; explain in coding_notes",
    },
)

PEDAGOGY = TaxonomyDimension(
    name="pedagogical_approach",
    options=(
        "knowledge_building",
        "collaboration_scripts",
        "inquiry_problem_based_learning",
        "argumentation",
        "peer_review_feedback",
        "teacher_orchestrated_discussion",
        "self_peer_regulation",
        "community_of_practice",
        "other",
    ),
    glosses={
        "knowledge_building": "Scardamalia & Bereiter model: community-driven idea improvement",
        "collaboration_scripts": "Structured roles, turn sequences, or scripts regulating collaboration",
        "inquiry_problem_based_learning": "Open-ended questions or problems drive learning activity",
        "argumentation": "Explicit construction, critique, or negotiation of claims and evidence",
        "peer_review_feedback": "Students give or receive structured feedback on each other's work",
        "teacher_orchestrated_discussion": "Teacher actively shapes whole-class or small-group dialogue",
        "self_peer_regulation": "Students monitor, plan, or regulate their own or each other's learning",
        "community_of_practice": "Learning through participation in an authentic professional community",
        "other": "Does not fit any above; explain in coding_notes",
    },
)

TECHNOLOGY = TaxonomyDimension(
    name="technological_support",
    options=(
        "asynchronous_forum",
        "synchronous_chat_video",
        "wiki_knowledge_base",
        "shared_workspace_canvas",
        "tabletop_tangible_interface",
        "awareness_dashboard",
        "collaboration_scripting_tools",
        "multimodal_sensors_eye_tracking",
        "none_minimal_technology",
        "other",
    ),
    glosses={
        "asynchronous_forum": "Discussion boards, blogs, or thread-based tools used across time",
        "synchronous_chat_video": "Real-time text chat, video conferencing, or live messaging",
        "wiki_knowledge_base": "Collaboratively edited knowledge repositories (e.g., Knowledge Forum, wikis)",
        "shared_workspace_canvas": "Co-editing tools, shared whiteboards, or collaborative document spaces",
        "tabletop_tangible_interface": "Physical or tangible computing surfaces supporting face-to-face collaboration",
        "awareness_dashboard": "Tools that display group activity or progress to learners or teachers",
        "collaboration_scripting_tools": "Software that enacts roles, sequences, or prompts for structured collaboration",
        "multimodal_sensors_eye_tracking": "Physiological, gaze, gesture, or movement sensors capturing embodied interaction",
        "none_minimal_technology": "Technology is not the focus; collaboration is face-to-face or technology-peripheral",
        "other": "Does not fit any above; explain in coding_notes",
    },
)

THEORY = TaxonomyDimension(
    name="theoretical_framework",
    options=(
        "sociocultural",
        "dialogic",
        "socio_cognitive",
        "knowledge_building_theory",
        "activity_theory",
        "communities_of_practice",
        "distributed_cognition",
        "information_processing",
        "critical_pragmatic",
        "other",
    ),
    glosses={
        "sociocultural": "Vygotsky-lineage: learning as socially and culturally mediated activity",
        "dialogic": "Bakhtin-lineage: meaning made through multi-voiced dialogue and uptake",
        "socio_cognitive": "Piaget-influenced: collaborative conflict and explanation drive cognitive change",
        "knowledge_building_theory": "Scardamalia & Bereiter: progressive discourse advances collective knowledge",
        "activity_theory": "Engeström: contradictions within activity systems drive development",
        "communities_of_practice": "Lave & Wenger: learning through legitimate peripheral participation",
        "distributed_cognition": "Hutchins: cognition is spread across people, artifacts, and environment",
        "information_processing": "Cognitive load, working memory, schema; individual mental architecture",
        "critical_pragmatic": "Power, equity, or justice lens on participation and knowledge",
        "other": "Does not fit any above; explain in coding_notes",
    },
)

AI_LLM_INVOLVEMENT = TaxonomyDimension(
    name="ai_llm_involvement",
    options=(
        "none",
        "ai_supported_non_llm",
        "llm_supported_writing",
        "llm_supported_feedback",
        "llm_supported_assessment",
        "llm_supported_orchestration",
        "llm_supported_analytics",
        "llm_as_learning_partner",
        "other",
    ),
    glosses={
        "none": "No AI or LLM involvement in the study design or technology",
        "ai_supported_non_llm": "AI mechanisms used (e.g., rule-based agents, recommender systems, ML classifiers) but not LLMs",
        "llm_supported_writing": "LLM used by participants to draft, edit, or generate text",
        "llm_supported_feedback": "LLM provides automated formative feedback to learners",
        "llm_supported_assessment": "LLM used to score, classify, or evaluate learning artifacts",
        "llm_supported_orchestration": "LLM acts as a conversational agent, tutor, or discussion partner",
        "llm_supported_analytics": "LLM or AI used for analysis, coding, or pattern detection in research",
        "llm_as_learning_partner": "LLM is the primary collaborator or interlocutor for learners",
        "other": "Does not fit any above; explain in coding_notes",
    },
)


TAXONOMY = {
    "methodology": METHODOLOGY,
    "unit_of_analysis": UNIT_OF_ANALYSIS,
    "pedagogy": PEDAGOGY,
    "technology": TECHNOLOGY,
    "theory": THEORY,
    "ai_llm_involvement": AI_LLM_INVOLVEMENT,
}
