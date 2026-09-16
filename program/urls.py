from django.urls import path
from . import bosco
from . import bosc
from . import hod
from . import nirf
from . import forms
from . import functions
from . import views

urlpatterns = [
    # nirf
    path('programs/nirf_data', nirf.nirf_data, name='nirf_data'),

    # bosco
    path('programs', bosco.programs, name='programs'),
    path('programs/program_details/<str:id>', views.program_details, name='program_details'),
    path('programs/final_preview/<str:id>', bosco.final_preview, name='final_preview'),
    path('programs/initiate_program/<str:id>', bosco.initiate_program, name='initiate_program'),
    path('programs/bosco_forward_program/<str:id>', bosco.bosco_forward_program, name='bosco_forward_program'),
    path('programs/delete_program', bosco.delete_program, name='delete_program'),
    path('programs/course_requests', bosco.course_requests, name='bosco_course_requests'),
    path('programs/course_request_details/<str:id>', bosco.course_request_details, name='course_request_details'),
    path('programs/initiate_course_request', bosco.initiate_course_request, name='initiate_course_request'),
    path('programs/assign_course_request', bosco.assign_course_request, name='assign_course_request'),

    # bosc
    path('programs/bosc_forward_program/<str:id>', bosc.bosc_forward_program, name='bosc_forward_program'),

    # hod
    path('programs/save_course_request', hod.save_course_request, name='save_course_request'),
    path('programs/get_bosco_for_department', hod.get_bosco_for_department, name='get_bosco_for_department'),
    path('programs/delete_course_request', hod.delete_course_request, name='delete_course_request'),
    path('programs/hod_forward_program/<str:id>', hod.hod_forward_program, name='hod_forward_program'),
    path('programs/map_courses', hod.map_courses, name='map_courses'),
    path('programs/hod_course_request_details/<str:id>', hod.course_request_details, name='hod_course_request_details'),
    path('programs/respond_course_request', hod.respond_course_request, name='respond_course_request'),

    # forms
    path('programs/add_program', forms.add_program, name='add_program'),
    path('programs/edit_program/<str:id>', forms.edit_program, name='edit_program'),
    path('programs/save_basic_details', forms.save_basic_details, name='save_basic_details'),
    path('programs/save_program_structure', forms.save_program_structure, name='save_program_structure'),
    path('programs/add_program_structure_row', forms.add_program_structure_row, name='add_program_structure_row'),
    path('programs/update_program_structure_row', forms.update_program_structure_row, name='update_program_structure_row'),
    path('programs/delete_program_structure_row', forms.delete_program_structure_row, name='delete_program_structure_row'),
    path('programs/save_program_outcomes', forms.save_program_outcomes, name='save_program_outcomes'),
    path('programs/add_program_outcome_row', forms.add_program_outcome_row, name='add_program_outcome_row'),
    path('programs/delete_program_outcome_row', forms.delete_program_outcome_row, name='delete_program_outcome_row'),
    path('programs/update_program_outcome_row', forms.update_program_outcome_row, name='update_program_outcome_row'),

    # functions
    path('programs/get_credit_levels_by_program_level', functions.get_credit_levels_by_program_level, name='get_credit_levels_by_program_level'),
    path('programs/get_duration_exit_plan', functions.get_duration_exit_plan, name='get_duration_exit_plan'),
    path('programs/get_hods_by_school', functions.get_hods_by_school, name='get_hods_by_school'),
]
