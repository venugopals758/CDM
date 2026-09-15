from django.contrib import admin
from .models import (
    CourseType, CourseCategory, CourseLevels, CourseDegree, CourseAdmittedBatch,
    CourseStatusLevels, CourseStatus, SyllabusType, PedagogyTools,
    Campus, Institutions, UCourse, DepartmentInstituteCodes,
    CampusInstitutionMapping, CampusInstitutionCourseMapping, CampusInstitutionCourseDepartmentMapping,
)


@admin.register(CourseType)
class CourseTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'status')


@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'code', 'priority', 'status')


@admin.register(CourseLevels)
class CourseLevelsAdmin(admin.ModelAdmin):
    list_display = ('id', 'level', 'code', 'course_type_id', 'program_level', 'status')


@admin.register(CourseDegree)
class CourseDegreeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status')


@admin.register(CourseAdmittedBatch)
class CourseAdmittedBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status')


@admin.register(CourseStatusLevels)
class CourseStatusLevelsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')


@admin.register(CourseStatus)
class CourseStatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'status')


@admin.register(SyllabusType)
class SyllabusTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(PedagogyTools)
class PedagogyToolsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(Campus)
class CampusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'campus_code', 'status')


@admin.register(Institutions)
class InstitutionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'institution_code', 'status')


@admin.register(UCourse)
class UCourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'full_name', 'status')


@admin.register(DepartmentInstituteCodes)
class DepartmentInstituteCodesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'dept_code', 'dept_inst', 'course_code_doaa', 'status')
    search_fields = ('name', 'dept_code', 'dept_inst')


@admin.register(CampusInstitutionMapping)
class CampusInstitutionMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'campus', 'institution')


@admin.register(CampusInstitutionCourseMapping)
class CampusInstitutionCourseMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'campus', 'institution', 'course')


@admin.register(CampusInstitutionCourseDepartmentMapping)
class CampusInstitutionCourseDepartmentMappingAdmin(admin.ModelAdmin):
    list_display = ('id', 'campus', 'institution', 'course', 'department')
