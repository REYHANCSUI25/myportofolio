from django import forms
from django.forms import ModelForm

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
