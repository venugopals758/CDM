from django.db.models import Q, Case, When, Value, IntegerField
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from usermanagement.decorators import group_required
from usermanagement.encryption_util import encrypt, decrypt
from usermanagement.models import ErrorLogs
from program.functions import get_ip
from program.models import *
from datetime import datetime


@login_required
@group_required('HOD')
def programs(request):
    involved_program_ids = ProgramTrackingUserMapping.objects.filter(
        Q(to_user_id=request.user.id) | Q(user_id=request.user.id)
    ).values_list('programs_id', flat=True)

    base_qs = Programs.objects.select_related(
        'program_type', 'program_level', 'program_batch', 'program_status', 'pending_at',
    ).filter(
        Q(id__in=involved_program_ids) | Q(created_by_id=request.user.id)
    ).distinct()

    program_list = base_qs.annotate(
        is_pending_here=Case(
            When(pending_at_id=request.user.id, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('is_pending_here', '-created_at')

    for p in program_list:
        p.enc_id = encrypt(p.id)
        p.is_pending_here = p.pending_at_id == request.user.id
        p.pending_is_doaa = bool(p.pending_at_id) and UserGroups.objects.filter(
            user_id=p.pending_at_id, group_id=7, is_active=1, is_block=0
        ).exists()

    context = {
        'programs': program_list,
        'total_count': base_qs.count(),
        'pending_count': base_qs.filter(pending_at_id=request.user.id, program_status_id=3).count(),
    }
    return render(request, 'program/hod/programs.html', context)


@login_required
@group_required('HOD')
def get_bosco_for_department(request):
    department_id = request.GET.get('department_id')
    mapping = BosCochairHODDeptMapping.objects.filter(
        dept_id=department_id, is_active=1
    ).select_related('bos_cochair').first()

    if not mapping or not mapping.bos_cochair_id:
        return JsonResponse({'found': False})

    cochair = mapping.bos_cochair
    name = '%s | %s %s | %s | %s | %s | %s' % (
        cochair.emp_id, cochair.first_name, cochair.last_name or '',
        cochair.campus or '—', cochair.school_code or '—', cochair.dept_code or '—', cochair.designation or '—',
    )
    return JsonResponse({
        'found': True,
        'name': name,
    })


@login_required
@csrf_exempt
@group_required('HOD')
def save_course_request(request):
    if request.method == 'POST':
        try:
            program_id = decrypt(request.POST.get('program_id'))
            request_type = request.POST.get('request_type')
            dept_scope = request.POST.get('dept_scope')
            department_id = request.POST.get('department_id')
            course_title = (request.POST.get('course_title') or '').strip()
            justification = (request.POST.get('justification') or '').strip()
            description = (request.POST.get('description') or '').strip()

            if (
                request_type not in ('new', 'modify') or dept_scope not in ('same', 'other')
                or not justification or not description
            ):
                return JsonResponse({'status': 400, 'message': 'Please fill all the required fields.'})

            if request_type == 'new' and not course_title:
                return JsonResponse({'status': 400, 'message': 'Please provide a tentative course title.'})

            if dept_scope == 'other' and not department_id:
                return JsonResponse({'status': 400, 'message': 'Please select a department.'})

            program = Programs.objects.filter(id=program_id).first()
            if not program:
                return JsonResponse({'status': 404, 'message': 'Program not found.'})
            
            own_mapping = BosCochairHODDeptMapping.objects.filter(
                hod_id=request.user.id, is_active=1
            ).first()

            if not own_mapping or not own_mapping.bos_cochair_id:
                return JsonResponse({
                    'status': 400,
                    'message': 'No BOS Cochair is currently mapped to your department. Please contact the admin.',
                })

            department = own_mapping.dept_id if dept_scope == 'same' else department_id

            course_request = CourseRequest.objects.create(
                program=program,
                request_type=request_type,
                dept_scope=dept_scope,
                department_id=department,
                course_title=course_title if request_type == 'new' else None,
                justification=justification,
                description=description,
                raised_by_id=request.user.id,
                pending_at_id=own_mapping.bos_cochair_id,
            )

            submitted_status, _ = CourseRequestStatus.objects.get_or_create(name='Submitted', defaults={'status': 1})
            course_request.request_status = submitted_status
            course_request.save(update_fields=['request_status'])

            tracking_status = CourseRequestTrackingStatus.objects.create(
                course_request=course_request,
                request_status=submitted_status,
                user_id=request.user.id,
                description=description,
                group_id=5,  # HOD
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                emp_id=request.user.emp_id,
            )
            CourseRequestTrackingUserMapping.objects.create(
                course_request=course_request,
                course_request_tracking_status=tracking_status,
                to_user_id=own_mapping.bos_cochair_id,
                to_user_group_id=2,  # BOSCO
                user_id=request.user.id,
                is_edit=1,
            )

            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('HOD')
def delete_course_request(request):
    if request.method == 'POST':
        try:
            course_request_id = decrypt(request.POST.get('course_request_id'))
            cr = CourseRequest.objects.filter(
                id=course_request_id, raised_by_id=request.user.id, program__program_status_id=3
            ).exclude(request_status_id__in=(3, 7)).first()
            if not cr:
                return JsonResponse({'status': 404, 'message': 'Request not found or cannot be deleted.'})

            # Soft-cancel rather than hard delete - the request may already be pending with
            # a BOSCO (pending_at is set at raise time), so marking it Request cancelled
            # keeps the audit trail and takes it out of their actionable queue instead of
            # just vanishing from under them.
            cr.request_status_id = 7  # Request cancelled
            cr.pending_at_id = None
            cr.save(update_fields=['request_status', 'pending_at'])

            CourseRequestTrackingStatus.objects.create(
                course_request=cr,
                request_status_id=7,
                user_id=request.user.id,
                description='Cancelled by the HOD.',
                group_id=5,  # HOD
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                emp_id=request.user.emp_id,
            )

            CourseRequestTrackingUserMapping.objects.filter(
                course_request=cr, is_edit=1
            ).update(is_edit=0)

            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('HOD')
def hod_forward_program(request, id):
    if request.method == "POST":
        status = request.POST.get('status')
        description = request.POST.get('comments')
        program_id = decrypt(id)
        try:
            program = Programs.objects.get(id=program_id)
        except Programs.DoesNotExist:
            messages.error(request, 'Program not found.')
            return redirect('/programs')

        try:
            hod_group_id = Group.objects.filter(name='HOD').values_list('id', flat=True).first()
            if not ProgramTrackingUserMapping.objects.filter(
                to_user_id=request.user.id, programs_id=program_id,
                to_user_group_id=hod_group_id, is_edit=1
            ).exists():
                messages.error(request, 'You do not have permission to forward this program.')
                return redirect('/programs')

            
            tracking_status = ProgramTrackingStatus.objects.create(
                description=description,
                program_id=program_id,
                program_status_id=int(status),
                user_id=request.user.id,
                group_id=hod_group_id,
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                emp_id=request.user.emp_id,
                created=datetime.now(),
            )
            if int(status) == 7:
                bos_chair_mapping = BosChairSchoolMapping.objects.filter(
                    school_id=program.school_id, is_active=1
                ).first()
                if not bos_chair_mapping:
                    messages.error(request, 'No active BOS Chair is mapped to this school. Please contact the admin.')
                    return redirect('/programs')

                to_user_id = bos_chair_mapping.bos_chair_id
                to_user_group_id = 1  # BOSC

                ProgramTrackingUserMapping.objects.create(
                    programs_id=program_id,
                    program_tracking_status=tracking_status,
                    to_user_id=to_user_id,
                    to_user_group_id=to_user_group_id,
                    user_id=request.user.id,
                    is_edit=1,
                )


            Programs.objects.filter(id=program.id).update(
                program_status_id=int(status), pending_at_id=to_user_id
            )
            ProgramTrackingUserMapping.objects.filter(
                            to_user_id=request.user.id, programs_id=program_id,
                            to_user_group_id=hod_group_id, is_edit=1,
                        ).update(is_edit=0)

            messages.success(request, 'Submitted Successfully')
            return redirect('/programs')
        except Exception as e:
            ErrorLogs.objects.create(log=str(e), user_id=request.user.id, info=request.POST)
            return redirect('/user/not_found')
    else:
        return redirect('/')


@login_required
@csrf_exempt
@group_required('HOD')
def map_courses(request):
    if request.method == 'POST':
        try:
            program_id = decrypt(request.POST.get('program_id'))
            enc_course_ids = request.POST.getlist('course_ids[]') or request.POST.getlist('course_ids')
            if not enc_course_ids:
                return JsonResponse({'status': 400, 'message': 'Please select at least one course to map.'})

            program = Programs.objects.filter(id=program_id).first()
            if not program:
                return JsonResponse({'status': 404, 'message': 'Program not found.'})

            mapped_enc_ids = []
            for enc_course_id in enc_course_ids:
                course_id = decrypt(enc_course_id)
                if not Course.objects.filter(id=course_id, program_id=program.id).exists():
                    continue
                ProgramCourseMapping.objects.get_or_create(
                    program=program, course_id=course_id,
                    defaults={'mapped_by_id': request.user.id},
                )
                mapped_enc_ids.append(enc_course_id)

            return JsonResponse({'status': 200, 'mapped_course_ids': mapped_enc_ids})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@group_required('HOD')
def course_request_details(request, id):
    dec_id = decrypt(id)
    cr = CourseRequest.objects.filter(id=dec_id, raised_by_id=request.user.id).select_related(
        'program', 'department', 'request_status', 'raised_by', 'pending_at'
    ).first()
    if not cr:
        return redirect('/programs')

    cr.enc_id = id
    tracking_status = cr.tracking_status.select_related('request_status', 'user', 'group').order_by('-id')

    context = {
        'cr': cr,
        'tracking_status': tracking_status,
        'is_pending_here': cr.pending_at_id == request.user.id,
        'respond_status_options': CourseRequestStatus.objects.filter(id__in=[6, 7]),
    }
    return render(request, 'program/hod/course_request_details.html', context)


@login_required
@csrf_exempt
@group_required('HOD')
def respond_course_request(request):
    if request.method == 'POST':
        try:
            course_request_id = decrypt(request.POST.get('course_request_id'))
            status_id = request.POST.get('status')
            description = (request.POST.get('comments') or '').strip()

            if status_id not in ('6', '7'):
                return JsonResponse({'status': 400, 'message': 'Please select a valid status.'})
            status_id = int(status_id)

            cr = CourseRequest.objects.filter(
                id=course_request_id, raised_by_id=request.user.id, pending_at_id=request.user.id
            ).first()
            if not cr:
                return JsonResponse({'status': 404, 'message': 'Request not found or not pending with you.'})

            # Whoever last sent this back to me (the BOSCO) is who "Info Provided" goes back to.
            last_mapping = CourseRequestTrackingUserMapping.objects.filter(
                course_request=cr, to_user_id=request.user.id, to_user_group_id=5
            ).order_by('-id').first()

            if status_id == 6:
                # Program head/HOD Info Provided - goes back to the BOSCO who asked.
                if not last_mapping:
                    return JsonResponse({'status': 400, 'message': 'Could not determine who to send this back to.'})
                to_user_id = last_mapping.user_id
                to_user_group_id = 2  # BOSCO
            elif status_id == 7:
                # Request cancelled - nothing further to route.
                to_user_id = None
                to_user_group_id = None

            cr.request_status_id = status_id
            cr.pending_at_id = to_user_id
            cr.save(update_fields=['request_status', 'pending_at'])

            tracking_status = CourseRequestTrackingStatus.objects.create(
                course_request=cr,
                request_status_id=status_id,
                user_id=request.user.id,
                description=description,
                group_id=5,  # HOD
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                emp_id=request.user.emp_id,
            )

            if status_id == 6:
                CourseRequestTrackingUserMapping.objects.create(
                    course_request=cr,
                    course_request_tracking_status=tracking_status,
                    to_user_id=to_user_id,
                    to_user_group_id=to_user_group_id,
                    user_id=request.user.id,
                    is_edit=1,
                )

            CourseRequestTrackingUserMapping.objects.filter(
                course_request=cr, to_user_id=request.user.id, to_user_group_id=5, is_edit=1
            ).update(is_edit=0)

            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})
