# Generated by Django 5.2.1 on 2025-07-08 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ImmigrationProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Full name', max_length=100)),
                ('age', models.CharField(help_text='Age', max_length=100)),
                ('current_country', models.CharField(help_text='Current country', max_length=100)),
                ('reason_for_immigration', models.CharField(choices=[('Job', 'Job'), ('Education', 'Education')], default='Education', max_length=20)),
                ('target_country', models.CharField(choices=[('USA', 'USA'), ('Canada', 'Canada'), ('Australia', 'Australia'), ('Germany', 'Germany'), ('Netherlands', 'Netherlands'), ('New Zealand', 'New Zealand'), ('Other', 'Other')], default='Germany', max_length=30)),
                ('target_job', models.CharField(blank=True, help_text='Desired job title', max_length=100, null=True)),
                ('experience', models.TextField(blank=True, help_text='Relevant experience (free text)', null=True)),
                ('previous_degrees', models.CharField(choices=[('Bachelor', 'Bachelor'), ('Master', 'Master'), ('PhD', 'PhD'), ('Other', 'Other')], default='Bachelor', max_length=30)),
                ('target_education_degree', models.CharField(choices=[('Bachelor', 'Bachelor'), ('Master', 'Master'), ('PhD', 'PhD'), ('Other', 'Other')], default='Bachelor', max_length=30)),
                ('target_position', models.CharField(blank=True, help_text='Target Position the user want to apply for', max_length=100, null=True)),
                ('target_education_field', models.CharField(blank=True, help_text='Field of study', max_length=100, null=True)),
                ('language_proficiency', models.TextField(blank=True, help_text='Language proficiency (free text)', null=True)),
                ('financial_status', models.TextField(blank=True, help_text='Financial status (free text)', null=True)),
                ('family_ties', models.TextField(blank=True, help_text='Family ties (free text)', null=True)),
                ('health_status', models.TextField(blank=True, help_text='Health status (free text)', null=True)),
                ('criminal_record', models.TextField(blank=True, help_text='Criminal record (free text)', null=True)),
            ],
        ),
    ]
