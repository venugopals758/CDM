from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group
import os
from usermanagement.models_gitam import EmployeeMaster

Group.add_to_class('priority', models.IntegerField(null=True))
Group.add_to_class('description',models.CharField(max_length=500,null=True))

class User(AbstractUser):
    phone = models.BigIntegerField(null=True)
    campus = models.CharField(max_length=100, null=True)
    school_code = models.CharField(max_length=100, null=True)
    dept_code = models.CharField(max_length=100, null=True)
    designation = models.CharField(max_length=100, null=True)
    emp_id = models.CharField(max_length=100, null=True)
    groups = models.ManyToManyField(
        Group,
        verbose_name=('groups'),
        blank=True,
        help_text=(
            'The groups this user belongs to. A user will get all permissions '
            'granted to each of their groups.'
        ),
        related_name="user_set",
        related_query_name="user",
        through="UserGroups"
    )

    class Meta:
        db_table = "users"

    def __str__(self):
        return str(self.id)


class UserGroups(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    role = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    is_default = models.BooleanField(default=False)
    is_block = models.BooleanField(default=False)
    class Meta:
        db_table = "user_groups"

    def __str__(self):
        return self.id

class ErrorLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    log = models.TextField(null=True)
    info = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_error_logs"

class UserAuthLogs(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True)
    ip_address=models.GenericIPAddressField(null=True)
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True)
    session_key = models.TextField(null=True)
    login_data = models.TextField(null=True)
    status_type = models.CharField(null=True,max_length=5)
    email = models.EmailField(null=True)
    device_type=models.CharField(null=True,max_length=100)
    browser=models.CharField(null=True,max_length=100)
    browser_version=models.CharField(null=True,max_length=50)
    os=models.CharField(null=True,max_length=100)
    os_version=models.CharField(null=True,max_length=50)
    class Meta:
        db_table = "user_auth_logs"


class Batches(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'u_batches'


class Schools(models.Model):
    name = models.CharField(max_length=500)
    code = models.CharField(max_length=50, null=True)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'u_schools'


class Streams(models.Model):
    name = models.CharField(max_length=100)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'u_streams'


class Departments(models.Model):
    name = models.CharField(max_length=70)
    code = models.CharField(max_length=5)
    status = models.BooleanField(default=1)
    class Meta:
        db_table = 'u_department' 

class BosCochairHODDeptMapping(models.Model):
    dept = models.ForeignKey(Departments, on_delete=models.CASCADE,null=True)
    school = models.ForeignKey(Schools, on_delete=models.CASCADE,null=True)
    bos_cochair = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    hod = models.ForeignKey(User, on_delete=models.CASCADE, null=True,related_name='BosCochairHODDeptMapping_hod')
    is_active = models.BooleanField()
    
    created = models.DateTimeField(auto_now_add=True,null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='BosCochairHODDeptMapping_created_by',null=True)

    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='BosCochairHODDeptMapping_modified_by',null=True)
    modified = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'bos_cochair_hod_dept_mapping'


class BosChairSchoolMapping(models.Model):
    school = models.ForeignKey(Schools, on_delete=models.CASCADE,null=True)
    bos_chair = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField()
    
    created = models.DateTimeField(auto_now_add=True,null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='BosChairSchoolMapping_created_by',null=True)

    modified_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='BosChairSchoolMapping_modified_by',null=True)
    modified = models.DateTimeField(null=True)
    
    class Meta:
        db_table = 'bos_chair_school_mapping'