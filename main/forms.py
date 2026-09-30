from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.html import strip_tags

from main.models import Education


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
        institution = strip_tags(self.cleaned_data["institution"]).strip()
        if not institution:
            raise ValidationError("Institution can't contain only HTML tags.")
        return institution

    def clean_degree(self):
        degree = strip_tags(self.cleaned_data["degree"]).strip()
        if not degree:
            raise ValidationError("Degree can't contain only HTML tags.")
        return degree

    def clean_description(self):
        return strip_tags(self.cleaned_data["description"]).strip()
