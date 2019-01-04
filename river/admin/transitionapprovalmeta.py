from django import forms
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType

from river.models.fields.state import StateField, workflow_registry
from river.models.transitionapprovalmeta import TransitionApprovalMeta


def get_workflow_choices():
    class_by_id = lambda cid: workflow_registry.class_index[cid]
    result = []
    for class_id, field_names in workflow_registry.workflows.items():
        cls = class_by_id(class_id)
        content_type = ContentType.objects.get_for_model(cls)
        for field_name in field_names:
            result.append(("%s %s" % (content_type.pk, field_name), "%s.%s - %s" % (cls.__module__, cls.__name__, field_name)))
    return result


class TransitionApprovalMetaForm(forms.ModelForm):
    workflow = forms.ChoiceField(choices=get_workflow_choices())

    class Meta:
        model = TransitionApprovalMeta
        fields = ('workflow', 'source_state', 'destination_state', 'permissions', 'groups', 'priority', 'action_text')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance", None)
        if instance and instance.pk:
            self.declared_fields['workflow'].initial = "%s %s" % (instance.content_type.pk, instance.field_name)

        super(TransitionApprovalMetaForm, self).__init__(*args, **kwargs)

    def clean_workflow(self):
        if self.cleaned_data.get('workflow') == '' or ' ' not in self.cleaned_data.get('workflow'):
            return None, None
        else:
            return self.cleaned_data.get('workflow').split(" ")

    def save(self, *args, **kwargs):
        content_type_pk, field_name = self.cleaned_data.get('workflow')
        instance = super(TransitionApprovalMetaForm, self).save(commit=False)
        instance.content_type = ContentType.objects.get(pk=content_type_pk)
        instance.field_name = field_name
        return super(TransitionApprovalMetaForm, self).save(*args, **kwargs)


class TransitionApprovalMetaAdmin(admin.ModelAdmin):
    form = TransitionApprovalMetaForm
    list_display = ('model_class', 'field_name', 'source_state', 'destination_state', 'priority')

    def model_class(self, obj):
        cls = obj.content_type.model_class()
        return "%s.%s" % (cls.__module__, cls.__name__)


admin.site.register(TransitionApprovalMeta, TransitionApprovalMetaAdmin)
