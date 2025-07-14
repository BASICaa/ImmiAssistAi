from django import forms
from .models import ImmigrationProfile

class QueryForm(forms.Form):
    user_msg = forms.CharField(
        label='',
        widget=forms.Textarea(attrs={
            'placeholder': 'Ask about company or university info, deadlines, etc.',
            'class': 'query-input'
        })
    )

class ImmigrationProfileForm(forms.ModelForm):
    class Meta:
        model = ImmigrationProfile
        fields = ['name', 'age', 'current_country', 'reason_for_immigration', 'target_country', 'target_job', 'experience', 'target_education_field', 'previous_degrees', 'target_education_degree', 'target_position', 'language_proficiency', 'financial_status', 'family_ties', 'health_status', 'criminal_record']
        common_attrs = {
            'class': 'w-full rounded-lg border border-slate-300 px-4 py-2 focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200 transition duration-150 ease-in-out',
        }
        widgets = {
            'name': forms.TextInput(attrs={**common_attrs, 'placeholder': 'Your Full Name'}),
            'age': forms.TextInput(attrs={**common_attrs, 'placeholder': 'Your Age'}),
            'current_country': forms.TextInput(attrs={**common_attrs, 'placeholder': 'Your Current Country'}),
            'reason_for_immigration': forms.Select(attrs=common_attrs),
            'target_country': forms.Select(attrs=common_attrs),
            'target_job': forms.TextInput(attrs={**common_attrs, 'placeholder': 'Desired job title'}),
            'experience': forms.Textarea(attrs={**common_attrs, 'placeholder': 'Describe your relevant experience', 'rows': 3}),
            'target_education_field': forms.TextInput(attrs={**common_attrs, 'placeholder': 'e.g., Computer Science'}),
            'previous_degrees': forms.Select(attrs=common_attrs),
            'target_education_degree': forms.Select(attrs=common_attrs),
            'target_position': forms.TextInput(attrs={**common_attrs, 'placeholder': 'Desired position'}),
            'language_proficiency': forms.Textarea(attrs={**common_attrs, 'placeholder': 'e.g., IELTS: 7.5, German: B1', 'rows': 3}),
            'financial_status': forms.Textarea(attrs={**common_attrs, 'placeholder': 'e.g., Self-funded, Scholarship', 'rows': 3}),
            'family_ties': forms.Textarea(attrs={**common_attrs, 'placeholder': 'e.g., Cousin in Berlin', 'rows': 3}),
            'health_status': forms.Textarea(attrs={**common_attrs, 'placeholder': 'e.g., Good', 'rows': 3}),
            'criminal_record': forms.Textarea(attrs={**common_attrs, 'placeholder': 'e.g., None', 'rows': 3}),
        }
        labels = {
            'name': "Name",
            'age': "Age",
            'current_country': "Current Country",
            'reason_for_immigration': "Reason for Immigration",
            'target_country': "Target Country",
            'target_job': "Target Job",
            'target_education_field': "Target Education Field",
            'target_education_degree': "Target Education Degree",
            'target_position': "Target Position",
            'experience': "Experience",
            'previous_degrees': "Previous Degrees",
            'language_proficiency': "Language Proficiency",
            'financial_status': "Financial Status",
            'family_ties': "Family Ties",
            'health_status': "Health Status",
            'criminal_record': "Criminal Record"
        }