from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, TemplateView, View

from apps.customers.models import Customer
from apps.drivers.models import Driver
from apps.shipments.models import Shipment, ShipmentEvent
from apps.shipments.state_machine import InvalidTransitionError, transition_shipment


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "backoffice/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()

        stats = Shipment.objects.aggregate(
            total=Count("id"),
            created=Count("id", filter=Q(status="created")),
            assigned=Count("id", filter=Q(status="assigned")),
            in_transit=Count("id", filter=Q(status__in=["picked_up", "in_transit"])),
            out_for_delivery=Count("id", filter=Q(status="out_for_delivery")),
            delivered_today=Count(
                "id",
                filter=Q(status="delivered", actual_delivery_date__date=today),
            ),
            not_delivered=Count("id", filter=Q(status="not_delivered")),
        )
        context["stats"] = stats

        context["recent_shipments"] = (
            Shipment.objects.select_related("sender", "driver", "driver__user")
            .order_by("-created_at")[:10]
        )

        context["today"] = today
        return context


class ShipmentListView(LoginRequiredMixin, ListView):
    template_name = "backoffice/shipments/list.html"
    context_object_name = "shipments"
    paginate_by = 25

    def get_queryset(self):
        qs = Shipment.objects.select_related(
            "sender", "driver", "driver__user", "external_carrier",
        ).order_by("-created_at")

        # Filtri
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(tracking_code__icontains=q)
                | Q(reference__icontains=q)
                | Q(recipient_name__icontains=q)
                | Q(sender__company_name__icontains=q)
            )

        delivery_type = self.request.GET.get("delivery_type")
        if delivery_type:
            qs = qs.filter(delivery_type=delivery_type)

        return qs

    def get_template_names(self):
        if self.request.htmx:
            return ["backoffice/shipments/_table.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = Shipment.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        context["current_q"] = self.request.GET.get("q", "")
        return context


class ShipmentDetailView(LoginRequiredMixin, DetailView):
    template_name = "backoffice/shipments/detail.html"
    context_object_name = "shipment"

    def get_object(self):
        return get_object_or_404(
            Shipment.objects.select_related(
                "sender", "driver", "driver__user",
                "external_carrier", "created_by",
            ).prefetch_related("events"),
            uuid=self.kwargs["uuid"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        shipment = context["shipment"]
        context["events"] = shipment.events.all()
        context["drivers"] = Driver.objects.filter(
            is_active=True, status="available",
        ).select_related("user")

        # POD
        pod = None
        try:
            pod = shipment.pod
        except Exception:
            pass
        context["pod"] = pod
        context["pod_photos"] = pod.photos.all() if pod else []

        from apps.shipments.state_machine import VALID_TRANSITIONS

        context["allowed_transitions"] = VALID_TRANSITIONS.get(shipment.status, [])
        context["status_choices"] = dict(Shipment.Status.choices)
        return context


class ShipmentCreateView(LoginRequiredMixin, CreateView):
    model = Shipment
    template_name = "backoffice/shipments/create.html"
    fields = [
        "sender", "sender_address",
        "recipient_name", "recipient_phone", "recipient_email",
        "delivery_address", "delivery_street", "delivery_city",
        "delivery_province", "delivery_postal_code",
        "delivery_type", "priority", "reference",
        "description", "packages_count", "weight_kg",
        "notes_internal", "estimated_delivery_date",
    ]

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        # Crea evento iniziale
        ShipmentEvent.objects.create(
            shipment=self.object,
            status="created",
            description="Spedizione creata",
            recorded_by=self.request.user,
        )
        return response

    def get_success_url(self):
        return f"/shipments/{self.object.uuid}/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["customers"] = Customer.objects.filter(is_active=True)
        return context


class ShipmentTransitionView(LoginRequiredMixin, View):
    def post(self, request, uuid):
        shipment = get_object_or_404(Shipment, uuid=uuid)
        new_status = request.POST.get("new_status")

        try:
            transition_shipment(
                shipment=shipment,
                new_status=new_status,
                user=request.user,
            )
        except InvalidTransitionError:
            pass

        if request.htmx:
            # Ricarica solo il dettaglio
            from django.template.loader import render_to_string
            from django.http import HttpResponse

            shipment.refresh_from_db()
            return redirect(f"/shipments/{uuid}/")

        return redirect(f"/shipments/{uuid}/")


class CustomerListView(LoginRequiredMixin, ListView):
    template_name = "backoffice/customers/list.html"
    context_object_name = "customers"
    paginate_by = 25

    def get_queryset(self):
        qs = Customer.objects.filter(is_active=True).order_by("company_name")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(
                Q(company_name__icontains=q) | Q(contact_name__icontains=q)
            )
        return qs
