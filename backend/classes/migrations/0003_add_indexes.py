from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('classes', '0002_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='classroom',
            index=models.Index(fields=['teacher', '-created_at'], name='cr_teacher_created_idx'),
        ),
        migrations.AddIndex(
            model_name='classroom',
            index=models.Index(fields=['code'], name='cr_code_idx'),
        ),
        migrations.AddIndex(
            model_name='team',
            index=models.Index(fields=['class_room'], name='team_classroom_idx'),
        ),
    ]
