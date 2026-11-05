from django import forms
from django.forms import ModelForm

from main.models import Education
from main.validators import strip_html_required, validate_period


class EducationForm(ModelForm):
    class Meta:
        model = Education
        fields = [
            "institution",
            "degree",
            "description",
            "started_at",
            "ended_at",
        ]

        labels = {
            "institution": "Institution",
            "degree": "Degree / Track",
            "description": "Description",
            "started_at": "Started",
            "ended_at": "Ended (leave blank if ongoing)",
        }

        widgets = {
            "institution": forms.TextInput(
                attrs={
                    "placeholder": "Universitas Indonesia",
                    "maxlength": 255,
                }
            ),
            "degree": forms.TextInput(
                attrs={
                    "placeholder": "S1 Ilmu Komputer KKI",
                    "maxlength": 255,
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "What did you study or focus on here?",
                    "rows": 3,
                }
            ),
            "started_at": forms.DateInput(
                attrs={"type": "date"}
            ),
            "ended_at": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def clean_institution(self):
        return strip_html_required(self.cleaned_data["institution"])

    def clean_degree(self):
        return strip_html_required(self.cleaned_data["degree"])

    def clean_description(self):
        return strip_html_required(self.cleaned_data["description"])

    def clean(self):
        cleaned_data = super().clean()
        validate_period(cleaned_data.get("started_at"), cleaned_data.get("ended_at"))
        return cleaned_data
