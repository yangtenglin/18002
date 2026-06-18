from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decisions', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='decision',
            index=models.Index(fields=['game', 'round_number'], name='dec_game_round_idx'),
        ),
        migrations.AddIndex(
            model_name='decision',
            index=models.Index(fields=['team', 'game', 'round_number'], name='dec_team_game_round_idx'),
        ),
        migrations.AddIndex(
            model_name='decision',
            index=models.Index(fields=['game', 'round_number', 'is_submitted'], name='dec_game_round_submitted_idx'),
        ),
    ]
