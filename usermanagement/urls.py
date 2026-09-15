from django.urls import path,include
from . import views,admin
from django.conf import settings

urlpatterns = [
    path('switch_role/<str:group_id>',views.switch_role,name="switch_role"),
    path('dashboard', views.dashboard, name='dashboard'),
    path('not_found',views.not_found,name='not_found'),
    path('ulogin/<str:emp_id>',views.ulogin,name="ulogin"),
    path('userlogout', views.userlogout, name='userlogout'),

    # admin - schools
    path('admin/schools', admin.schools, name='admin_schools'),
    path('admin/schools/save', admin.save_school, name='admin_save_school'),
    path('admin/schools/toggle_status', admin.toggle_school_status, name='admin_toggle_school_status'),

    # admin - streams
    path('admin/streams', admin.streams, name='admin_streams'),
    path('admin/streams/save', admin.save_stream, name='admin_save_stream'),
    path('admin/streams/toggle_status', admin.toggle_stream_status, name='admin_toggle_stream_status'),

    # admin - departments
    path('admin/departments', admin.departments, name='admin_departments'),
    path('admin/departments/save', admin.save_department, name='admin_save_department'),
    path('admin/departments/toggle_status', admin.toggle_department_status, name='admin_toggle_department_status'),

    # admin - users
    path('admin/users', admin.users, name='admin_users'),
    path('admin/users/add', admin.add_user, name='admin_add_user'),
    path('admin/users/search_employee', admin.search_employee, name='admin_search_employee'),
    path('admin/users/get_employee_data', admin.get_employee_data, name='admin_get_employee_data'),

    # admin - bos cochair / hod - department mapping
    path('admin/bos_cochair_mappings', admin.bos_cochair_mappings, name='admin_bos_cochair_mappings'),
    path('admin/bos_cochair_mappings/save', admin.save_bos_cochair_mapping, name='admin_save_bos_cochair_mapping'),
    path('admin/bos_cochair_mappings/toggle_status', admin.toggle_bos_cochair_mapping_status, name='admin_toggle_bos_cochair_mapping_status'),

    # admin - bos chair - school mapping
    path('admin/bos_chair_school_mappings', admin.bos_chair_school_mappings, name='admin_bos_chair_school_mappings'),
    path('admin/bos_chair_school_mappings/save', admin.save_bos_chair_school_mapping, name='admin_save_bos_chair_school_mapping'),
    path('admin/bos_chair_school_mappings/toggle_status', admin.toggle_bos_chair_school_mapping_status, name='admin_toggle_bos_chair_school_mapping_status'),

    # admin - program level / school - duration & exit plan mapping
    path('admin/duration_exit_plans', admin.duration_exit_plans, name='admin_duration_exit_plans'),
    path('admin/duration_exit_plans/save', admin.save_duration_exit_plan, name='admin_save_duration_exit_plan'),
    path('admin/duration_exit_plans/toggle_status', admin.toggle_duration_exit_plan_status, name='admin_toggle_duration_exit_plan_status'),

    # admin - tracks
    path('admin/tracks', admin.tracks, name='admin_tracks'),
    path('admin/tracks/save', admin.save_track, name='admin_save_track'),
    path('admin/tracks/toggle_status', admin.toggle_track_status, name='admin_toggle_track_status'),

    # admin - program level / school - track mapping
    path('admin/track_school_mappings', admin.track_school_mappings, name='admin_track_school_mappings'),
    path('admin/track_school_mappings/save', admin.save_track_school_mapping, name='admin_save_track_school_mapping'),
    path('admin/track_school_mappings/toggle_status', admin.toggle_track_school_mapping_status, name='admin_toggle_track_school_mapping_status'),
]
