from django.db import models
from django.core.exceptions import ValidationError

IMMIGRATION_REASON_CHOICES = [
    ("Job", "Job"),
    ("Education", "Education"),
]
TARGET_COUNTRY_CHOICES = [
    ("USA", "USA"),
    ("Canada", "Canada"),
    ("Australia", "Australia"),
    ("Germany", "Germany"),
    ("Netherlands", "Netherlands"),
    ("New Zealand", "New Zealand"),
    ("Other", "Other"),
]
TARGET_EDUCATION_DEGREE_CHOICES = [
    ("Bachelor", "Bachelor"),
    ("Master", "Master"),
    ("PhD", "PhD"),
    ("Other", "Other"),
]
PREVIOUS_DEGREE_CHOICES = [
    ("Bachelor", "Bachelor"),
    ("Master", "Master"),
    ("PhD", "PhD"),
    ("Other", "Other"),
]

class ImmigrationProfile(models.Model):
    name = models.CharField(max_length=100, help_text="Full name")
    age = models.CharField(max_length=100, help_text="Age")
    current_country = models.CharField(max_length=100, help_text="Current country")

    reason_for_immigration = models.CharField(
        max_length=20,
        choices=IMMIGRATION_REASON_CHOICES,
        default="Education",
    )
    target_country = models.CharField(
        max_length=30,
        choices=TARGET_COUNTRY_CHOICES,
        default="Germany",
    )

    target_job = models.CharField(
        max_length=100, blank=True, null=True, help_text="Desired job title"
    )
    experience = models.TextField(
        blank=True, null=True, help_text="Relevant experience (free text)"
    )

    previous_degrees = models.CharField(
        max_length=30,
        choices=PREVIOUS_DEGREE_CHOICES,
        default="Bachelor",
    )
    target_education_degree = models.CharField(
        max_length=30,
        choices=TARGET_EDUCATION_DEGREE_CHOICES,
        default="Bachelor",
    )
    target_position = models.CharField(
        max_length=100, blank=True, null=True, help_text="Target Position the user want to apply for"
    )
    target_education_field = models.CharField(
        max_length=100, blank=True, null=True, help_text="Field of study"
    )

    language_proficiency = models.TextField(blank=True, null=True, help_text="Language proficiency (free text)")
    financial_status = models.TextField(blank=True, null=True, help_text="Financial status (free text)")
    family_ties = models.TextField(blank=True, null=True, help_text="Family ties (free text)")
    health_status = models.TextField(blank=True, null=True, help_text="Health status (free text)")
    criminal_record = models.TextField(blank=True, null=True, help_text="Criminal record (free text)")

    def clean(self):
        super().clean()
        if self.reason_for_immigration == "Job":
            if not self.target_job:
                raise ValidationError({"target_job": "Required for job immigration."})
        elif self.reason_for_immigration == "Education":
            if not self.target_education_field:
                raise ValidationError(
                    {"target_education_field": "Required for education immigration."}
                )

    def __str__(self):
        return f"{self.name} → {self.target_country}"