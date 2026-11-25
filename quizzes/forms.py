from django import forms
from django.forms import inlineformset_factory

from .models import AnswerOption, Question, Quiz


class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            existing = widget.attrs.get("class", "")
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{existing} form-check-input".strip()
            elif isinstance(widget, forms.RadioSelect):
                widget.attrs["class"] = f"{existing}".strip()
            elif isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs["class"] = f"{existing} form-select".strip()
            else:
                widget.attrs["class"] = f"{existing} form-control".strip()


class QuizForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Quiz
        fields = ["title", "description", "is_published"]
        widgets = {"description": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class QuestionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Question
        fields = ["text", "order"]
        widgets = {"text": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class AnswerOptionForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = AnswerOption
        fields = ["text", "is_correct"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


AnswerOptionFormSet = inlineformset_factory(
    Question,
    AnswerOption,
    form=AnswerOptionForm,
    fields=["text", "is_correct"],
    extra=4,
    min_num=2,
    validate_min=True,
    max_num=6,
    can_delete=True,
)
