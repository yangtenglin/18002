from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulation', '0001_initial'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['class_room', '-created_at'], name='game_classroom_created_idx'),
        ),
        migrations.AddIndex(
            model_name='game',
            index=models.Index(fields=['status'], name='game_status_idx'),
        ),
        migrations.AddIndex(
            model_name='gameparameter',
            index=models.Index(fields=['game', 'round_number'], name='gp_game_round_idx'),
        ),
    ]
