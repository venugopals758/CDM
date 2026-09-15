from django.db import models


class EmployeeMaster(models.Model):
    empid = models.CharField(db_column='EMPID', primary_key=True, max_length=25)
    emp_name = models.CharField(db_column='EMP_NAME', max_length=500, blank=True, null=True)
    emailid = models.CharField(db_column='EMAILID', max_length=500, blank=True, null=True)
    mobile = models.CharField(db_column='MOBILE', max_length=120, blank=True, null=True)
    dob = models.DateTimeField(db_column='DOB', blank=True, null=True)
    doj = models.DateTimeField(db_column='DOJ', blank=True, null=True)
    dor = models.DateTimeField(db_column='DOR', blank=True, null=True)
    job_description = models.CharField(db_column='JOB_DESCRIPTION', max_length=500, blank=True, null=True)
    job_type = models.CharField(db_column='JOB_TYPE', max_length=25, blank=True, null=True)
    emp_type = models.CharField(db_column='EMP_TYPE', max_length=25, blank=True, null=True)
    campus = models.CharField(db_column='CAMPUS', max_length=25, blank=True, null=True)
    college_code = models.CharField(db_column='COLLEGE_CODE', max_length=25, blank=True, null=True)
    dept_code = models.CharField(db_column='DEPT_CODE', max_length=50, blank=True, null=True)
    gender = models.CharField(db_column='GENDER', max_length=10, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'EMPLOYEE_MASTER'


class NirfData(models.Model):
    year = models.IntegerField(db_column='year')
    school = models.CharField(db_column='school', max_length=50, blank=True, null=True)
    campus = models.CharField(db_column='campus', max_length=50, blank=True, null=True)
    department = models.CharField(db_column='department', max_length=100, blank=True, null=True)
    empid_list = models.TextField(db_column='empid_list', blank=True, null=True)
    faculty_count_regular = models.IntegerField(db_column='faculty_count_regular', default=0)
    male_faculty = models.IntegerField(db_column='male_faculty', default=0)
    female_faculty = models.IntegerField(db_column='female_faculty', default=0)
    faculty_with_phd = models.IntegerField(db_column='faculty_with_phd', default=0)
    faculty_without_phd = models.IntegerField(db_column='faculty_without_phd', default=0)
    exp_lt_8 = models.IntegerField(db_column='exp_lt_8', default=0)
    exp_8_15 = models.IntegerField(db_column='exp_8_15', default=0)
    exp_gt_15 = models.IntegerField(db_column='exp_gt_15', default=0)
    patent_published = models.IntegerField(db_column='patent_published', null=True, blank=True)
    patent_granted = models.IntegerField(db_column='patent_granted', null=True, blank=True)
    publication_count = models.IntegerField(db_column='publication_count', null=True, blank=True)
    ret_count = models.IntegerField(db_column='ret_count', null=True, blank=True)
    research_funding = models.IntegerField(db_column='research_funding', null=True, blank=True)
    consulting_grants = models.IntegerField(db_column='consulting_grants', null=True, blank=True)
    fdp = models.IntegerField(db_column='fdp', null=True, blank=True)
    mdp = models.IntegerField(db_column='mdp', null=True, blank=True)
    created = models.DateTimeField(db_column='created', auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'tbl_faculty_nirf_raw_data'
