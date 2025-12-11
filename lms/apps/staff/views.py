import datetime
import logging
from urllib import parse

from django.conf import settings
from django.db.models import Prefetch
from django.http import HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, QueryDict
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.views import View, generic
from django_filters import FilterSet
from django_filters.views import BaseFilterView
from rest_framework import serializers
from vanilla import TemplateView

import core.utils
from core.models import University, AcademicProgram, SavedFilter
from core.reports import dataframe_to_response
from core.services import FilterAutoSaveMixin, querydict_to_json, save_user_filter
from core.urls import reverse
from courses.constants import SemesterTypes
from courses.models import Course, Semester
from courses.utils import get_current_term_pair
from learning.gradebook.views import GradeBookListBaseView
from learning.models import Enrollment, Invitation
from learning.reports import (
    ProgressReportForInvitation,
    ProgressReportForSemester,
    ProgressReportFull,
)
from learning.settings import StudentStatuses
from staff.filters import EnrollmentInvitationFilter, StudentProfileFilter
from staff.models import Hint
from users.filters import StudentFilter
from users.mixins import CuratorOnlyMixin
from users.models import StudentProfile, StudentTypes

logger = logging.getLogger(__name__)


class StudentSearchCSVView(FilterAutoSaveMixin, CuratorOnlyMixin, BaseFilterView):
    context_object_name = "applicants"
    model = StudentProfile
    filterset_class = StudentFilter
    filter_auto_save_target = "staff:student_search"

    def get_queryset(self):
        return StudentProfile.objects.select_related("user")

    def get(self, request, *args, **kwargs):
        filterset_class = self.get_filterset_class()
        self.filterset = self.get_filterset(filterset_class)

        if (
            not self.filterset.is_bound
            or self.filterset.is_valid()
            or not self.get_strict()
        ):
            queryset = self.filterset.qs
        else:
            queryset = self.filterset.queryset.none()
        report = ProgressReportFull()
        custom_qs = report.get_queryset(base_queryset=queryset)
        df = report.generate(queryset=custom_qs)
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        file_name = f"sheet_{today}"
        return dataframe_to_response(df, "csv", file_name)


class StudentSearchView(FilterAutoSaveMixin, CuratorOnlyMixin, TemplateView):
    template_name = "lms/staff/student_search.html"
    filter_auto_save_target = "staff:student_search"
    filterset_class = StudentFilter

    def get_context_data(self, **kwargs):
        # Load saved filter state (if any) for the authenticated user so the
        # template can pre-fill inputs after a page refresh.
        saved_data = None
        try:
            if getattr(self.request, 'user', None) and self.request.user.is_authenticated:
                from core.models import SavedFilter
                try:
                    obj = SavedFilter.objects.filter(user=self.request.user, target='staff:student_search').first()
                    if obj:
                        saved_data = obj.data or {}
                except Exception:
                    saved_data = None
        except Exception:
            saved_data = None

        context = {
            "json_api_uri": reverse("staff:student_search_json"),
            "saved_filters": saved_data,
            "admission_years": (
                StudentProfile.objects.filter(year_of_admission__isnull=False)
                .values_list("year_of_admission", flat=True)
                .order_by("year_of_admission")
                .distinct()
            ),
            "universities": University.objects.all(),
            "academic_programs": AcademicProgram.objects.all(),
            "types": StudentTypes.choices,
            "status": StudentStatuses.values,
            "cnt_enrollments": range(StudentFilter.ENROLLMENTS_MAX + 1),
            "is_paid_basis": [("1", "Yes"), ("0", "No")],
        }
        return context


class ResetStudentSearchFiltersView(CuratorOnlyMixin, View):
    """Endpoint to reset saved filters for student search for current user."""

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)
        try:
            SavedFilter.objects.filter(user=request.user, target='staff:student_search').delete()
            return JsonResponse({"status": "ok"})
        except Exception:
            logger.exception("[StudentSearch] Failed to delete saved filter")
            return JsonResponse({"error": "failed"}, status=500)


class ExportsView(CuratorOnlyMixin, generic.TemplateView):
    template_name = "staff/exports.html"

    def get_context_data(self, **kwargs):
        current_term = get_current_term_pair()
        prev_term = current_term.get_prev()
        context = {
            "current_term": current_term,
            "prev_term": {"year": prev_term.year, "type": prev_term.type},
        }
        return context


class ProgressReportFullView(CuratorOnlyMixin, generic.base.View):
    def get(self, request, output_format, *args, **kwargs):
        report = ProgressReportFull()
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        file_name = f"sheet_{today}"
        return dataframe_to_response(report.generate(), output_format, file_name)


class ProgressReportForSemesterView(CuratorOnlyMixin, generic.base.View):
    def get(self, request, output_format, *args, **kwargs):
        # Validate year and term GET params
        try:
            term_year = int(self.kwargs["term_year"])
            if term_year < settings.ESTABLISHED:
                raise ValueError("ProgressReportForSemester: Wrong year format")
            term_type = self.kwargs["term_type"]
            if term_type not in SemesterTypes.values:
                raise ValueError("ProgressReportForSemester: Wrong term format")
            filters = {"year": term_year, "type": term_type}
            semester = get_object_or_404(Semester, **filters)
        except (KeyError, ValueError):
            return HttpResponseBadRequest()
        report = ProgressReportForSemester(semester)
        file_name = "sheet_{}_{}".format(semester.year, semester.type)
        return dataframe_to_response(report.generate(), output_format, file_name)


class EnrollmentInvitationListView(CuratorOnlyMixin, TemplateView):
    template_name = "lms/staff/enrollment_invitations.html"

    def get(self, request, *args, **kwargs):
        # Filterset knows how to validate input data too
        invitations = Invitation.objects.select_related("semester").order_by(
            "-semester__index", "name"
        )
        filter_set = EnrollmentInvitationFilter(
            data=self.request.GET, queryset=invitations
        )
        context = self.get_context_data(filter_set, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, filter_set: FilterSet, **kwargs):
        context = {
            "filter_form": filter_set.form,
            "enrollment_invitations": filter_set.qs,
        }
        return context


class InvitationStudentsProgressReportView(CuratorOnlyMixin, View):
    def get(self, request, output_format, invitation_id, *args, **kwargs):
        invitation = get_object_or_404(Invitation.objects.filter(pk=invitation_id))
        report = ProgressReportForInvitation(invitation)
        term = invitation.semester
        file_name = f"sheet_invitation_{invitation.pk}_{term.year}_{term.type}"
        return dataframe_to_response(report.generate(), output_format, file_name)


class HintListView(CuratorOnlyMixin, generic.ListView):
    context_object_name = "faq"
    template_name = "staff/warehouse.html"

    def get_queryset(self):
        return Hint.objects.order_by("sort")


class StudentFacesView(CuratorOnlyMixin, TemplateView):
    """Photo + names to memorize newbies"""

    template_name = "lms/staff/student_faces.html"

    class InputSerializer(serializers.Serializer):
        university = serializers.ChoiceField(required=True, choices=())
        year = serializers.IntegerField(
            label="Year of Admission", required=True, min_value=settings.ESTABLISHED
        )
        type = serializers.ChoiceField(
            required=False, allow_blank=True, choices=StudentTypes.choices
        )

    def get_template_names(self):
        if "print" in self.request.GET:
            self.template_name = "lms/staff/student_faces_printable.html"
        return super().get_template_names()

    def get(self, request, *args, **kwargs):
        universities = University.objects.all()
        assert len(universities) > 0
        serializer = self.InputSerializer(data=request.GET)
        serializer.fields["university"].choices = [(b.pk, b.name) for b in universities]
        
        # Load saved filters if no URL params provided
        if not request.GET and request.user.is_authenticated:
            try:
                saved_data = SavedFilter.objects.get(
                    user=request.user, target="staff:student_faces"
                ).data
                
                # Redirect to same page with saved params in URL
                params = parse.urlencode(saved_data, doseq=True)
                return HttpResponseRedirect(f"{request.path}?{params}")
            except SavedFilter.DoesNotExist:
                pass
        
        # Use defaults if no params and no saved filters
        if not request.GET:
            university = universities[0]
            current_term = get_current_term_pair(university.city.get_timezone())
            url = f"{request.path}?university={university.pk}&year={current_term.year}&type={StudentTypes.REGULAR}"
            return HttpResponseRedirect(url)
        
        filter_set = StudentProfileFilter(
            universities, data=request.GET, queryset=self.get_queryset()
        )
        context = self.get_context_data(filter_set, **kwargs)
        return self.render_to_response(context)

    def get_context_data(self, filter_set: FilterSet, **kwargs):
        # Load saved filters for this user
        saved_filters = {}
        if self.request.user.is_authenticated:
            try:
                saved_filters = SavedFilter.objects.get(
                    user=self.request.user, target="staff:student_faces"
                ).data
                
                from django.conf import settings
                if settings.DEBUG:
                    logger.debug(
                        "[StudentFaces] Loaded saved filters for user %s keys=%s",
                        self.request.user.pk,
                        list(saved_filters.keys()),
                    )
            except SavedFilter.DoesNotExist:
                pass
        
        context = {
            "filter_form": filter_set.form,
            "users": [x.user for x in filter_set.qs],
            "StudentStatuses": StudentStatuses,
            "saved_filters": saved_filters,
        }
        return context

    def post(self, request, *args, **kwargs):
        from django.conf import settings
        
        universities = University.objects.all()
        filter_set = StudentProfileFilter(
            universities, data=request.POST, queryset=self.get_queryset()
        )
        
        if filter_set.is_valid():
            # Save filters for the current user
            if request.user.is_authenticated:
                filter_data = querydict_to_json(request.POST)
                
                save_user_filter(
                    user=request.user,
                    target="staff:student_faces",
                    data=filter_data,
                )
            
            # Redirect to same page with filter params
            params = request.POST.urlencode()
            return HttpResponseRedirect(f"{request.path}?{params}")
        
        context = self.get_context_data(filter_set, **kwargs)
        return self.render_to_response(context)

    def get_queryset(self):
        qs = StudentProfile.objects.select_related("user").order_by(
            "user__last_name", "user__first_name", "pk"
        )
        if "print" in self.request.GET:
            qs = qs.exclude(status__in=StudentStatuses.inactive_statuses)
        return qs


class SaveStudentFacesFiltersView(CuratorOnlyMixin, View):
    """AJAX endpoint to save student faces filters."""
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)
        
        try:
            filter_data = querydict_to_json(request.POST)
            
            save_user_filter(
                user=request.user,
                target="staff:student_faces",
                data=filter_data,
            )
            return JsonResponse({"status": "ok"})
        except Exception as e:
            logger.exception("[StudentFaces] Error saving filters")
            return JsonResponse({"error": "Failed to save filters"}, status=500)


class CourseParticipantsIntersectionView(CuratorOnlyMixin, generic.TemplateView):
    template_name = "staff/courses_intersection.html"

    def get_context_data(self, **kwargs):
        term_pair = get_current_term_pair()
        all_courses_in_term = Course.objects.filter(
            semester__index=term_pair.index
        ).select_related("meta_course")
        # Get participants
        query_courses = self.request.GET.getlist("course_offerings[]", [])
        query_courses = [int(t) for t in query_courses if t]
        results = list(
            Course.objects.filter(pk__in=query_courses)
            .select_related("meta_course")
            .prefetch_related(
                Prefetch(
                    "enrollment_set",
                    queryset=(
                        Enrollment.active.select_related("student").only(
                            "pk",
                            "course_id",
                            "student_id",
                            "student__username",
                            "student__first_name",
                            "student__last_name"
                        )
                    ),
                )
            )
        )
        if len(results) > 1:
            first_course, second_course = (
                {e.student_id for e in co.enrollment_set.all()} for co in results
            )
            intersection = first_course.intersection(second_course)
        else:
            intersection = set()
        context = {
            "course_offerings": all_courses_in_term,
            "intersection": intersection,
            "current_term": "{} {}".format(_(term_pair.type), term_pair.year),
            "results": results,
            "query": {"course_offerings": query_courses},
        }
        return context


class GradeBookListView(CuratorOnlyMixin, GradeBookListBaseView):
    template_name = "staff/gradebook_list.html"

    def get_term_threshold(self):
        latest_term = Semester.objects.order_by("-index").first()
        return latest_term.index

    def get_context_data(self, **kwargs):
        semester_list = list(self.object_list)
        # Add stub term if we have only 1 term for the ongoing academic year
        if semester_list:
            current = semester_list[0]
            if current.type == SemesterTypes.AUTUMN:
                next_term = current.term_pair.get_next()
                term = Semester(type=next_term.type, year=next_term.year)
                term.course_offerings = []
                semester_list.insert(0, term)
            # Here we build a list of "academic years", that is, pairs consisting of autumn-spring semesters.
            # Semesters from the same academic year will be shown in the UI side by side.
            semester_list = [(a, s) for s, a in core.utils.chunks(semester_list, 2)]
        context = {"semester_list": semester_list}
        return context
