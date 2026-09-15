
import os
from django.db import models
from usermanagement.models import *
from datetime import datetime
from course_management.models import *
from program.program_course_models import (
    CourseRequestStatus, CourseRequest, CourseRequestTrackingStatus, CourseRequestTrackingUserMapping,
)

class ProgramType(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'program_type'


class ProgramLevel(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'program_level'


class ProgramLevelCreditMapping(models.Model):
    program_level = models.ForeignKey(ProgramLevel, on_delete=models.CASCADE)
    minimum_credits = models.FloatField(null=True)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'program_level_credit_mapping'



class TracksHeader(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'tracks_header'


class TrackHeaderLevelSchoolMapping(models.Model):
    program_level = models.ForeignKey(ProgramLevel, on_delete=models.CASCADE)
    school = models.ForeignKey(Schools, on_delete=models.CASCADE)
    track = models.ForeignKey(TracksHeader, on_delete=models.CASCADE)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'track_header_level_school_mapping'


class ProgramSchoolDurationExitplanMapping(models.Model):
    program_level = models.ForeignKey(ProgramLevel, on_delete=models.CASCADE)
    school = models.ForeignKey(Schools, on_delete=models.CASCADE)
    duration = models.IntegerField(null=True)
    exit_plan = models.BooleanField(default=0)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'program_school_duration_exitplan_mapping'


def program_structure_path(instance, filename):
    return os.path.join(
        'programs',
        str(instance.id),
        filename
    )

class ProgramRef(models.Model):
    status = models.BooleanField(default=1)
    class Meta:
        db_table = "program_ref"

class ProgramStatus(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=0)
    class Meta:
        db_table = "program_status"

class Programs(models.Model):
    ref_no = models.CharField(max_length=15, null=True)
    code = models.CharField(max_length=20,null=True)
    minimum_credits = models.IntegerField(null=True)
    title = models.CharField(max_length=100,null=True)
    duration = models.IntegerField(null=True, blank=True)
    has_exit_plan = models.BooleanField(null=True, blank=True)
    exit_minimum_credits = models.IntegerField(null=True, blank=True)
    program_type = models.ForeignKey(ProgramType, on_delete=models.CASCADE,null=True,blank=True)
    program_level = models.ForeignKey(ProgramLevel, on_delete=models.CASCADE,null=True,blank=True)
    program_level_credits = models.FloatField(null=True,blank=True)
    status = models.BooleanField(default=1)
    program_structure_pdf = models.FileField(upload_to=program_structure_path, null=True, blank=True)
    program_structure_xl = models.FileField(upload_to=program_structure_path, null=True, blank=True)
    program_batch = models.ForeignKey(Batches, on_delete=models.CASCADE,null=True,blank=True)
    school = models.ForeignKey(Schools, on_delete=models.CASCADE,null=True,blank=True)
    program_head = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True,related_name='program_head')
    program_stream = models.ForeignKey(Streams, on_delete=models.CASCADE,null=True,blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    created_at = models.DateTimeField(null=True,blank=True)
    active_step = models.IntegerField(default=1)
    program_status = models.ForeignKey(ProgramStatus, on_delete=models.CASCADE,
                                            related_name='Programs_program_status', null=True)
    pending_at = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='Programs_pending_at')
  
    class Meta:
        db_table = 'programs'



class ProgramOutcomesMapping(models.Model):
    outcome_type = models.CharField(max_length=10, null=True,
                                    choices=[('PO', 'PO'), ('PSO', 'PSO'), ('PEO', 'PEO')])
    code = models.CharField(max_length=20, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    program = models.ForeignKey(Programs, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'program_outcomes_mapping'

class ProgramTrackCourseStructureMapping(models.Model):
    program = models.ForeignKey(Programs, on_delete=models.CASCADE)
    course_category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE)
    track = models.ForeignKey(TracksHeader, on_delete=models.CASCADE, null=True, blank=True)
    is_exit_structure = models.BooleanField(default=False)
    no_of_credits = models.IntegerField(null=True)
    percentage_of_credits = models.FloatField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'program_track_course_structure_mapping'


class ProgramTrackingStatus(models.Model):
    program = models.ForeignKey(Programs, on_delete=models.CASCADE, related_name='ProgramTrackingStatus_program')
    program_status = models.ForeignKey(ProgramStatus, on_delete=models.CASCADE,
                                        related_name='ProgramTrackingStatus_program_status', null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ProgramTrackingStatus_user')
    description = models.TextField(null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True)
    campus = models.CharField(max_length=100, null=True)
    institution = models.CharField(max_length=100, null=True)
    department = models.CharField(max_length=100, null=True)
    created = models.DateTimeField(default=datetime.now, null=True)
    designation = models.CharField(max_length=100, null=True)
    ip_address = models.GenericIPAddressField(null=True)
    emp_id = models.CharField(max_length=15, null=True)

    class Meta:
        db_table = "program_tracking_status"


class ProgramTrackingUserMapping(models.Model):
    programs = models.ForeignKey(Programs, on_delete=models.CASCADE)
    program_tracking_status = models.ForeignKey(ProgramTrackingStatus, on_delete=models.CASCADE,
                                                related_name='ProgramTrackingUserMapping_project_tracking_status',
                                                null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ProgramTrackingUserMapping_user')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ProgramTrackingUserMapping_to_user')
    to_user_group = models.ForeignKey(Group, on_delete=models.CASCADE,
                                      related_name='ProgramTrackingUserMapping_to_user_group')
    created = models.DateTimeField(auto_now_add=True)
    is_edit = models.IntegerField(default=0)
    class Meta:
        db_table = "program_tracking_user_mapping"


class ProgramBoscHistory(models.Model):
    program = models.ForeignKey(Programs, on_delete=models.CASCADE, related_name='bosc_history')
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    previous_data = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'program_bosc_history'