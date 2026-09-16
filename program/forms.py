import json
from django.db.models import Sum, Q
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from usermanagement.decorators import group_required
from usermanagement.models import User, ErrorLogs
from usermanagement.encryption_util import encrypt, decrypt
from program.models import *
from datetime import datetime


def get_editable_program(program_id, user_id):
    """A program can be opened by the BOSCO who created it, or by the BOSC it is currently pending_at."""
    return Programs.objects.filter(id=program_id).filter(
        Q(created_by_id=user_id) | Q(pending_at_id=user_id)
    ).first()


def is_bosc_reviewer(user_id, program):
    """True when the user editing this program is the BOS Chair it was forwarded to, not its BOSCO creator."""
    return bool(program and program.pending_at_id == user_id and program.created_by_id != user_id)


def is_post_submission_edit(user_id, program):
    """True whenever a program that has already been submitted at least once (any status past Draft)
    is being edited - either by the BOSC reviewer it's currently pending at, or by the original BOSCO
    creator after it came back to them (e.g. a 'need more info' round-trip)."""
    if not program or program.program_status_id == 1:
        return False
    return is_bosc_reviewer(user_id, program) or program.created_by_id == user_id


def model_fields(model, exclude=('id', 'program_id')):
    """Field names derived from the model itself, so any field added later is picked up
    automatically with no list to remember to update."""
    return [field.attname for field in model._meta.fields if field.attname not in exclude]


def snapshot_program_state(program):
    return {
        'basic_details': {
            field: getattr(program, field) for field in model_fields(Programs)
        },
        'course_structure': list(
            ProgramTrackCourseStructureMapping.objects.filter(program=program).values(
                *model_fields(ProgramTrackCourseStructureMapping)
            )
        ),
        'outcomes': list(
            ProgramOutcomesMapping.objects.filter(program=program).values(
                *model_fields(ProgramOutcomesMapping)
            )
        ),
    }


def record_bosc_history(user_id, program):
    if is_post_submission_edit(user_id, program):
        ProgramBoscHistory.objects.create(
            program=program,
            changed_by_id=user_id,
            previous_data=json.dumps(snapshot_program_state(program), default=str),
        )


OUTCOME_TYPE_LABELS = [
    ('PEO', 'Programme Educational Objectives (PEOs)'),
    ('PO', 'Programme Outcomes (POs)'),
    ('PSO', 'Programme Specific Outcomes (PSOs)'),
]


def get_program_outcomes_context(program):
    rows = ProgramOutcomesMapping.objects.filter(program=program).order_by('id')
    for row in rows:
        row.enc_id = encrypt(row.id)

    outcomes_by_type = {'PO': [], 'PSO': [], 'PEO': []}
    for row in rows:
        outcomes_by_type.setdefault(row.outcome_type, []).append(row)

    outcome_sections = [
        {'type_code': type_code, 'type_label': type_label, 'rows': outcomes_by_type[type_code]}
        for type_code, type_label in OUTCOME_TYPE_LABELS
    ]

    return {'outcome_sections': outcome_sections}


def get_tracks_for_program(program):
    if not (program and program.program_level_id and program.school_id):
        return []
    mappings = TrackHeaderLevelSchoolMapping.objects.filter(
        program_level_id=program.program_level_id,
        school_id=program.school_id,
        status=1,
        track__status=1,
    ).select_related('track')
    return [m.track for m in mappings]


def get_course_structure_context(program):
    tracks = get_tracks_for_program(program)

    rows = ProgramTrackCourseStructureMapping.objects.filter(program=program).select_related(
        'course_category', 'track'
    )
    for row in rows:
        row.enc_id = encrypt(row.id)

    course_structure_by_track = {}
    course_structure_exit = []
    course_structure_default = []
    for row in rows:
        if row.is_exit_structure:
            course_structure_exit.append(row)
        elif row.track_id:
            course_structure_by_track.setdefault(row.track_id, []).append(row)
        else:
            course_structure_default.append(row)

    def totals_for(rows):
        return {
            'credits': sum(r.no_of_credits or 0 for r in rows),
            'percentage': sum(r.percentage_of_credits or 0 for r in rows),
        }

    for track in tracks:
        track.rows = course_structure_by_track.get(track.id, [])
        track.totals = totals_for(track.rows)

    return {
        'tracks': tracks,
        # Used only when no Track mapping is configured for this Program Level + School,
        # so the wizard still has a single table (track=None) to enter structure into.
        'course_structure_default': course_structure_default,
        'course_structure_default_totals': totals_for(course_structure_default),
        'course_structure_exit': course_structure_exit,
        'course_structure_exit_totals': totals_for(course_structure_exit),
    }


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def add_program(request):
    context = {
        'program_levels': ProgramLevel.objects.filter(status=1),
        'program_batches': Batches.objects.filter(status=1),
        'schools': Schools.objects.filter(status=1),
        'program_type': ProgramType.objects.filter(status=1),
        'program_streams': Streams.objects.filter(status=1),
        'course_categories': CourseCategory.objects.filter(status=1),
        **get_program_outcomes_context(None),
    }
    return render(request, 'program/forms/form_base.html', context)


@login_required
@group_required('BOSCO', 'BOSC')
def edit_program(request, id):
    dec_id = decrypt(id)
    program = get_editable_program(dec_id, request.user.id)
    if not program:
        return redirect('/programs')

    completed_steps = list(range(1, program.active_step)) if program.active_step else []

    course_structure_context = get_course_structure_context(program)
    program_outcomes_context = get_program_outcomes_context(program)

    context = {
        'program': program,
        'enc_program_id': id,
        'completed_steps': completed_steps,
        'program_levels': ProgramLevel.objects.filter(status=1),
        'program_batches': Batches.objects.filter(status=1),
        'schools': Schools.objects.filter(status=1),
        'program_type': ProgramType.objects.filter(status=1),
        'program_streams': Streams.objects.filter(status=1),
        'course_categories': CourseCategory.objects.filter(status=1),
        **course_structure_context,
        **program_outcomes_context,
    }
    return render(request, 'program/forms/form_base.html', context)


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def save_basic_details(request):
    if request.method == 'POST':
        program_id = None
        enc_program_id = None
        try:
            post = request.POST
            raw_id = post.get('program_id')
            existing_program = None
            if raw_id:
                program_id = decrypt(raw_id)
                existing_program = get_editable_program(program_id, request.user.id)
                if not existing_program:
                    return JsonResponse({'status': 404, 'message': 'Program not found.'})

            preserve_workflow_state = is_post_submission_edit(request.user.id, existing_program)
            record_bosc_history(request.user.id, existing_program)

            btn_type = int(post.get('btn_type', 1))
            active_step = 2 if btn_type == 2 else 1

            updated_values = {
                'status': 1,
                'active_step': active_step,
                'code': post.get('code') or None,
                'title': post.get('temp_program_title') or None,
                'minimum_credits': post.get('minimum_credits') or None,
                'duration': post.get('duration') or None,
                'has_exit_plan': post.get('has_exit_plan') == '1',
                'exit_end_of_year': post.get('exit_end_of_year') or None,
                'exit_minimum_credits': post.get('exit_minimum_credits') or None,
                'program_level_credits': post.get('program_level_credits') or None,
                'program_type_id': post.get('program_type') or None,
                'program_level_id': post.get('program_level') or None,
                'program_batch_id': post.get('program_batch') or None,
                'school_id': post.get('school') or None,
                'program_head_id': post.get('program_head') or None,
                'program_stream_id': post.get('program_stream') or None,
                'created_at': datetime.now(),
                'program_status_id': 1,
            }

            if preserve_workflow_state:
                # Editing a program that's already been submitted at least once - whether by the
                # BOSC reviewer it's pending at, or by the creator after it came back to them (e.g.
                # a "need more info" round-trip) - must not silently reset its review workflow state.
                updated_values.pop('program_status_id')
                updated_values['active_step'] = existing_program.active_step
            else:
                updated_values['created_by_id'] = request.user.id

            new_level_id = post.get('program_level') or None
            new_school_id = post.get('school') or None
            level_or_school_changed = existing_program and (
                str(existing_program.program_level_id or '') != str(new_level_id or '')
                or str(existing_program.school_id or '') != str(new_school_id or '')
            )
            exit_plan_disabled = existing_program and existing_program.has_exit_plan and updated_values['has_exit_plan'] is False

            obj, _ = Programs.objects.update_or_create(id=program_id, defaults=updated_values)
            program_id = obj.id

            if level_or_school_changed:
                # The whole Program Structure step - both the track breakdown and the Exit
                # Plan structure (its own exit_minimum_credits is also specific to this Level +
                # School combo) - is tied to the previous Program Level + School. Once that
                # changes, none of it still applies, so it would otherwise sit as orphaned DB
                # records (and could confusingly reappear if the level/school is changed back).
                ProgramTrackCourseStructureMapping.objects.filter(program_id=program_id).delete()

            if exit_plan_disabled:
                # Same reasoning for the Exit Plan structure: once "Do you have an Exit Plan"
                # flips to No, its rows no longer apply to anything and would otherwise be left
                # as orphaned records that silently reappear if Exit Plan is turned back on.
                ProgramTrackCourseStructureMapping.objects.filter(
                    program_id=program_id, is_exit_structure=True
                ).delete()

            # Uploaded after the row has a real pk, since program_structure_path() needs instance.id
            uploaded_pdf = request.FILES.get('program_structure_pdf')
            if uploaded_pdf:
                obj.program_structure_pdf = uploaded_pdf
                obj.save(update_fields=['program_structure_pdf'])

            if not preserve_workflow_state and not ProgramTrackingStatus.objects.filter(
                program_id=program_id, program_status_id=1
            ).exists():
                # Only a genuinely new/Draft-stage save gets its own "Draft" timeline entry - editing
                # a program that's already mid-review (forward or backward in the workflow) shouldn't
                # insert a spurious Draft record into its tracking history.
                ProgramTrackingStatus.objects.create(
                    program_id=program_id,
                    program_status_id=1,
                    user_id=request.user.id,
                    created=datetime.now()
                )

            enc_program_id = encrypt(program_id)


            return JsonResponse({'status': 200, 'enc_id': enc_program_id})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def add_program_structure_row(request):
    if request.method == 'POST':
        try:
            post = request.POST
            program_id = decrypt(post.get('program_id'))
            program = get_editable_program(program_id, request.user.id)
            if not program:
                return JsonResponse({'status': 404, 'message': 'Program not found. Please complete Basic Details first.'})

            record_bosc_history(request.user.id, program)

            is_exit = post.get('is_exit') == '1'
            track_id = None if is_exit else (post.get('track') or None)

            row = ProgramTrackCourseStructureMapping.objects.create(
                program=program,
                course_category_id=post.get('course_category'),
                track_id=track_id,
                is_exit_structure=is_exit,
                no_of_credits=post.get('no_of_credits') or None,
                percentage_of_credits=post.get('percentage_of_credits') or None,
            )

            return JsonResponse({'status': 200, 'enc_row_id': encrypt(row.id)})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def update_program_structure_row(request):
    if request.method == 'POST':
        try:
            row_id = decrypt(request.POST.get('row_id'))
            row = ProgramTrackCourseStructureMapping.objects.filter(id=row_id).filter(
                Q(program__created_by_id=request.user.id) | Q(program__pending_at_id=request.user.id)
            ).select_related('program').first()
            if not row:
                return JsonResponse({'status': 404, 'message': 'Row not found.'})

            no_of_credits = request.POST.get('no_of_credits')
            percentage_of_credits = request.POST.get('percentage_of_credits')
            if no_of_credits in (None, '') or percentage_of_credits in (None, ''):
                return JsonResponse({'status': 400, 'message': 'Please fill all the credit fields before saving.'})

            record_bosc_history(request.user.id, row.program)
            row.no_of_credits = no_of_credits
            row.percentage_of_credits = percentage_of_credits
            row.save(update_fields=['no_of_credits', 'percentage_of_credits'])

            return JsonResponse({
                'status': 200,
                'no_of_credits': row.no_of_credits,
                'percentage_of_credits': float(row.percentage_of_credits),
            })
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def delete_program_structure_row(request):
    if request.method == 'POST':
        try:
            row_id = decrypt(request.POST.get('row_id'))
            row = ProgramTrackCourseStructureMapping.objects.filter(id=row_id).filter(
                Q(program__created_by_id=request.user.id) | Q(program__pending_at_id=request.user.id)
            ).select_related('program').first()
            if not row:
                return JsonResponse({'status': 404, 'message': 'Row not found.'})

            record_bosc_history(request.user.id, row.program)
            row.delete()
            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def save_program_structure(request):
    if request.method == 'POST':
        try:
            program_id = decrypt(request.POST.get('program_id'))
            program = get_editable_program(program_id, request.user.id)
            if not program:
                return JsonResponse({'status': 404, 'message': 'Program not found. Please complete Basic Details first.'})

            tracks = get_tracks_for_program(program)
            if tracks:
                for track in tracks:
                    total = ProgramTrackCourseStructureMapping.objects.filter(
                        program=program, is_exit_structure=False, track=track
                    ).aggregate(total=Sum('no_of_credits'))['total'] or 0
                    if program.minimum_credits:
                        if total < program.minimum_credits:
                            return JsonResponse({
                                'status': 400,
                                'message': 'Total credits for "%s" must be at least %s (currently %s).' % (
                                    track.name, program.minimum_credits, total
                                ),
                            })
                    elif total == 0:
                        return JsonResponse({
                            'status': 400,
                            'message': 'Add at least one course category to the "%s" structure before continuing.' % track.name,
                        })
            else:
                # No Track mapping configured for this Program Level + School - the wizard falls
                # back to a single default (track=None) table, validated the same way.
                total = ProgramTrackCourseStructureMapping.objects.filter(
                    program=program, is_exit_structure=False, track__isnull=True
                ).aggregate(total=Sum('no_of_credits'))['total'] or 0
                if program.minimum_credits:
                    if total < program.minimum_credits:
                        return JsonResponse({
                            'status': 400,
                            'message': 'Total credits must be at least %s (currently %s).' % (
                                program.minimum_credits, total
                            ),
                        })
                elif total == 0:
                    return JsonResponse({
                        'status': 400,
                        'message': 'Add at least one course category to the structure before continuing.',
                    })

            if program.has_exit_plan:
                exit_total = ProgramTrackCourseStructureMapping.objects.filter(
                    program=program, is_exit_structure=True
                ).aggregate(total=Sum('no_of_credits'))['total'] or 0
                if program.exit_minimum_credits:
                    if exit_total < program.exit_minimum_credits:
                        return JsonResponse({
                            'status': 400,
                            'message': 'Total credits for the Exit Plan structure must be at least %s (currently %s).' % (
                                program.exit_minimum_credits, exit_total
                            ),
                        })
                elif exit_total == 0:
                    return JsonResponse({
                        'status': 400,
                        'message': 'Add at least one course category to the Exit Plan structure before continuing.',
                    })

            program.active_step = 3
            program.save(update_fields=['active_step'])

            return JsonResponse({'status': 200})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def add_program_outcome_row(request):
    if request.method == 'POST':
        try:
            post = request.POST
            program_id = decrypt(post.get('program_id'))
            program = get_editable_program(program_id, request.user.id)
            if not program:
                return JsonResponse({'status': 404, 'message': 'Program not found. Please complete Basic Details first.'})

            outcome_type = post.get('outcome_type')
            if outcome_type not in ('PO', 'PSO', 'PEO'):
                return JsonResponse({'status': 400, 'message': 'Invalid outcome type.'})

            description = (post.get('description') or '').strip()
            if not description:
                return JsonResponse({'status': 400, 'message': 'Please enter a value before adding.'})

            record_bosc_history(request.user.id, program)

            next_seq = ProgramOutcomesMapping.objects.filter(program=program, outcome_type=outcome_type).count() + 1
            code = '%s%s' % (outcome_type, next_seq)

            row = ProgramOutcomesMapping.objects.create(
                program=program, outcome_type=outcome_type, code=code, description=description
            )

            return JsonResponse({'status': 200, 'enc_row_id': encrypt(row.id), 'code': code})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def update_program_outcome_row(request):
    if request.method == 'POST':
        try:
            row_id = decrypt(request.POST.get('row_id'))
            row = ProgramOutcomesMapping.objects.filter(id=row_id).filter(
                Q(program__created_by_id=request.user.id) | Q(program__pending_at_id=request.user.id)
            ).select_related('program').first()
            if not row:
                return JsonResponse({'status': 404, 'message': 'Row not found.'})

            description = (request.POST.get('description') or '').strip()
            if not description:
                return JsonResponse({'status': 400, 'message': 'Please enter a value before saving.'})

            record_bosc_history(request.user.id, row.program)
            row.description = description
            row.save(update_fields=['description'])

            return JsonResponse({'status': 200, 'description': description})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def delete_program_outcome_row(request):
    if request.method == 'POST':
        try:
            row_id = decrypt(request.POST.get('row_id'))
            row = ProgramOutcomesMapping.objects.filter(id=row_id).filter(
                Q(program__created_by_id=request.user.id) | Q(program__pending_at_id=request.user.id)
            ).select_related('program').first()
            if not row:
                return JsonResponse({'status': 404, 'message': 'Row not found.'})

            program = row.program
            outcome_type = row.outcome_type
            record_bosc_history(request.user.id, program)
            row.delete()

            # Close the gap: renumber the remaining rows of this outcome type back to a contiguous sequence
            remaining = ProgramOutcomesMapping.objects.filter(
                program=program, outcome_type=outcome_type
            ).order_by('id')
            updated = []
            for i, remaining_row in enumerate(remaining):
                new_code = '%s%s' % (outcome_type, i + 1)
                if remaining_row.code != new_code:
                    remaining_row.code = new_code
                    remaining_row.save(update_fields=['code'])
                updated.append({'enc_row_id': encrypt(remaining_row.id), 'code': new_code})

            return JsonResponse({'status': 200, 'updated': updated})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})


@login_required
@csrf_exempt
@group_required('BOSCO', 'BOSC')
def save_program_outcomes(request):
    if request.method == 'POST':
        try:
            program_id = decrypt(request.POST.get('program_id'))
            program = get_editable_program(program_id, request.user.id)
            if not program:
                return JsonResponse({'status': 404, 'message': 'Program not found. Please complete Basic Details first.'})

            if not ProgramOutcomesMapping.objects.filter(program=program).exists():
                return JsonResponse({
                    'status': 400,
                    'message': 'Add at least one PO, PSO, or PEO before continuing.',
                })

            program.active_step = 4
            program.save(update_fields=['active_step'])

            enc_id = encrypt(program.id)
            if program.program_status_id == 1:
                redirect_url = '/programs/final_preview/%s' % enc_id
            else:
                redirect_url = '/programs/program_details/%s' % enc_id

            return JsonResponse({'status': 200, 'redirect_url': redirect_url})
        except Exception as e:
            ErrorLogs.objects.create(user_id=request.user.id, log=str(e), info=str(request.POST))
            return JsonResponse({'status': 500, 'message': str(e)})
    return JsonResponse({'status': 405})
