from django.db.models import Q, F
from django.db.models import IntegerField
from django.db.models.functions import Cast

import sal.plugin


TITLES = {
    'cycle_ok': 'Batteries with less than 300 cycles',
    'cycle_warning': 'Batteries with 300-500 cycles',
    'cycle_alert': 'Batteries with more than 500 cycles',
    'cycle_unknown': 'Machines with no battery cycle data'}
PLUGIN_Q = Q(pluginscriptsubmission__plugin='Battery')
CYCLE_Q = Q(pluginscriptsubmission__pluginscriptrow__pluginscript_name='CycleCount')
LAPTOPS_Q = Q(machine_model__contains='Book')


class BatteryCycleCount(sal.plugin.Widget):

    description = "Cycle Count Battery Information"
    supported_os_families = [sal.plugin.OSFamilies.darwin]

    def get_context(self, queryset, **kwargs):
        queryset = queryset.filter(os_family='Darwin')
        context = self.super_get_context(queryset, **kwargs)
        
        cycle_plugin_results = queryset.filter(
            pluginscriptsubmission__plugin='Battery',
            pluginscriptsubmission__pluginscriptrow__pluginscript_name="CycleCount")
        
        cycle_plugin_results = cycle_plugin_results.annotate(
            pluginscript_data=F(
                "pluginscriptsubmission__pluginscriptrow__"
                "pluginscript_data"))
        cycle_plugin_results = cycle_plugin_results.values(
            "pluginscript_data").annotate(
                count=Count("pluginscript_data")).order_by("pluginscript_data")

        counter = Counter()
        
        
        context['cycle_ok_label'] = '< 300'
        context['cycle_warning_label'] = '300 - 500'
        context['cycle_alert_label'] = '500 +'
        context['cycle_unknown_label'] = 'No Data'
        context['cycle_ok'] = self._filter(queryset, 'cycle_ok').count()
        context['cycle_warning'] = self._filter(queryset, 'cycle_warning').count()
        context['cycle_alert'] = self._filter(queryset, 'cycle_alert').count()
        context['cycle_unknown'] = (
            queryset.filter(LAPTOPS_Q).count() - context['cycle_ok'] - context['cycle_alert'] - context['c$
        return context

    def filter(self, machines, data):
        if data not in TITLES:
            return None, None
        return self._filter(machines, data), TITLES[data]

    def _filter(self, machines, data):
        if data == 'cycle_ok':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        CYCLE_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__lt=300))
        elif data == 'cycle_warning':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        CYCLE_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__range=(300, 500)))
        elif data == 'cycle_alert':
            machines = (
                machines
                .filter(PLUGIN_Q,
                        CYCLE_Q,
                        pluginscriptsubmission__pluginscriptrow__pluginscript_data__gt=500))
        elif data == 'cycle_unknown':
            machines = (
                machines
                .filter(LAPTOPS_Q)
                .exclude(pk__in=self._filter(machines, 'cycle_ok').values('pk'))
                .exclude(pk__in=self._filter(machines, 'cycle_warning').values('pk'))
                .exclude(pk__in=self._filter(machines, 'cycle_alert').values('pk')))
        else:
            machines = None

        return machines

