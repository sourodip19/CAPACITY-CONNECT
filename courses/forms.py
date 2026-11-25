from django import forms

from accounts.models import User

from .models import Course


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{existing} form-check-input".strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = f"{existing} form-select".strip()
            elif isinstance(widget, forms.FileInput):
                widget.attrs["class"] = f"{existing} form-control".strip()
            else:
                widget.attrs["class"] = f"{existing} form-control".strip()


class CourseForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Course
        fields = ["title", "description", "category", "status", "thumbnail"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if self.user and (self.user.is_superuser or self.user.role == User.Role.ADMIN):
            self.fields["trainer"] = forms.ModelChoiceField(
                queryset=User.objects.filter(role=User.Role.TRAINER, is_active=True),
                required=True,
                label="Trainer",
            )
            self.fields["trainer"].widget.attrs["class"] = "form-select"
            if self.instance and self.instance.pk:
                self.fields["trainer"].initial = self.instance.trainer
        self._apply_bootstrap()

    def save(self, commit=True):
        course = super().save(commit=False)
        if self.user and self.user.role == User.Role.TRAINER:
            course.trainer = self.user
        elif self.user and (self.user.is_superuser or self.user.role == User.Role.ADMIN):
            course.trainer = self.cleaned_data["trainer"]
        if commit:
            course.save()
        return course
