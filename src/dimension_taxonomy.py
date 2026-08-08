from dataclasses import dataclass


@dataclass(frozen=True)
class TaxonomyDimension:
    name: str
    options: tuple[str, ...]


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
    ),
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
    ),
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
    ),
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
    ),
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
    ),
)

AI_LLM_INVOLVEMENT = TaxonomyDimension(
    name="ai_llm_involvement",
    options=(
        "none",
        "llm_supported_writing",
        "llm_supported_feedback",
        "llm_supported_assessment",
        "llm_supported_orchestration",
        "llm_supported_analytics",
        "llm_as_learning_partner",
    ),
)


TAXONOMY = {
    "methodology": METHODOLOGY,
    "unit_of_analysis": UNIT_OF_ANALYSIS,
    "pedagogy": PEDAGOGY,
    "technology": TECHNOLOGY,
    "theory": THEORY,
    "ai_llm_involvement": AI_LLM_INVOLVEMENT,
}
