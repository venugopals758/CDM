from django.db import models
from django.contrib.auth.models import Group
from usermanagement.models import User, Departments


class CourseRequestStatus(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)

    class Meta:
        db_table = 'program_course_request_status'


class CourseRequest(models.Model):
    REQUEST_TYPE_CHOICES = [('new', 'Float a New Course'), ('modify', 'Modify an Existing Course')]
    DEPT_SCOPE_CHOICES = [('same', 'Within the Department'), ('other', 'Other Department')]

    # String reference avoids importing program.models.Programs directly here, since
    # program/models.py in turn imports this module - a direct import would be circular.
    program = models.ForeignKey('program.Programs', on_delete=models.CASCADE, related_name='course_requests')
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES)
    dept_scope = models.CharField(max_length=10, choices=DEPT_SCOPE_CHOICES)
    department = models.ForeignKey(Departments, on_delete=models.CASCADE, null=True, blank=True)
    course_title = models.CharField(max_length=255, null=True, blank=True)
    justification = models.TextField(default='')
    description = models.TextField()
    request_status = models.ForeignKey(CourseRequestStatus, on_delete=models.CASCADE, null=True, blank=True)
    raised_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_requests_raised')
    pending_at = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='CourseRequest_pending_at'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'program_course_request'


class CourseRequestTrackingStatus(models.Model):
    course_request = models.ForeignKey(CourseRequest, on_delete=models.CASCADE, related_name='tracking_status')
    request_status = models.ForeignKey(CourseRequestStatus, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    campus = models.CharField(max_length=100, null=True, blank=True)
    institution = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    emp_id = models.CharField(max_length=15, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'program_course_request_tracking_status'


class CourseRequestTrackingUserMapping(models.Model):
    course_request = models.ForeignKey(CourseRequest, on_delete=models.CASCADE, related_name='tracking_user_mapping')
    course_request_tracking_status = models.ForeignKey(
        CourseRequestTrackingStatus, on_delete=models.CASCADE, null=True, blank=True
    )
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_request_to_user')
    to_user_group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_request_from_user')
    is_edit = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'program_course_request_tracking_user_mapping'


