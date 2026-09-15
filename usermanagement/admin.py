from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db.models import Q
from datetime import datetime
from usermanagement.decorators import group_required
from usermanagement.models import (
    Schools, Streams, Departments, ErrorLogs, User, UserGroups, EmployeeMaster,
    BosCochairHODDeptMapping, BosChairSchoolMapping,
)
from usermanagement.encryption_util import encrypt, decrypt
from program.models import ProgramLevel, ProgramSchoolDurationExitplanMapping, TracksHeader, TrackHeaderLevelSchoolMapping

DEFAULT_NEW_USER_PASSWORD = 'CDM@gitam$'


# ---------------- Schools ----------------

@login_required
@group_required('ADMIN')
def schools(request):
    school_list = Schools.objects.all().order_by('-id')
    for s in school_list:
        s.enc_id = encrypt(s.id)
    return render(request, 'admin/schools.html', {'schools': school_list})


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_school(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip()
            if not name:
                return JsonResponse({'status': 400, 'message': 'Name is required.'})

            if enc_id:
                school_id = decrypt(enc_id)
                Schools.objects.filter(id=school_id).update(name=name, code=code)
            else:
                Schools.objects.create(name=name, code=code)
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_school_status(request):
    if request.method == 'POST':
        try:
            school_id = decrypt(request.POST.get('id'))
            school = Schools.objects.filter(id=school_id).first()
            if not school:
                return JsonResponse({'status': 404, 'message': 'School not found.'})
            school.status = not school.status
            school.save(update_fields=['status'])
            return JsonResponse({'status': 200, 'is_active': school.status})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- Streams ----------------

@login_required
@group_required('ADMIN')
def streams(request):
    stream_list = Streams.objects.all().order_by('-id')
    for s in stream_list:
        s.enc_id = encrypt(s.id)
    return render(request, 'admin/streams.html', {'streams': stream_list})


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_stream(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'status': 400, 'message': 'Name is required.'})

            if enc_id:
                stream_id = decrypt(enc_id)
                Streams.objects.filter(id=stream_id).update(name=name)
            else:
                Streams.objects.create(name=name)
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_stream_status(request):
    if request.method == 'POST':
        try:
            stream_id = decrypt(request.POST.get('id'))
            stream = Streams.objects.filter(id=stream_id).first()
            if not stream:
                return JsonResponse({'status': 404, 'message': 'Stream not found.'})
            stream.status = not stream.status
            stream.save(update_fields=['status'])
            return JsonResponse({'status': 200, 'is_active': stream.status})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- Departments ----------------

@login_required
@group_required('ADMIN')
def departments(request):
    department_list = Departments.objects.all().order_by('-id')
    for d in department_list:
        d.enc_id = encrypt(d.id)
    return render(request, 'admin/departments.html', {'departments': department_list})


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_department(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            name = request.POST.get('name', '').strip()
            code = request.POST.get('code', '').strip()
            if not name:
                return JsonResponse({'status': 400, 'message': 'Name is required.'})

            if enc_id:
                department_id = decrypt(enc_id)
                Departments.objects.filter(id=department_id).update(name=name, code=code)
            else:
                Departments.objects.create(name=name, code=code)
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_department_status(request):
    if request.method == 'POST':
        try:
            department_id = decrypt(request.POST.get('id'))
            department = Departments.objects.filter(id=department_id).first()
            if not department:
                return JsonResponse({'status': 404, 'message': 'Department not found.'})
            department.status = not department.status
            department.save(update_fields=['status'])
            return JsonResponse({'status': 200, 'is_active': department.status})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- Users ----------------

@login_required
@group_required('ADMIN')
def users(request):
    user_list = User.objects.filter(is_active=1).order_by('-id')

    roles_by_user = {}
    for ug in UserGroups.objects.values('user_id', 'group__name', 'is_active'):
        roles_by_user.setdefault(ug['user_id'], []).append(ug)

    for u in user_list:
        user_roles = roles_by_user.get(u.id, [])
        u.role_names = ', '.join(r['group__name'] for r in user_roles)
        active_role = next((r['group__name'] for r in user_roles if r['is_active']), None)
        u.active_role = active_role

    return render(request, 'admin/users.html', {'users': user_list})


@login_required
@group_required('ADMIN')
@csrf_exempt
def add_user(request):
    if request.method == 'POST':
        try:
            emp_id = request.POST.get('emp_id', '').strip()
            group_id = request.POST.get('group_id')

            if not emp_id or not group_id:
                messages.error(request, 'Employee and Role are required.')
                return redirect('admin_add_user')

            if User.objects.filter(username=emp_id).exists():
                messages.error(request, 'A user with this Employee ID already exists.')
                return redirect('admin_add_user')

            data = EmployeeMaster.objects.using('GITAM').filter(empid=emp_id).values(
                'empid', 'emp_name', 'emailid', 'mobile', 'job_description', 'campus', 'college_code', 'dept_code'
            ).last()

            if not data:
                messages.error(request, 'Employee not found.')
                return redirect('admin_add_user')

            group = Group.objects.filter(id=group_id).first()
            if not group:
                messages.error(request, 'Invalid role selected.')
                return redirect('admin_add_user')

            name_parts = (data['emp_name'] or '').strip().split(' ', 1)
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[1] if len(name_parts) > 1 else ''

            user = User.objects.create_user(
                username=emp_id,
                password=DEFAULT_NEW_USER_PASSWORD,
                emp_id=emp_id,
                first_name=first_name,
                last_name=last_name,
                email=data['emailid'] or '',
                phone=data['mobile'] if data['mobile'] and str(data['mobile']).isdigit() else None,
                designation=data['job_description'],
                campus=data['campus'],
                school_code=data['college_code'],
                dept_code=data['dept_code'],
            )

            UserGroups.objects.create(
                user=user,
                group=group,
                role=group.name,
                is_active=1,
                is_default=1,
                is_block=0,
            )

            messages.success(request, 'User added successfully.')
            return redirect('admin_users')
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            messages.error(request, str(e))
            return redirect('admin_add_user')

    groups = Group.objects.all().order_by('name')
    return render(request, 'admin/add_user.html', {'groups': groups})


@login_required
@csrf_exempt
@group_required('ADMIN')
def search_employee(request):
    term = request.POST.get('term', '').strip()
    if not term:
        return JsonResponse({'status': 200, 'data': []})

    existing_emp_ids = set(User.objects.values_list('username', flat=True))

    data = EmployeeMaster.objects.using('GITAM').filter(
        Q(empid__icontains=term) | Q(emp_name__icontains=term) | Q(emailid__icontains=term)
    ).values('empid', 'emp_name', 'emailid')[:20]

    results = []
    for item in data:
        results.append({
            'empid': item['empid'],
            'emp_name': item['emp_name'],
            'emailid': item['emailid'],
            'exists': item['empid'] in existing_emp_ids,
        })

    return JsonResponse({'status': 200, 'data': results})


@login_required
@csrf_exempt
@group_required('ADMIN')
def get_employee_data(request):
    emp_id = request.POST.get('emp_id', '').strip()
    if not emp_id:
        return JsonResponse({'status': 400, 'message': 'Employee ID is required.'})

    data = EmployeeMaster.objects.using('GITAM').filter(empid=emp_id).values(
        'empid', 'emp_name', 'emailid', 'mobile', 'job_description', 'campus', 'college_code', 'dept_code'
    ).last()

    if not data:
        return JsonResponse({'status': 404, 'message': 'Employee not found.'})

    return JsonResponse({'status': 200, 'data': data})


# ---------------- BOS Cochair / HOD - Department Mapping ----------------

@login_required
@group_required('ADMIN')
def bos_cochair_mappings(request):
    mapping_list = BosCochairHODDeptMapping.objects.select_related('dept', 'school', 'bos_cochair', 'hod').all().order_by('-id')
    for m in mapping_list:
        m.enc_id = encrypt(m.id)

    mapped_cochair_ids = mapping_list.values_list('bos_cochair_id', flat=True)
    mapped_hod_ids = mapping_list.values_list('hod_id', flat=True)

    context = {
        'mappings': mapping_list,
        'departments': Departments.objects.filter(status=1).order_by('name'),
        'schools': Schools.objects.filter(status=1).order_by('name'),
        'cochair_users': User.objects.filter(is_active=1).filter(
            Q(id__in=UserGroups.objects.filter(group__name='BOSCO', is_active=1).values_list('user_id', flat=True))
            | Q(id__in=mapped_cochair_ids)
        ).order_by('first_name'),
        'hod_users': User.objects.filter(is_active=1).filter(
            Q(id__in=UserGroups.objects.filter(group__name='HOD', is_active=1).values_list('user_id', flat=True))
            | Q(id__in=mapped_hod_ids)
        ).order_by('first_name'),
    }
    return render(request, 'admin/bos_cochair_mappings.html', context)


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_bos_cochair_mapping(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            dept_id = request.POST.get('dept_id')
            school_id = request.POST.get('school_id')
            bos_cochair_id = request.POST.get('bos_cochair_id')
            hod_id = request.POST.get('hod_id')

            if not dept_id or not school_id or not bos_cochair_id or not hod_id:
                return JsonResponse({'status': 400, 'message': 'Department, School, BOS Cochair and HOD are required.'})

            if enc_id:
                mapping_id = decrypt(enc_id)
                BosCochairHODDeptMapping.objects.filter(id=mapping_id).update(
                    dept_id=dept_id,
                    school_id=school_id,
                    bos_cochair_id=bos_cochair_id,
                    hod_id=hod_id,
                    modified=datetime.now(),
                    modified_by_id=request.user.id,
                )
            else:
                BosCochairHODDeptMapping.objects.create(
                    dept_id=dept_id,
                    school_id=school_id,
                    bos_cochair_id=bos_cochair_id,
                    hod_id=hod_id,
                    is_active=1,
                    created_by_id=request.user.id,
                )
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_bos_cochair_mapping_status(request):
    if request.method == 'POST':
        try:
            mapping_id = decrypt(request.POST.get('id'))
            mapping = BosCochairHODDeptMapping.objects.filter(id=mapping_id).first()
            if not mapping:
                return JsonResponse({'status': 404, 'message': 'Mapping not found.'})
            mapping.is_active = not mapping.is_active
            mapping.modified = datetime.now()
            mapping.modified_by_id = request.user.id
            mapping.save(update_fields=['is_active', 'modified', 'modified_by'])
            return JsonResponse({'status': 200, 'is_active': mapping.is_active})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- BOS Chair - School Mapping ----------------

@login_required
@group_required('ADMIN')
def bos_chair_school_mappings(request):
    mapping_list = BosChairSchoolMapping.objects.select_related('school', 'bos_chair').all().order_by('-id')
    for m in mapping_list:
        m.enc_id = encrypt(m.id)

    mapped_bos_chair_ids = mapping_list.values_list('bos_chair_id', flat=True)

    context = {
        'mappings': mapping_list,
        'schools': Schools.objects.filter(status=1).order_by('name'),
        'bos_chair_users': User.objects.filter(is_active=1).filter(
            Q(id__in=UserGroups.objects.filter(group__name='BOSC', is_active=1).values_list('user_id', flat=True))
            | Q(id__in=mapped_bos_chair_ids)
        ).order_by('first_name'),
    }
    return render(request, 'admin/bos_chair_school_mappings.html', context)


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_bos_chair_school_mapping(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            school_id = request.POST.get('school_id')
            bos_chair_id = request.POST.get('bos_chair_id')

            if not school_id or not bos_chair_id:
                return JsonResponse({'status': 400, 'message': 'School and BOS Chair are required.'})

            if enc_id:
                mapping_id = decrypt(enc_id)
                BosChairSchoolMapping.objects.filter(id=mapping_id).update(
                    school_id=school_id,
                    bos_chair_id=bos_chair_id,
                    modified=datetime.now(),
                    modified_by_id=request.user.id,
                )
            else:
                BosChairSchoolMapping.objects.create(
                    school_id=school_id,
                    bos_chair_id=bos_chair_id,
                    is_active=1,
                    created_by_id=request.user.id,
                )
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_bos_chair_school_mapping_status(request):
    if request.method == 'POST':
        try:
            mapping_id = decrypt(request.POST.get('id'))
            mapping = BosChairSchoolMapping.objects.filter(id=mapping_id).first()
            if not mapping:
                return JsonResponse({'status': 404, 'message': 'Mapping not found.'})
            mapping.is_active = not mapping.is_active
            mapping.modified = datetime.now()
            mapping.modified_by_id = request.user.id
            mapping.save(update_fields=['is_active', 'modified', 'modified_by'])
            return JsonResponse({'status': 200, 'is_active': mapping.is_active})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- Program Level / School - Duration & Exit Plan Mapping ----------------

@login_required
@group_required('ADMIN')
def duration_exit_plans(request):
    mapping_list = ProgramSchoolDurationExitplanMapping.objects.select_related(
        'program_level', 'school'
    ).all().order_by('program_level_id', 'school__name')
    for m in mapping_list:
        m.enc_id = encrypt(m.id)

    context = {
        'mappings': mapping_list,
        'program_levels': ProgramLevel.objects.filter(status=1).order_by('name'),
        'schools': Schools.objects.filter(status=1).order_by('name'),
    }
    return render(request, 'admin/duration_exit_plans.html', context)


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_duration_exit_plan(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            program_level_id = request.POST.get('program_level_id')
            school_id = request.POST.get('school_id')
            duration = request.POST.get('duration')
            exit_plan = request.POST.get('exit_plan') == '1'

            if not program_level_id or not school_id or not duration:
                return JsonResponse({'status': 400, 'message': 'Program Level, School and Duration are required.'})

            if enc_id:
                mapping_id = decrypt(enc_id)
                ProgramSchoolDurationExitplanMapping.objects.filter(id=mapping_id).update(
                    program_level_id=program_level_id,
                    school_id=school_id,
                    duration=duration,
                    exit_plan=exit_plan,
                )
            else:
                if ProgramSchoolDurationExitplanMapping.objects.filter(
                    program_level_id=program_level_id, school_id=school_id
                ).exists():
                    return JsonResponse({
                        'status': 400,
                        'message': 'A mapping for this Program Level and School already exists. Edit it instead.',
                    })
                ProgramSchoolDurationExitplanMapping.objects.create(
                    program_level_id=program_level_id,
                    school_id=school_id,
                    duration=duration,
                    exit_plan=exit_plan,
                    status=1,
                )
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_duration_exit_plan_status(request):
    if request.method == 'POST':
        try:
            mapping_id = decrypt(request.POST.get('id'))
            mapping = ProgramSchoolDurationExitplanMapping.objects.filter(id=mapping_id).first()
            if not mapping:
                return JsonResponse({'status': 404, 'message': 'Mapping not found.'})
            mapping.status = not mapping.status
            mapping.save(update_fields=['status'])
            return JsonResponse({'status': 200, 'is_active': mapping.status})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- Tracks ----------------

@login_required
@group_required('ADMIN')
def tracks(request):
    track_list = TracksHeader.objects.all().order_by('name')
    for t in track_list:
        t.enc_id = encrypt(t.id)
    return render(request, 'admin/tracks.html', {'tracks': track_list})


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_track(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            name = request.POST.get('name', '').strip()
            if not name:
                return JsonResponse({'status': 400, 'message': 'Name is required.'})

            if enc_id:
                track_id = decrypt(enc_id)
                TracksHeader.objects.filter(id=track_id).update(name=name)
            else:
                TracksHeader.objects.create(name=name, status=1)
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_track_status(request):
    if request.method == 'POST':
        try:
            track_id = decrypt(request.POST.get('id'))
            track = TracksHeader.objects.filter(id=track_id).first()
            if not track:
                return JsonResponse({'status': 404, 'message': 'Track not found.'})
            track.status = not track.status
            track.save(update_fields=['status'])
            return JsonResponse({'status': 200, 'is_active': track.status})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


# ---------------- Program Level / School - Track Mapping ----------------

@login_required
@group_required('ADMIN')
def track_school_mappings(request):
    mapping_list = TrackHeaderLevelSchoolMapping.objects.select_related(
        'program_level', 'school', 'track'
    ).all().order_by('program_level_id', 'school__name', 'track__name')
    for m in mapping_list:
        m.enc_id = encrypt(m.id)

    context = {
        'mappings': mapping_list,
        'program_levels': ProgramLevel.objects.filter(status=1).order_by('name'),
        'schools': Schools.objects.filter(status=1).order_by('name'),
        'tracks': TracksHeader.objects.filter(status=1).order_by('name'),
    }
    return render(request, 'admin/track_school_mappings.html', context)


@login_required
@csrf_exempt
@group_required('ADMIN')
def save_track_school_mapping(request):
    if request.method == 'POST':
        try:
            enc_id = request.POST.get('id')
            program_level_id = request.POST.get('program_level_id')
            school_id = request.POST.get('school_id')
            track_id = request.POST.get('track_id')

            if not program_level_id or not school_id or not track_id:
                return JsonResponse({'status': 400, 'message': 'Program Level, School and Track are required.'})

            if enc_id:
                mapping_id = decrypt(enc_id)
                TrackHeaderLevelSchoolMapping.objects.filter(id=mapping_id).update(
                    program_level_id=program_level_id,
                    school_id=school_id,
                    track_id=track_id,
                )
            else:
                if TrackHeaderLevelSchoolMapping.objects.filter(
                    program_level_id=program_level_id, school_id=school_id, track_id=track_id
                ).exists():
                    return JsonResponse({
                        'status': 400,
                        'message': 'This Program Level, School and Track combination already exists.',
                    })
                TrackHeaderLevelSchoolMapping.objects.create(
                    program_level_id=program_level_id,
                    school_id=school_id,
                    track_id=track_id,
                    status=1,
                )
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('ADMIN')
def toggle_track_school_mapping_status(request):
    if request.method == 'POST':
        try:
            mapping_id = decrypt(request.POST.get('id'))
            mapping = TrackHeaderLevelSchoolMapping.objects.filter(id=mapping_id).first()
            if not mapping:
                return JsonResponse({'status': 404, 'message': 'Mapping not found.'})
            mapping.status = not mapping.status
            mapping.save(update_fields=['status'])
            return JsonResponse({'status': 200, 'is_active': mapping.status})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})
