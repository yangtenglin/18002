from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='roundresult',
            index=models.Index(fields=['game', 'round_number'], name='rr_game_round_idx'),
        ),
        migrations.AddIndex(
            model_name='roundresult',
            index=models.Index(fields=['game', 'team', 'round_number'], name='rr_game_team_round_idx'),
        ),
        migrations.AddIndex(
            model_name='roundresult',
            index=models.Index(fields=['game', 'round_number', '-score'], name='rr_game_round_score_idx'),
        ),
        migrations.AddIndex(
            model_name='cumulativeresult',
            index=models.Index(fields=['game', 'rank'], name='cr_game_rank_idx'),
        ),
        migrations.AddIndex(
            model_name='cumulativeresult',
            index=models.Index(fields=['game', '-final_score'], name='cr_game_score_idx'),
        ),
    ]
