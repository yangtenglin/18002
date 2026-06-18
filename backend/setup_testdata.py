import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'backend.settings'
django.setup()

from users.models import User
from classes.models import ClassRoom, Team
from simulation.models import Game, GameParameter
from decisions.models import Decision
from simulation.engine import SimulationEngine
from django.utils import timezone

teacher = User.objects.get(username='teacher1')
classroom = ClassRoom.objects.filter(teacher=teacher).first()
print(f'Classroom: {classroom.name} ({classroom.code})')

team_a, _ = Team.objects.get_or_create(name='星际酒店集团', class_room=classroom)
team_b, _ = Team.objects.get_or_create(name='皇冠酒店集团', class_room=classroom)

students = list(User.objects.filter(role='student'))
if len(students) >= 4:
    team_a.members.set(students[:2])
    team_b.members.set(students[2:4])
    team_a.captain = students[0]
    team_b.captain = students[2]
team_a.save()
team_b.save()
print(f'Teams: {team_a.name}, {team_b.name}')

game, created = Game.objects.get_or_create(
    name='酒店经营模拟-第1期',
    class_room=classroom,
    defaults={'total_rounds': 8, 'status': 'running', 'current_round': 1, 'started_at': timezone.now()}
)
if created:
    GameParameter.objects.create(game=game, round_number=0)
    for rn in range(1, game.total_rounds + 1):
        GameParameter.objects.create(
            game=game, round_number=rn,
            market_base_demand=1000 + rn * 50,
            seasonal_factor=round(1.0 + 0.1 * ((rn % 4) - 1.5), 2),
            economic_factor=1.0, competition_intensity=0.5,
        )
print(f'Game: {game.name} (R{game.current_round}/{game.total_rounds})')

Decision.objects.get_or_create(
    team=team_a, game=game, round_number=1,
    defaults={
        'room_rate_standard': 480, 'room_rate_deluxe': 780, 'room_rate_suite': 1400,
        'food_budget': 60000, 'marketing_budget': 40000,
        'staff_training_budget': 25000, 'renovation_budget': 15000,
        'service_quality_target': 8.0, 'is_submitted': True,
    }
)
Decision.objects.get_or_create(
    team=team_b, game=game, round_number=1,
    defaults={
        'room_rate_standard': 520, 'room_rate_deluxe': 850, 'room_rate_suite': 1600,
        'food_budget': 45000, 'marketing_budget': 35000,
        'staff_training_budget': 20000, 'renovation_budget': 20000,
        'service_quality_target': 7.5, 'is_submitted': True,
    }
)
print('Decisions created for Round 1')

engine = SimulationEngine()
results = engine.calculate_round(game, 1)
for r in results:
    print(f'  {r.team.name}: profit={r.profit:.0f}, satisfaction={r.customer_satisfaction:.1f}, score={r.score:.1f}')

game.current_round = 2
game.save()
print(f'Game advanced to round {game.current_round}')
print('All test data ready!')
