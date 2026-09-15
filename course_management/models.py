from django.db import models
from usermanagement.models import *

# Create your models here.
class CourseType(models.Model):
    name = models.CharField(max_length=40)
    code = models.CharField(max_length=20)
    status = models.IntegerField(default=1)
    class Meta:
        db_table = 'course_course_type'


class CourseCategory(models.Model):
    category = models.CharField(max_length=70)
    code = models.CharField(max_length=20)
    status = models.IntegerField(default=1)
    priority = models.IntegerField(null=True)
    class Meta:
        db_table = 'course_course_category'


class CourseDegree(models.Model):
    name = models.CharField(max_length=30)
    status = models.IntegerField(default=1)
    class Meta:
        db_table = 'course_degree'


class CourseAdmittedBatch(models.Model):
    name = models.CharField(max_length=30)
    status = models.IntegerField(default=1)
    class Meta:
        db_table = 'course_admitted_batch'


class CourseLevels(models.Model):
    level = models.CharField(max_length=50)
    code = models.CharField(max_length=20)
    status = models.IntegerField(default=1)
    course_type_id = models.ForeignKey(CourseType, on_delete=models.CASCADE, null=True)
    program_level = models.ForeignKey('program.ProgramLevel', on_delete=models.CASCADE, null=True)
    class Meta:
        db_table = 'course_levels'


class CourseHeader(models.Model):
    status = models.BooleanField(default=1)
    program_status = models.BooleanField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_user_id')
    program = models.ForeignKey('program.Programs', on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'course_course_header'


class CourseStatusLevels(models.Model):
    title = models.CharField(max_length=200)
    class Meta:
        db_table = 'course_status_levels'


class CourseStatus(models.Model):
    name = models.CharField(max_length=200)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = 'course_status'


class Campus(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    campus_code = models.CharField(max_length=10, null=True)
    status = models.BooleanField(default=0)
    icon = models.ImageField(upload_to='campus_icons', null=True)
    class Meta:
        db_table = "u_campus"


class Institutions(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=0)
    institution_code = models.CharField(max_length=100, null=True)

    class Meta:
        db_table = "u_institutions"
    def __str__(self):
        return self.name


class CampusInstitutionMapping(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institutions, on_delete=models.CASCADE)
    class Meta:
        db_table = "u_campus_institution_mapping"


class UCourse(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=0)
    full_name = models.TextField(max_length=100, null=True)

    class Meta:
        db_table = "u_courses"
    def __str__(self):
        return self.name


class CampusInstitutionCourseMapping(models.Model):
    institution = models.ForeignKey(Institutions, on_delete=models.CASCADE)
    course = models.ForeignKey(UCourse, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "u_campus_institution_course_mapping"


class DepartmentInstituteCodes(models.Model):
    name = models.CharField(max_length=70, null=True)
    dept_inst = models.CharField(max_length=70)
    dept_code = models.CharField(max_length=5)
    status = models.BooleanField(default=1)
    course_code_doaa = models.CharField(max_length=70, null=True)

    class Meta:
        db_table = 'u_department_institute_code'


class CampusInstitutionCourseDepartmentMapping(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    institution = models.ForeignKey(Institutions, on_delete=models.CASCADE)
    course = models.ForeignKey(UCourse, on_delete=models.CASCADE)
    department = models.ForeignKey(DepartmentInstituteCodes, on_delete=models.CASCADE, null=True)
    class Meta:
        db_table = "u_campus_institution_course_department_mapping"


class Course(models.Model):
    admitted_batch = models.ForeignKey(CourseAdmittedBatch, on_delete=models.CASCADE, null=True)
    degree = models.ForeignKey(CourseDegree, on_delete=models.CASCADE, null=True)
    course_header = models.ForeignKey(CourseHeader, on_delete=models.CASCADE, null=True)
    program = models.ForeignKey('program.Programs', on_delete=models.CASCADE, null=True)
    program_type = models.ForeignKey('program.ProgramLevel', on_delete=models.CASCADE, null=True)
    course_name = models.TextField(null=True)
    course_type = models.ForeignKey(CourseType, on_delete=models.CASCADE)
    level_of_course = models.ForeignKey(CourseLevels, on_delete=models.CASCADE, null=True)
    course_category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, null=True)
    desc1 = models.TextField(null=True)
    instruction_plan = models.FileField(upload_to='media/course/', max_length=4000)
    instruction_plan_practical = models.FileField(upload_to='media/course/', null=True, max_length=4000)
    active_step = models.IntegerField(null=True)
    version = models.DecimalField(null=True, decimal_places=1, max_digits=4)
    version_status = models.BooleanField(default=0)
    total_no_of_contact_hours = models.TextField(null=True)
    L = models.TextField(null=True)
    T = models.TextField(null=True)
    P = models.TextField(null=True)
    S = models.TextField(null=True)
    J = models.TextField(null=True)
    C = models.TextField(null=True)
    pre_requisites = models.BooleanField(default=0)
    pre_requisites_codes = models.TextField(null=True)
    co_requisites = models.BooleanField(default=0)
    co_requisites_codes = models.TextField(null=True)
    alternative_exposure = models.TextField(null=True)
    course_descrption = models.TextField(null=True)
    specific_instruction_objectives = models.TextField(null=True)
    course_code = models.CharField(max_length=100, null=True)
    practical_referance = models.JSONField(null=True)
    practical_topic_mapping = models.JSONField(null=True)
    project_topic = models.JSONField(null=True)
    course_outcome = models.JSONField(null=True)
    course_objectives = models.JSONField(null=True)
    course_unit_name = models.JSONField(null=True)
    course_unit_contact_hours = models.JSONField(null=True)
    course_unit_description = models.JSONField(null=True)
    course_unit_outcomes = models.JSONField(null=True)
    course_unit_outcome_levels = models.JSONField(null=True)
    course_unit_pedagogy_tools = models.JSONField(null=True)

    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_created_by')
    modified = models.DateTimeField(auto_now_add=True, null=True)
    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='course_modified_by')
    dept_code = models.ForeignKey(DepartmentInstituteCodes, on_delete=models.CASCADE, null=True)
    pass_fail = models.BooleanField(default=0)
    faculty = models.BooleanField(default=1)
    sdg = models.JSONField(null=True)
    sdg_description = models.TextField(null=True)
    form_type = models.IntegerField(null=True)
    status = models.ForeignKey(CourseStatusLevels, on_delete=models.CASCADE, null=True)
    bos_date = models.DateTimeField(null=True)
    ac_council_number = models.CharField(null=True, max_length=100)
    ac_council_date = models.DateTimeField(null=True)
    is_delete = models.BooleanField(default=0)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='course_deleted_by')
    deleted_time = models.DateTimeField(null=True)
    mode_of_delivery = models.CharField(max_length=100, null=True)

    L_hours = models.TextField(null=True)
    T_hours = models.TextField(null=True)
    P_hours = models.TextField(null=True)
    S_hours = models.TextField(null=True)
    J_hours = models.TextField(null=True)
    proposed_name = models.CharField(null=True, max_length=250)

    is_copied = models.BooleanField(default=0)

    course_status = models.ForeignKey(CourseStatus, on_delete=models.CASCADE, null=True)
    audit = models.IntegerField(null=True)
    assign_faculty = models.IntegerField(null=True)

    internal_maxmarks = models.FloatField(null=True)
    external_maxmarks = models.FloatField(null=True)

    internal_pass_marks = models.FloatField(null=True)
    external_pass_marks = models.FloatField(null=True)
    eval_diff_marks = models.FloatField(null=True)
    overall_pass_marks = models.FloatField(null=True)

    re_internal_pass_marks = models.FloatField(null=True)
    re_external_pass_marks = models.FloatField(null=True)
    re_eval_diff_marks = models.FloatField(null=True)
    re_overall_pass_marks = models.FloatField(null=True)
    regulations = models.CharField(max_length=250, null=True)
    anti_requisites = models.BooleanField(default=0)
    anti_requisites_codes = models.TextField(null=True)

    course_code_exists = models.BooleanField(null=True)

    pending_at = models.ForeignKey(User, on_delete=models.CASCADE, related_name='Course_pending_at', null=True)


    class Meta:
        db_table = 'course'


class CourseCampusMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'course_campus_mapping'


class CourseDepartmentMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    department = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    c_i_c_d = models.ForeignKey(CampusInstitutionCourseDepartmentMapping, on_delete=models.CASCADE, null=True)
    class Meta:
        db_table = 'course_department_mapping'


class CourseInstituteMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    institute = models.CharField(max_length=255, null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'course_institute_mapping'


class CoursePrerequestiesMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    prerequesti = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_prerequesting_mapping')
    created = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'course_prerequesties_mapping'

class CourseCorequestiesMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    corequesti = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_corequesting_mapping')
    created = models.DateTimeField(auto_now_add=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'course_corequesties_mapping'


class CourseUserMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    course_header = models.ForeignKey(CourseHeader, on_delete=models.CASCADE, null=True)
    to_user = models.ForeignKey(User, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_created_user_id')
    course_status_level = models.ForeignKey(CourseStatusLevels, on_delete=models.CASCADE, related_name='course_status_level', null=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    is_edit = models.IntegerField(null=True)
    comment = models.TextField(null=True)
    to_user_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, related_name='cour_to_user_group')
    user_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(null=True, default=1)
    assigned_time = models.DateTimeField(null=True)
    bos_aproved_date = models.DateField(null=True)
    doaa_aproved_date = models.DateField(null=True)

    class Meta:
        db_table = 'course_user_mapping'


class CourseOutcome(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    course_outcome = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'course_outcome'


class CourseUnits(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    unit_no = models.IntegerField()
    class Meta:
        db_table = 'course_units'


class PedagogyTools(models.Model):
    name = models.CharField(max_length=50)
    class Meta:
        db_table = 'course_pedagogy_tools'


class CourseSyllabus(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    unit_name = models.TextField(null=True)
    short_title = models.CharField(max_length=500, null=True)
    number_of_contact_hours = models.CharField(max_length=10, null=True)
    version = models.DecimalField(null=True, decimal_places=1, max_digits=4)
    outcome_1 = models.TextField(null=True)
    level_1 = models.TextField(null=True)
    outcome_2 = models.TextField(null=True)
    level_2 = models.TextField(null=True)
    outcome_3 = models.TextField(null=True)
    level_3 = models.TextField(null=True)
    outcome_4 = models.TextField(null=True)
    level_4 = models.TextField(null=True)
    outcome_5 = models.TextField(null=True)
    level_5 = models.TextField(null=True)
    pedagogy_tools = models.JSONField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    course_unit = models.ForeignKey(CourseUnits, on_delete=models.CASCADE, null=True)
    class Meta:
        db_table = 'course_syllabus'


class CourseProposedPrograms(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    program_name = models.JSONField(null=True)
    branch_code = models.JSONField(null=True)
    psos = models.IntegerField(null=True)
    pos = models.IntegerField(null=True)

    class Meta:
        db_table = 'course_proposed_programs'


class CourseSyllabusTopicsMapping(models.Model):
    course_syllabus = models.ForeignKey(CourseSyllabus, on_delete=models.CASCADE)
    title = models.TextField(null=True)
    duration = models.IntegerField(null=True)

    class Meta:
        db_table = 'course_syllabus_topics_mapping'


class SyllabusType(models.Model):
    name = models.CharField(max_length=20)
    class Meta:
        db_table = 'course_syllabus_type'

class CourseSyllabusPractical(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    syllabus_type = models.ForeignKey(SyllabusType, on_delete=models.CASCADE)
    topic = models.TextField()
    version = models.DecimalField(null=True, decimal_places=1, max_digits=4)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    duration = models.FloatField(null=True)

    class Meta:
        db_table = 'course_syllabus_practical'

class CourseBooks(models.Model):
    title = models.TextField()
    author = models.TextField(null=True)
    publisher = models.TextField(null=True)
    place_of_publication = models.TextField(null=True)
    year = models.IntegerField(null=True)
    edition = models.TextField(null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    isbn = models.TextField(null=True)
    unit_mapping = models.TextField(null=True)
    class Meta:
        db_table = 'course_books'

class References(models.Model):
    title = models.TextField(null=True)
    author = models.TextField(null=True)
    publisher = models.TextField(null=True)
    place_of_publication = models.TextField(null=True)
    year = models.IntegerField(null=True)
    edition = models.TextField(null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    isbn = models.TextField(null=True)
    unit_mapping = models.TextField(null=True)
    url = models.TextField(null=True)
    class Meta:
        db_table = 'course_reference'

class CourseCoPoPso(models.Model):
    co = models.IntegerField()
    po = models.JSONField(null=True)
    pso = models.JSONField(null=True)
    po1 = models.IntegerField(null=True)
    po2 = models.IntegerField(null=True)
    po3 = models.IntegerField(null=True)
    po4 = models.IntegerField(null=True)
    po5 = models.IntegerField(null=True)
    po6 = models.IntegerField(null=True)
    po7 = models.IntegerField(null=True)
    po8 = models.IntegerField(null=True)
    po9 = models.IntegerField(null=True)
    po10 = models.IntegerField(null=True)
    po11 = models.IntegerField(null=True)
    po12 = models.IntegerField(null=True)
    pso1 = models.IntegerField(null=True)
    pso2 = models.IntegerField(null=True)
    pso3 = models.IntegerField(null=True)
    pso4 = models.IntegerField(null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    proposed_program = models.ForeignKey(CourseProposedPrograms, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = 'course_co_po_pso'


class JournalBooks(models.Model):
    title = models.TextField(null=True)
    author = models.TextField(null=True)
    year = models.TextField(null=True)
    doi_url = models.TextField(null=True)
    pages = models.IntegerField(null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    unit_mapping = models.TextField(null=True)
    class Meta:
        db_table = 'course_journal_books'

class Websites(models.Model):
    name_website = models.TextField(null=True)
    last_accessed = models.DateTimeField(auto_now_add=True)
    website_url = models.URLField(null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    unit_mapping = models.TextField(null=True)
    class Meta:
        db_table = 'course_websites'


class CourseSDG(models.Model):
    go_id = models.CharField(max_length=255)
    go_key = models.TextField()
    go_description = models.TextField(null=True)

    class Meta:
        db_table = 'course_sdg'


class CourseSyllabusPDF(models.Model):
    school = models.TextField(null=True)
    department = models.TextField(null=True)
    program = models.TextField(null=True)
    admitted_batch = models.TextField(null=True)
    course_code = models.JSONField(null=True)
    file = models.FileField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    class Meta:
        db_table = 'course_syllabus_pdf'


class CourseTrackingStatus(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='CourseTrackingStatus_course', null=True)
    course_status = models.ForeignKey(CourseStatus, on_delete=models.CASCADE, related_name='CourseTrackingStatus_course_status', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='CourseTrackingStatus_user')
    description = models.TextField(null=True)
    first_name = models.CharField(max_length=250, null=True)
    emp_id = models.CharField(max_length=15, null=True)
    designation = models.CharField(max_length=100, null=True)
    campus = models.CharField(max_length=100, null=True)
    institution = models.CharField(max_length=100, null=True)
    department = models.CharField(max_length=100, null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    created = models.DateTimeField(auto_now_add=True)
    attachment = models.FileField(null=True, max_length=1000)

    class Meta:
        db_table = "course_tracking_status"


class CourseAcknowledgment(models.Model):
    self_submitted_date = models.DateTimeField(null=True)
    doaa_submitted_date = models.DateTimeField(null=True)
    self_acknowldgement_status = models.IntegerField(null=True)
    doaa_acknowldgement_status = models.IntegerField(null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acknowldgement_user_id')
    doaa = models.ForeignKey(User, on_delete=models.CASCADE, related_name='acknowldgement_doaa', null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='CourseAcknowledgment_course', null=True)
    course_status = models.ForeignKey(CourseStatus, on_delete=models.CASCADE, related_name='CourseAcknowledgment_course_status', null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_acknowldgement'


class CourseTrackingUserMapping(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='CourseTrackingUserMapping_course', null=True)
    course_tracking_status = models.ForeignKey(CourseTrackingStatus, on_delete=models.CASCADE, related_name='CourseTrackingUserMapping_tracking_status', null=True)

    course_respond_status = models.ForeignKey(CourseTrackingStatus, on_delete=models.CASCADE, related_name='CourseTrackingUserMapping_respond_status', null=True)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='CourseTrackingUserMapping_user')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='CourseTrackingUserMapping_to_user', null=True)
    type = models.IntegerField()
    is_seen = models.BooleanField(default=False)
    seen_time = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    is_edit = models.IntegerField(default=False)
    is_respond = models.BooleanField(default=False)
    to_user_group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "course_tracking_user_mapping"


class CourseDetailsHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    about_course = models.JSONField(blank=True, null=True)
    syllabus = models.JSONField(blank=True, null=True)
    syllabus_topics = models.JSONField(blank=True, null=True)
    syllabus_practicals = models.JSONField(blank=True, null=True)
    books = models.JSONField(blank=True, null=True)
    reference = models.JSONField(blank=True, null=True)
    co_po_mapping = models.JSONField(blank=True, null=True)
    course_proposed_programs = models.JSONField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_details_history'


class CourseRevertLog(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='revert_logs', null=True)
    reverted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reverted_by')
    approved_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_revert_approved_by', null=True)
    reverted_from_status = models.ForeignKey(CourseStatus, on_delete=models.CASCADE, related_name='course_revert_from_status', null=True)
    ip_address = models.GenericIPAddressField(null=True)
    reverted_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_revert_log'