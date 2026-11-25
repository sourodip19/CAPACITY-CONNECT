from django import forms

from .models import LearningMaterial


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


class LearningMaterialForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = LearningMaterial
        fields = ["title", "description", "material_type", "file", "external_url", "order"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
        self.fields["file"].required = False
        self.fields["external_url"].required = False

    def clean(self):
        cleaned = super().clean()
        material_type = cleaned.get("material_type")
        file = cleaned.get("file")
        external_url = cleaned.get("external_url")
        if material_type == LearningMaterial.MaterialType.PDF and not file and not self.instance.file:
            self.add_error("file", "A PDF file is required for PDF materials.")
        if material_type == LearningMaterial.MaterialType.EXTERNAL_LINK and not external_url:
            self.add_error("external_url", "An external URL is required for link materials.")
        return cleaned
