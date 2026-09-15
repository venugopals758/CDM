from django.db.models import Q
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from usermanagement.decorators import group_required
from usermanagement.models import ErrorLogs, BosChairSchoolMapping
from usermanagement.encryption_util import encrypt, decrypt
from program.models import *
from program.functions import get_ip
from program.forms import get_course_structure_context, get_program_outcomes_context, get_editable_program
from program.bosc import programs as bosc_programs
from program.hod import programs as hod_programs
from program.doaa import programs as doaa_programs
from datetime import datetime


@login_required
@group_required('BOSCO', 'BOSC', 'HOD', 'DOAA')
def programs(request):
    if UserGroups.objects.filter(user_id=request.user.id, group__name='BOSC', is_active=1).exists():
        return bosc_programs(request)
    if UserGroups.objects.filter(user_id=request.user.id, group__name='HOD', is_active=1).exists():
        return hod_programs(request)
    if UserGroups.objects.filter(user_id=request.user.id, group__name='DOAA', is_active=1).exists():
        return doaa_programs(request)

    involved_program_ids = ProgramTrackingUserMapping.objects.filter(
        Q(to_user_id=request.user.id) | Q(user_id=request.user.id)
    ).values_list('programs_id', flat=True)

    base_qs = Programs.objects.select_related(
        'program_type', 'program_level', 'program_batch', 'program_status', 'pending_at',
    ).filter(
        Q(id__in=involved_program_ids) | Q(created_by_id=request.user.id)
    ).distinct()

    program_list = base_qs.order_by('-created_at')
    for p in program_list:
        p.enc_id = encrypt(p.id)
        p.is_pending_here = p.pending_at_id == request.user.id
        p.pending_is_doaa = bool(p.pending_at_id) and UserGroups.objects.filter(
            user_id=p.pending_at_id, group_id=7, is_active=1, is_block=0
        ).exists()

    context = {
        'programs': program_list,
        'total_count': base_qs.count(),
        'pending_count': base_qs.filter(pending_at_id=request.user.id, program_status_id=4).count(),
    }
    return render(request, 'program/bosco/programs.html', context)


@login_required
@group_required('BOSCO', 'BOSC')
def final_preview(request, id):
    dec_id = decrypt(id)
    program = get_editable_program(dec_id, request.user.id)
    if not program:
        return redirect('/programs')

    course_structure_context = get_course_structure_context(program)
    program_outcomes_context = get_program_outcomes_context(program)

    context = {
        'program': program,
        'enc_program_id': id,
        **course_structure_context,
        **program_outcomes_context,
    }
    return render(request, 'program/bosco/final_preview.html', context)


@login_required
@group_required('BOSCO')
def initiate_program(request, id):
    dec_id = decrypt(id)
    if not Programs.objects.filter(id=dec_id, created_by_id=request.user.id).exists():
        return redirect('/programs')

    if request.method == 'POST':
        try:
            program = Programs.objects.filter(id=dec_id, created_by_id=request.user.id).first()

            bos_chair_mapping = BosChairSchoolMapping.objects.filter(
                school_id=program.school_id, is_active=1
            ).first()
            if not bos_chair_mapping:
                messages.error(request, 'No active BOS Chair is mapped to this school. Please contact the admin.')
                return redirect('/programs')

            to_user_id = bos_chair_mapping.bos_chair_id
            to_user_group_id = Group.objects.filter(name='BOSC').values_list('id', flat=True).first()
            current_user_group_id = UserGroups.objects.filter(
                user_id=request.user.id, is_active=1
            ).values_list('group_id', flat=True).first()

            auto_inc = ProgramRef.objects.create(status=1)
            ref = str(datetime.today().year) + '/' + str(auto_inc.id).zfill(4)

            Programs.objects.filter(id=dec_id, created_by_id=request.user.id).update(
                ref_no=ref, program_status_id=2, pending_at_id=to_user_id
            )
            ProgramTrackingStatus.objects.filter(program_id=dec_id, program_status_id=1).update(
                program_status_id=2,
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                group_id=current_user_group_id,
                emp_id=request.user.emp_id,
                created=datetime.now()
            )

            tracking = ProgramTrackingStatus.objects.filter(program_id=dec_id, program_status_id=2).first()
            if tracking and to_user_id:
                ProgramTrackingUserMapping.objects.create(
                    programs_id=dec_id,
                    program_tracking_status_id=tracking.id,
                    to_user_id=to_user_id,
                    user_id=request.user.id,
                    is_edit=1,
                    to_user_group_id=to_user_group_id,
                )

            messages.success(request, 'Successfully Submitted')
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e) + ' Program', info=str(request.POST))

        return redirect('/programs')
    else:
        return redirect('/programs')


@login_required
@csrf_exempt
@group_required('BOSCO')
def bosco_forward_program(request, id):
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
            if not ProgramTrackingUserMapping.objects.filter(
                to_user_id=request.user.id, programs_id=program_id,
                to_user_group_id=2, is_edit=1
            ).exists():
                messages.error(request, 'You do not have permission to forward this program.')
                return redirect('/programs')

            if status == '2':
                bos_chair_mapping = BosChairSchoolMapping.objects.filter(
                    school_id=program.school_id, is_active=1
                ).first()
                if not bos_chair_mapping:
                    messages.error(request, 'No active BOS Chair is mapped to this school. Please contact the admin.')
                    return redirect('/programs')

                to_user_id = bos_chair_mapping.bos_chair_id
                to_user_group_id = Group.objects.filter(name='BOSC').values_list('id', flat=True).first()

                tracking_status = ProgramTrackingStatus.objects.create(
                    description=description,
                    program_id=program_id,
                    program_status_id=2,
                    user_id=request.user.id,
                    group_id=2,
                    campus=request.user.campus,
                    institution=request.user.school_code,
                    department=request.user.dept_code,
                    designation=request.user.designation,
                    ip_address=get_ip(request),
                    emp_id=request.user.emp_id,
                    created=datetime.now(),
                )

                ProgramTrackingUserMapping.objects.create(
                    programs_id=program_id,
                    program_tracking_status=tracking_status,
                    to_user_id=to_user_id,
                    to_user_group_id=to_user_group_id,
                    user_id=request.user.id,
                    is_edit=1,
                )

                Programs.objects.filter(id=program.id).update(
                    program_status_id=2, pending_at_id=to_user_id
                )

            ProgramTrackingUserMapping.objects.filter(
                to_user_id=request.user.id,
                programs_id=program_id,
                to_user_group_id=2,
                is_edit=1,
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
@group_required('BOSCO')
def delete_program(request):
    if request.method == 'POST':
        try:
            program_id = decrypt(request.POST.get('program_id'))
            deleted, _ = Programs.objects.filter(
                id=program_id, created_by_id=request.user.id, program_status_id=1
            ).delete()
            if not deleted:
                return JsonResponse({'status': 404, 'message': 'Program not found or cannot be deleted.'})
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@group_required('BOSCO')
def course_requests(request):
    involved_ids = CourseRequestTrackingUserMapping.objects.filter(
        Q(to_user_id=request.user.id) | Q(user_id=request.user.id)
    ).values_list('course_request_id', flat=True)

    qs = CourseRequest.objects.filter(id__in=involved_ids).select_related(
        'program', 'department', 'request_status', 'raised_by'
    ).distinct().order_by('-created')

    actionable_ids = set(CourseRequest.objects.filter(
        pending_at_id=request.user.id,
        #request_status_id__in=[1, 4, 6]
    ).values_list('id', flat=True))

    for cr in qs:
        cr.enc_id = encrypt(cr.id)
        cr.is_pending_here = cr.id in actionable_ids

    context = {'course_requests': qs}
    return render(request, 'program/bosco/course_requests.html', context)


@login_required
@group_required('BOSCO')
def course_request_details(request, id):
    dec_id = decrypt(id)
    cr = CourseRequest.objects.filter(id=dec_id).select_related(
        'program', 'department', 'request_status', 'raised_by', 'pending_at'
    ).first()
    if not cr:
        return redirect('/programs/course_requests')

    involved = CourseRequestTrackingUserMapping.objects.filter(course_request_id=dec_id).filter(
        Q(to_user_id=request.user.id) | Q(user_id=request.user.id)
    ).exists()
    if not involved:
        return redirect('/programs/course_requests')

    tracking_status = cr.tracking_status.select_related('request_status', 'user', 'group').order_by('-id')

    is_pending_here = cr.pending_at_id == request.user.id 
    #and cr.request_status_id in (1, 4, 6)
    is_correct_dept_cochair = False
    target_cochair_name = None
    if is_pending_here:
        mapping = BosCochairHODDeptMapping.objects.filter(
            dept_id=cr.department_id, is_active=1
        ).select_related('bos_cochair').first()
        is_correct_dept_cochair = bool(mapping and mapping.bos_cochair_id == request.user.id)
        if not is_correct_dept_cochair and mapping and mapping.bos_cochair_id:
            cochair = mapping.bos_cochair
            target_cochair_name = '%s | %s %s | %s | %s | %s | %s' % (
                cochair.emp_id, cochair.first_name, cochair.last_name or '',
                cochair.campus or '—', cochair.school_code or '—', cochair.dept_code or '—', cochair.designation or '—',
            )

    # An "other dept" request has already made its cross-department hop via the Assign
    # action - the receiving BOSCO just initiates it, no further "need more info" round
    # trip. Only a "same dept" request (straight from the HOD to their own BOSCO) offers it.
    if cr.dept_scope == 'same':
        initiate_status_options = CourseRequestStatus.objects.filter(id__in=[3, 5])
    else:
        initiate_status_options = CourseRequestStatus.objects.filter(id__in=[3])

    context = {
        'cr': cr,
        'enc_id': id,
        'tracking_status': tracking_status,
        'is_pending_here': is_pending_here,
        'is_correct_dept_cochair': is_correct_dept_cochair,
        'target_cochair_name': target_cochair_name,
        'initiate_status_options': initiate_status_options,
        'assign_status_options': CourseRequestStatus.objects.filter(id__in=[4, 5]),
    }
    return render(request, 'program/bosco/course_request_details.html', context)


@login_required
@csrf_exempt
@group_required('BOSCO')
def initiate_course_request(request):
    if request.method == 'POST':
        try:
            course_request_id = decrypt(request.POST.get('course_request_id'))
            status_id = request.POST.get('status')
            description = (request.POST.get('comments') or '').strip()

            if status_id not in ('3', '5'):
                return JsonResponse({'status': 400, 'message': 'Please select a valid status.'})
            status_id = int(status_id)

            cr = CourseRequest.objects.filter(
                id=course_request_id, pending_at_id=request.user.id, request_status_id__in=[1, 4, 6]
            ).select_related('program', 'department', 'request_status', 'raised_by').first()
            if not cr:
                return JsonResponse({'status': 404, 'message': 'Request not found or not assigned to you.'})

            if status_id == 5 and cr.dept_scope != 'same':
                return JsonResponse({'status': 400, 'message': 'Please select a valid status.'})

            if not BosCochairHODDeptMapping.objects.filter(
                dept_id=cr.department_id, bos_cochair_id=request.user.id, is_active=1
            ).exists():
                return JsonResponse({'status': 400, 'message': 'This request belongs to a different department.'})

            tracking_status = CourseRequestTrackingStatus.objects.create(
                course_request=cr,
                request_status_id=status_id,
                user_id=request.user.id,
                description=description,
                group_id=2,  # BOSCO
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                emp_id=request.user.emp_id,
            )
            if status_id == 3:
                pending_at_id = None

            elif status_id == 5:
                pending_at_id = cr.raised_by_id
                CourseRequestTrackingUserMapping.objects.create(
                    course_request=cr,
                    course_request_tracking_status=tracking_status,
                    to_user_id=cr.raised_by_id,
                    to_user_group_id=5,  # HOD
                    user_id=request.user.id,
                    is_edit=1,
                )

            cr.request_status_id = status_id
            cr.pending_at_id = pending_at_id
            cr.save(update_fields=['request_status', 'pending_at'])
            CourseRequestTrackingUserMapping.objects.filter(
                course_request=cr, to_user_id=request.user.id, to_user_group_id=2, is_edit=1
            ).update(is_edit=0)
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO')
def assign_course_request(request):
    if request.method == 'POST':
        try:
            course_request_id = decrypt(request.POST.get('course_request_id'))
            status_id = request.POST.get('status')
            description = (request.POST.get('comments') or '').strip()

            if status_id not in ('4', '5'):
                return JsonResponse({'status': 400, 'message': 'Please select a valid status.'})
            status_id = int(status_id)

            cr = CourseRequest.objects.filter(
                id=course_request_id, pending_at_id=request.user.id, request_status_id__in=[1, 4, 6]
            ).select_related('program', 'department', 'request_status', 'raised_by').first()
            if not cr:
                return JsonResponse({'status': 404, 'message': 'Request not found or not assigned to you.'})

            CourseRequestTrackingUserMapping.objects.filter(
                course_request=cr, to_user_id=request.user.id, to_user_group_id=2, is_edit=1
            ).update(is_edit=0)

            if status_id == 5:
                # Need more info from Program head/HOD - send it back to whoever raised it.
                to_user_id = cr.raised_by_id
                to_user_group_id = 5  # HOD
            else:
                # Assigned to Otherdept BOS Cochair to Initiate/Modify Course.
                mapping = BosCochairHODDeptMapping.objects.filter(
                    dept_id=cr.department_id, is_active=1
                ).first()
                if not mapping or not mapping.bos_cochair_id:
                    return JsonResponse({'status': 400, 'message': 'No BOS Cochair is mapped to that department.'})
                to_user_id = mapping.bos_cochair_id
                to_user_group_id = 2  # BOSCO

            cr.request_status_id = status_id
            cr.pending_at_id = to_user_id
            cr.save(update_fields=['request_status', 'pending_at'])

            tracking_status = CourseRequestTrackingStatus.objects.create(
                course_request=cr,
                request_status_id=status_id,
                user_id=request.user.id,
                description=description,
                group_id=2,  # BOSCO
                campus=request.user.campus,
                institution=request.user.school_code,
                department=request.user.dept_code,
                designation=request.user.designation,
                ip_address=get_ip(request),
                emp_id=request.user.emp_id,
            )
            CourseRequestTrackingUserMapping.objects.create(
                course_request=cr,
                course_request_tracking_status=tracking_status,
                to_user_id=to_user_id,
                to_user_group_id=to_user_group_id,
                user_id=request.user.id,
                is_edit=1,
            )

            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})
