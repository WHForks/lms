from operator import attrgetter
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.db.models import signals, sql
from django.utils import timezone

from core.db.models import SoftDeletionModel

if TYPE_CHECKING:
    # TODO: Remove once Collector in django-stubs has attribute types.
    Collector = Any
else:
    from django.db.models.deletion import Collector


class SoftDeleteService:
    """
    Supports `deleted_at` field value update for models that implement
    soft-delete interface by subclassing `SoftDeletionModel`.
    """
    def __init__(self, using, keep_parents=False):
        self.using = using
        self.keep_parents = keep_parents

    def delete(self, objects):
        collector = Collector(using=self.using)
        collector.collect(objects, keep_parents=self.keep_parents)
        now = timezone.now()
        self.__update_models(collector, now)

    def restore(self, objects):
        collector = Collector(using=self.using)
        collector.collect(objects, keep_parents=self.keep_parents)
        self.__update_models(collector, None)

    def __update_models(self, collector: Collector, deleted_at_value):
        # sort instance collections
        for model, instances in collector.data.items():
            if not issubclass(model, SoftDeletionModel):
                continue
            collector.data[model] = sorted(instances, key=attrgetter("pk"))

        # if possible, bring the models in an order suitable for databases that
        # don't support transactions or cannot defer constraint checks until the
        # end of a transaction.
        collector.sort()

        with transaction.atomic(using=collector.using, savepoint=False):
            # send pre_delete signals
            for model, obj in collector.instances_with_model():
                if not issubclass(model, SoftDeletionModel):
                    continue
                if not model._meta.auto_created:
                    signals.pre_delete.send(
                        sender=model, instance=obj, using=collector.using
                    )

            # Update fast deletes
            for qs in collector.fast_deletes:
                if not issubclass(qs.model, SoftDeletionModel):
                    continue
                qs.update(deleted_at=deleted_at_value)

            # reverse instance collections
            for instances in collector.data.values():
                instances.reverse()

            # Update instances
            for model, instances in collector.data.items():
                if not issubclass(model, SoftDeletionModel):
                    continue
                query = sql.UpdateQuery(model)
                pk_list = [obj.pk for obj in instances]
                query.update_batch(pk_list,
                                   {"deleted_at": deleted_at_value},
                                   collector.using)
                for obj in instances:
                    obj.deleted_at = deleted_at_value

                if not model._meta.auto_created:
                    for obj in instances:
                        signals.post_delete.send(
                            sender=model, instance=obj, using=collector.using
                        )


# -- Saved filters helpers --------------------------------------------------
from typing import Any
from django.http import QueryDict
import logging
logger = logging.getLogger(__name__)


def querydict_to_json(qd: QueryDict) -> dict:
    """Convert a QueryDict to a JSON-serializable dict.

    Handles both multi-valued keys (key=a&key=b) and comma-separated values (key=a,b).
    Single-valued keys are stored as scalars, multi-valued keys as lists.
    Empty strings are filtered out to avoid storing empty selections.
    """
    result: dict[str, Any] = {}
    for k in qd.keys():
        vals = qd.getlist(k)
        # Expand comma-separated values (frontend sends "0,1,2" not separate params)
        expanded = []
        for v in vals:
            if v:  # only non-empty values
                # Split by comma if present
                if ',' in v:
                    expanded.extend(v.split(','))
                else:
                    expanded.append(v)
        
        if len(expanded) == 0:
            # Store empty string to indicate "no selection"
            result[k] = ""
            continue
        
        # Multiple values → list; single value → scalar
        result[k] = expanded if len(expanded) > 1 else expanded[0]
    return result


def save_user_filter(user, target: str, data: dict) -> None:
    """Create or update a SavedFilter for (user, target).
    
    Args:
        user: The user owning the filter
        target: Filter identifier (e.g., "learning:student_assignments")
        data: Filter data as dict (typically from querydict_to_json)
    """
    from core.models import SavedFilter
    from django.conf import settings
    
    if not isinstance(data, dict):
        return
    
    if settings.DEBUG:
        logger.debug(
            "[SavedFilter] Saving filters user=%s target=%s keys=%s",
            getattr(user, 'pk', None),
            target,
            list(data.keys()),
        )
    
    try:
        SavedFilter.objects.update_or_create(
            user=user,
            target=target,
            defaults={"data": data},
        )
    except Exception as exc:
        logger.exception(
            "[SavedFilter] Failed to save filters user=%s target=%s",
            getattr(user, 'pk', None),
            target,
        )


class FilterAutoSaveMixin:
    """
    Mixin for DRF ListAPIView or django-filter BaseFilterView to auto-save
    filter params for authenticated users.

    Expects:
    - self.request to be available
    - self.filterset_class (or self.get_filterset_class()) to have Meta.fields
    - A target identifier passed to constructor or set as class attribute
    
    Usage in DRF ListAPIView:
        class MyListView(FilterAutoSaveMixin, ListAPIView):
            filterset_class = MyFilterSet
            filter_auto_save_target = "my_app:my_filters"
    
    Usage in django-filter BaseFilterView (e.g., for CSV export):
        class MyFilterView(FilterAutoSaveMixin, CuratorOnlyMixin, BaseFilterView):
            filterset_class = MyFilterSet
            filter_auto_save_target = "my_app:my_filters"
    """
    filter_auto_save_target: str = None  # Should be set on subclass or instance

    def _save_filter_state(self, request):
        """Extract and save filter state from request.GET."""
        if not request.user.is_authenticated or not request.GET:
            return
        
        target = self.filter_auto_save_target
        if not target:
            return
        
        try:
            data = querydict_to_json(request.GET)
            # Whitelist by filterset_class.Meta.fields if available
            allowed = getattr(
                getattr(self, 'filterset_class', None) or type(self),
                'Meta',
                None
            )
            if allowed:
                allowed_fields = getattr(allowed, 'fields', None)
                if allowed_fields and isinstance(allowed_fields, (list, tuple, set)):
                    data = {
                        k: v for k, v in data.items() if k in set(allowed_fields)
                    }
            save_user_filter(request.user, target, data)
        except Exception:
            # Best-effort: never fail the view because of filter persistence
            pass

    # For DRF ListAPIView
    def list(self, request, *args, **kwargs):
        self._save_filter_state(request)
        return super().list(request, *args, **kwargs)

    # For django-filter BaseFilterView (HTML/CSV views)
    def get(self, request, *args, **kwargs):
        self._save_filter_state(request)
        return super().get(request, *args, **kwargs)
