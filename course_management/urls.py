from django.urls import path
from . import views

urlpatterns = [
    path('courses', views.courses, name='courses'),
    path('courses/create_course', views.create_course, name='create_course'),
    path('courses/create_course/<str:id>', views.create_course, name='edit_course'),
    path('courses/<str:id>', views.course_details, name='course_details'),
    path('csmc/check_course_code', views.check_course_code, name='check_course_code'),
    path('csmc/get_levels_by_ptype', views.get_levels_by_ptype, name='get_levels_by_ptype'),
]
