from src.store import load_store, save_store

set_corrected = {
    "ijCSCL_3_3_6": "book review",
    "2019_v14i3_10.1007_s11412-019-09308-z_A_handheld_classroom_dashboard_Teachers_perspectives_on_the_use_of_real-time_collaborative_learning_analytics": "corrected",
    "2024_v19i3_10.1007_s11412-024-09425-4_Collaborative_Problem-Solving_in_Knowledge-Rich_Domains_A_Multi-Study_Structural_Equation_": "corrected",
    "2025_v20i1_10.1007_s11412-023-09392-2_Contesting_sociocomputational_norms_Computer_programming_instructors_and_students_stancetaking_around_refactoring": "corrected",
    "2026_v21i2_10.1007_s11412-025-09464-5_A_temporal_network_approach_to_reveal_the_longitudinal_dynamics_of_CSCL_group_regulation_a": "corrected",
}

revert_ids = [
    "2019_v14i3_10.1007_s11412-019-09307-0_It_is_not_either_or_An_initial_investigation_into_combining_collaborative_and_individual_learning_using_an_ITS",
    "2019_v14i3_10.1007_s11412-019-09306-1_Supporting_classroom_orchestration_with_real-time_feedback_A_role_for_teacher_dashboards_and_real-time_agents",
    "2019_v14i3_10.1007_s11412-019-09298-y_Guiding_collaborative_revision_of_science_explanations",
    "2025_v20i1_10.1007_s11412-024-09429-0_Revealing_the_interplay_of_cognitive_meta-cognitive_and_social_processes_in_university_students_collaborative_problem_so",
]

store = load_store()
updated = []
reverted = []

for aid, value in set_corrected.items():
    if aid in store:
        store[aid].editorial = value
        updated.append(aid)

for aid in revert_ids:
    if aid in store:
        store[aid].editorial = None
        reverted.append(aid)

save_store(store)

print("updated", len(updated))
for aid in updated:
    print("  ", aid, "->", store[aid].editorial)
print("reverted", len(reverted))
for aid in reverted:
    print("  ", aid, "->", store[aid].editorial)
