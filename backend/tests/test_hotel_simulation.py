import math
from django.test import TestCase, Client, override_settings
from django.core.cache import cache
from users.models import User
from classes.models import ClassRoom, Team
from simulation.models import Game, GameParameter
from decisions.models import Decision
from dashboard.models import RoundResult, CumulativeResult
from simulation.engine import SimulationEngine

DUMMY_CACHE = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}


@override_settings(CACHES=DUMMY_CACHE)
class BaseTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.client = Client()

        self.teacher = User.objects.create_user(
            username='teacher_test', password='testpass123',
            role='teacher', email='teacher@test.com'
        )
        self.students = []
        for i in range(6):
            s = User.objects.create_user(
                username=f'student{i + 1}', password='testpass123',
                role='student', student_id=f'S{i + 1:03d}', email=f'student{i + 1}@test.com'
            )
            self.students.append(s)

    def _login(self, user):
        self.client.login(username=user.username, password='testpass123')

    def _create_classroom_with_teams(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班', 'description': '测试班级'})
        self.assertEqual(resp.status_code, 201)
        classroom_id = resp.data['id']

        teams = []
        team_names = ['星际酒店集团', '皇冠酒店集团', '翡翠酒店集团']
        for i, name in enumerate(team_names):
            resp = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': name, 'class_room': classroom_id})
            self.assertEqual(resp.status_code, 201)
            team_id = resp.data['id']
            teams.append(team_id)

            member_ids = [self.students[i * 2].id, self.students[i * 2 + 1].id]
            resp = self.client.post(
                f'/api/classrooms/{classroom_id}/teams/{team_id}/add-members/',
                {'user_ids': member_ids},
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 200)

        return classroom_id, teams

    def _create_game(self, classroom_id, total_rounds=4):
        self._login(self.teacher)
        resp = self.client.post('/api/games/', {
            'name': '酒店经营模拟-测试',
            'class_room': classroom_id,
            'total_rounds': total_rounds,
            'description': '完整模拟测试'
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        return resp.data['id']

    def _start_game(self, game_id):
        self._login(self.teacher)
        return self.client.post(f'/api/games/{game_id}/start/')

    def _submit_decision(self, game_id, team_id, student, data=None):
        self._login(student)
        if data is None:
            data = {
                'team': team_id,
                'room_rate_standard': 500,
                'room_rate_deluxe': 800,
                'room_rate_suite': 1500,
                'food_budget': 50000,
                'marketing_budget': 30000,
                'staff_training_budget': 20000,
                'renovation_budget': 10000,
                'service_quality_target': 7.0,
            }
        data['team'] = team_id
        return self.client.post(
            f'/api/games/{game_id}/decisions/',
            data,
            content_type='application/json'
        )

    def _advance_round(self, game_id):
        self._login(self.teacher)
        return self.client.post(f'/api/games/{game_id}/advance-round/')

    def _pause_game(self, game_id):
        self._login(self.teacher)
        return self.client.post(f'/api/games/{game_id}/pause/')


class TestUserRegistrationAndLogin(BaseTestCase):
    def test_teacher_register(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'new_teacher',
            'password': 'newpass123',
            'role': 'teacher',
            'email': 'new_teacher@test.com',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['user']['role'], 'teacher')

    def test_student_register(self):
        resp = self.client.post('/api/auth/register/', {
            'username': 'new_student',
            'password': 'newpass123',
            'role': 'student',
            'student_id': 'S099',
            'email': 'new_student@test.com',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['user']['role'], 'student')

    def test_teacher_login(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'teacher_test',
            'password': 'testpass123',
            'role': 'teacher',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['user']['role'], 'teacher')

    def test_student_login(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'student1',
            'password': 'testpass123',
            'role': 'student',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['user']['role'], 'student')

    def test_login_with_wrong_role(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'teacher_test',
            'password': 'testpass123',
            'role': 'student',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_login_with_wrong_password(self):
        resp = self.client.post('/api/auth/login/', {
            'username': 'teacher_test',
            'password': 'wrongpass',
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 401)

    def test_current_user(self):
        self._login(self.teacher)
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['username'], 'teacher_test')


class TestClassroomAndTeamManagement(BaseTestCase):
    def test_teacher_create_classroom(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班'})
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['name'], '酒店管理1班')
        self.assertEqual(resp.data['teacher'], self.teacher.id)
        self.assertTrue(resp.data['code'])

    def test_student_cannot_create_classroom(self):
        self._login(self.students[0])
        resp = self.client.post('/api/classrooms/', {'name': '非法班级'})
        self.assertEqual(resp.status_code, 403)

    def test_teacher_see_own_classrooms(self):
        self._login(self.teacher)
        self.client.post('/api/classrooms/', {'name': '班级A'})
        self.client.post('/api/classrooms/', {'name': '班级B'})
        resp = self.client.get('/api/classrooms/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_student_see_enrolled_classrooms(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班'})
        classroom_id = resp.data['id']
        resp = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': '测试团队', 'class_room': classroom_id})
        team_id = resp.data['id']
        self.client.post(
            f'/api/classrooms/{classroom_id}/teams/{team_id}/add-members/',
            {'user_ids': [self.students[0].id]},
            content_type='application/json'
        )

        self._login(self.students[0])
        resp = self.client.get('/api/classrooms/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['name'], '酒店管理1班')

    def test_create_team_and_add_members(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班'})
        classroom_id = resp.data['id']

        resp = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': '星际酒店集团', 'class_room': classroom_id})
        self.assertEqual(resp.status_code, 201)
        team_id = resp.data['id']

        resp = self.client.post(
            f'/api/classrooms/{classroom_id}/teams/{team_id}/add-members/',
            {'user_ids': [self.students[0].id, self.students[1].id]},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['members_detail']), 2)

    def test_student_cannot_create_team(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班'})
        classroom_id = resp.data['id']

        self._login(self.students[0])
        resp = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': '非法团队', 'class_room': classroom_id})
        self.assertEqual(resp.status_code, 403)

    def test_remove_member_from_team(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班'})
        classroom_id = resp.data['id']

        resp = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': '测试团队', 'class_room': classroom_id})
        team_id = resp.data['id']
        self.client.post(
            f'/api/classrooms/{classroom_id}/teams/{team_id}/add-members/',
            {'user_ids': [self.students[0].id, self.students[1].id]},
            content_type='application/json'
        )

        resp = self.client.post(
            f'/api/classrooms/{classroom_id}/teams/{team_id}/remove-members/',
            {'user_ids': [self.students[1].id]},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['members_detail']), 1)

    def test_classroom_detail_shows_teams(self):
        self._login(self.teacher)
        resp = self.client.post('/api/classrooms/', {'name': '酒店管理1班'})
        classroom_id = resp.data['id']
        self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': '团队A', 'class_room': classroom_id})
        self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': '团队B', 'class_room': classroom_id})

        resp = self.client.get(f'/api/classrooms/{classroom_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data['teams']), 2)


class TestGameCreationAndLifecycle(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.classroom_id, self.team_ids = self._create_classroom_with_teams()

    def test_teacher_create_game(self):
        game_id = self._create_game(self.classroom_id, total_rounds=4)
        self.assertIsNotNone(game_id)

        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{game_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], '酒店经营模拟-测试')
        self.assertEqual(resp.data['status'], 'draft')
        self.assertEqual(resp.data['current_round'], 0)
        self.assertEqual(resp.data['total_rounds'], 4)

    def test_game_parameters_auto_generated(self):
        game_id = self._create_game(self.classroom_id, total_rounds=4)

        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{game_id}/parameters/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 5)

        round_params = [p for p in resp.data if p['round_number'] > 0]
        self.assertEqual(len(round_params), 4)
        for p in round_params:
            self.assertIn('seasonal_factor', p)
            self.assertIn('market_base_demand', p)
            self.assertIn('competition_intensity', p)

    def test_student_cannot_create_game(self):
        self._login(self.students[0])
        resp = self.client.post('/api/games/', {
            'name': '非法模拟',
            'class_room': self.classroom_id,
            'total_rounds': 4,
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 403)

    def test_start_game(self):
        game_id = self._create_game(self.classroom_id)
        resp = self._start_game(game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'running')
        self.assertEqual(resp.data['current_round'], 1)
        self.assertIsNotNone(resp.data['started_at'])

    def test_cannot_start_finished_game(self):
        game_id = self._create_game(self.classroom_id)
        game = Game.objects.get(pk=game_id)
        game.status = 'finished'
        game.save()

        resp = self._start_game(game_id)
        self.assertEqual(resp.status_code, 400)

    def test_pause_running_game(self):
        game_id = self._create_game(self.classroom_id)
        self._start_game(game_id)
        resp = self._pause_game(game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'paused')

    def test_resume_paused_game(self):
        game_id = self._create_game(self.classroom_id)
        self._start_game(game_id)
        self._pause_game(game_id)
        resp = self._start_game(game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'running')

    def test_cannot_pause_non_running_game(self):
        game_id = self._create_game(self.classroom_id)
        resp = self._pause_game(game_id)
        self.assertEqual(resp.status_code, 400)

    def test_student_cannot_start_game(self):
        game_id = self._create_game(self.classroom_id)
        self._login(self.students[0])
        resp = self.client.post(f'/api/games/{game_id}/start/')
        self.assertEqual(resp.status_code, 403)

    def test_update_game_parameter(self):
        game_id = self._create_game(self.classroom_id)
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{game_id}/parameters/')
        param_id = resp.data[1]['id']

        resp = self.client.put(
            f'/api/games/{game_id}/parameters/{param_id}/',
            {'seasonal_factor': 1.3, 'economic_factor': 0.9},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertAlmostEqual(resp.data['seasonal_factor'], 1.3)
        self.assertAlmostEqual(resp.data['economic_factor'], 0.9)

    def test_student_cannot_update_game_parameter(self):
        game_id = self._create_game(self.classroom_id)
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{game_id}/parameters/')
        param_id = resp.data[1]['id']

        self._login(self.students[0])
        resp = self.client.put(
            f'/api/games/{game_id}/parameters/{param_id}/',
            {'seasonal_factor': 1.3},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 403)


class TestStudentDecisionSubmission(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.classroom_id, self.team_ids = self._create_classroom_with_teams()
        self.game_id = self._create_game(self.classroom_id, total_rounds=4)
        self._start_game(self.game_id)

    def test_team_member_submit_decision(self):
        team_id = self.team_ids[0]
        student = self.students[0]
        resp = self._submit_decision(self.game_id, team_id, student, {
            'room_rate_standard': 480,
            'room_rate_deluxe': 780,
            'room_rate_suite': 1400,
            'food_budget': 60000,
            'marketing_budget': 40000,
            'staff_training_budget': 25000,
            'renovation_budget': 15000,
            'service_quality_target': 8.0,
        })
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data['is_submitted'])
        self.assertEqual(resp.data['round_number'], 1)

    def test_another_member_of_same_team_submit(self):
        team_id = self.team_ids[0]
        self._submit_decision(self.game_id, team_id, self.students[0])

        resp = self._submit_decision(self.game_id, team_id, self.students[1])
        self.assertEqual(resp.status_code, 400)

    def test_non_team_member_cannot_submit(self):
        team_id = self.team_ids[0]
        other_student = self.students[2]
        resp = self._submit_decision(self.game_id, team_id, other_student)
        self.assertEqual(resp.status_code, 403)

    def test_cannot_submit_when_game_not_running(self):
        self._pause_game(self.game_id)
        team_id = self.team_ids[0]
        resp = self._submit_decision(self.game_id, team_id, self.students[0])
        self.assertEqual(resp.status_code, 400)

    def test_my_decision_view(self):
        team_id = self.team_ids[0]
        self._submit_decision(self.game_id, team_id, self.students[0])

        self._login(self.students[0])
        resp = self.client.get(f'/api/games/{self.game_id}/my-decision/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['team'], team_id)
        self.assertTrue(resp.data['is_submitted'])

    def test_my_decision_not_submitted(self):
        self._login(self.students[0])
        resp = self.client.get(f'/api/games/{self.game_id}/my-decision/')
        self.assertEqual(resp.status_code, 404)

    def test_teacher_cannot_use_my_decision(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/my-decision/')
        self.assertEqual(resp.status_code, 400)

    def test_teacher_views_all_decisions(self):
        for i, team_id in enumerate(self.team_ids):
            self._submit_decision(self.game_id, team_id, self.students[i * 2])

        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/decisions/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)

    def test_student_views_own_team_decision_only(self):
        for i, team_id in enumerate(self.team_ids):
            self._submit_decision(self.game_id, team_id, self.students[i * 2])

        self._login(self.students[0])
        resp = self.client.get(f'/api/games/{self.game_id}/decisions/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['team'], self.team_ids[0])

    def test_decision_data_integrity(self):
        team_id = self.team_ids[0]
        decision_data = {
            'room_rate_standard': 520,
            'room_rate_deluxe': 880,
            'room_rate_suite': 1680,
            'food_budget': 55000,
            'marketing_budget': 35000,
            'staff_training_budget': 22000,
            'renovation_budget': 12000,
            'service_quality_target': 7.5,
        }
        resp = self._submit_decision(self.game_id, team_id, self.students[0], decision_data)
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['room_rate_standard'], 520)
        self.assertEqual(resp.data['room_rate_deluxe'], 880)
        self.assertEqual(resp.data['room_rate_suite'], 1680)
        self.assertEqual(resp.data['food_budget'], 55000)
        self.assertEqual(resp.data['marketing_budget'], 35000)
        self.assertEqual(resp.data['staff_training_budget'], 22000)
        self.assertEqual(resp.data['renovation_budget'], 12000)
        self.assertAlmostEqual(resp.data['service_quality_target'], 7.5)


class TestSimulationEngineCalculation(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='engine_teacher', password='testpass123',
            role='teacher', email='engine_teacher@test.com'
        )
        self.classroom = ClassRoom.objects.create(
            name='引擎测试班级', code='ENGTEST01', teacher=self.teacher
        )
        self.teams = []
        self.students = []
        for i in range(3):
            s = User.objects.create_user(
                username=f'eng_student{i + 1}', password='testpass123',
                role='student', email=f'eng_student{i + 1}@test.com'
            )
            self.students.append(s)
            team = Team.objects.create(name=f'团队{i + 1}', class_room=self.classroom)
            team.members.add(s)
            self.teams.append(team)

        self.game = Game.objects.create(
            name='引擎计算测试', class_room=self.classroom,
            total_rounds=4, status='running', current_round=1
        )
        GameParameter.objects.create(game=self.game, round_number=0)
        for rn in range(1, 5):
            GameParameter.objects.create(
                game=self.game, round_number=rn,
                market_base_demand=1000 + rn * 50,
                seasonal_factor=round(1.0 + 0.1 * ((rn % 4) - 1.5), 2),
                economic_factor=1.0, competition_intensity=0.5,
            )

        self.engine = SimulationEngine()

    def test_single_round_calculation(self):
        Decision.objects.create(
            team=self.teams[0], game=self.game, round_number=1,
            room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
            food_budget=50000, marketing_budget=30000,
            staff_training_budget=20000, renovation_budget=10000,
            service_quality_target=7.0, is_submitted=True,
        )
        Decision.objects.create(
            team=self.teams[1], game=self.game, round_number=1,
            room_rate_standard=520, room_rate_deluxe=850, room_rate_suite=1600,
            food_budget=45000, marketing_budget=35000,
            staff_training_budget=18000, renovation_budget=15000,
            service_quality_target=6.5, is_submitted=True,
        )
        Decision.objects.create(
            team=self.teams[2], game=self.game, round_number=1,
            room_rate_standard=480, room_rate_deluxe=780, room_rate_suite=1400,
            food_budget=55000, marketing_budget=40000,
            staff_training_budget=25000, renovation_budget=8000,
            service_quality_target=8.0, is_submitted=True,
        )

        results = self.engine.calculate_round(self.game, 1)
        self.assertEqual(len(results), 3)

        for r in results:
            self.assertGreater(r.occupancy_rate_standard, 0)
            self.assertLessEqual(r.occupancy_rate_standard, 0.98)
            self.assertGreater(r.revenue_total, 0)
            self.assertGreater(r.cost_total, 0)
            self.assertGreaterEqual(r.customer_satisfaction, 1.0)
            self.assertLessEqual(r.customer_satisfaction, 10.0)
            self.assertGreaterEqual(r.market_share, 0)
            self.assertLessEqual(r.market_share, 1.0)
            self.assertGreaterEqual(r.score, 0)

    def test_no_decisions_returns_empty(self):
        results = self.engine.calculate_round(self.game, 1)
        self.assertEqual(results, [])

    def test_occupancy_rate_bounds(self):
        Decision.objects.create(
            team=self.teams[0], game=self.game, round_number=1,
            room_rate_standard=2000, room_rate_deluxe=2000, room_rate_suite=2000,
            food_budget=0, marketing_budget=0,
            staff_training_budget=0, renovation_budget=0,
            service_quality_target=1.0, is_submitted=True,
        )
        Decision.objects.create(
            team=self.teams[1], game=self.game, round_number=1,
            room_rate_standard=100, room_rate_deluxe=100, room_rate_suite=100,
            food_budget=100000, marketing_budget=100000,
            staff_training_budget=50000, renovation_budget=50000,
            service_quality_target=10.0, is_submitted=True,
        )

        results = self.engine.calculate_round(self.game, 1)
        for r in results:
            self.assertGreaterEqual(r.occupancy_rate_standard, 0.05)
            self.assertLessEqual(r.occupancy_rate_standard, 0.98)
            self.assertGreaterEqual(r.occupancy_rate_deluxe, 0.05)
            self.assertLessEqual(r.occupancy_rate_deluxe, 0.98)
            self.assertGreaterEqual(r.occupancy_rate_suite, 0.05)
            self.assertLessEqual(r.occupancy_rate_suite, 0.98)

    def test_market_share_sums_to_one(self):
        for team in self.teams:
            Decision.objects.create(
                team=team, game=self.game, round_number=1,
                room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                food_budget=50000, marketing_budget=30000,
                staff_training_budget=20000, renovation_budget=10000,
                service_quality_target=7.0, is_submitted=True,
            )

        results = self.engine.calculate_round(self.game, 1)
        total_share = sum(r.market_share for r in results)
        self.assertAlmostEqual(total_share, 1.0, places=5)

    def test_price_competitiveness_affects_occupancy(self):
        Decision.objects.create(
            team=self.teams[0], game=self.game, round_number=1,
            room_rate_standard=300, room_rate_deluxe=500, room_rate_suite=800,
            food_budget=50000, marketing_budget=30000,
            staff_training_budget=20000, renovation_budget=10000,
            service_quality_target=7.0, is_submitted=True,
        )
        Decision.objects.create(
            team=self.teams[1], game=self.game, round_number=1,
            room_rate_standard=700, room_rate_deluxe=1100, room_rate_suite=2000,
            food_budget=50000, marketing_budget=30000,
            staff_training_budget=20000, renovation_budget=10000,
            service_quality_target=7.0, is_submitted=True,
        )

        results = self.engine.calculate_round(self.game, 1)
        low_price_result = results[0]
        high_price_result = results[1]
        self.assertGreater(
            low_price_result.occupancy_rate_standard,
            high_price_result.occupancy_rate_standard
        )

    def test_marketing_budget_affects_occupancy(self):
        Decision.objects.create(
            team=self.teams[0], game=self.game, round_number=1,
            room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
            food_budget=50000, marketing_budget=80000,
            staff_training_budget=20000, renovation_budget=10000,
            service_quality_target=7.0, is_submitted=True,
        )
        Decision.objects.create(
            team=self.teams[1], game=self.game, round_number=1,
            room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
            food_budget=50000, marketing_budget=5000,
            staff_training_budget=20000, renovation_budget=10000,
            service_quality_target=7.0, is_submitted=True,
        )

        results = self.engine.calculate_round(self.game, 1)
        high_marketing = results[0]
        low_marketing = results[1]
        self.assertGreater(
            high_marketing.occupancy_rate_standard,
            low_marketing.occupancy_rate_standard
        )

    def test_cumulative_results_created(self):
        for team in self.teams:
            Decision.objects.create(
                team=team, game=self.game, round_number=1,
                room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                food_budget=50000, marketing_budget=30000,
                staff_training_budget=20000, renovation_budget=10000,
                service_quality_target=7.0, is_submitted=True,
            )

        self.engine.calculate_round(self.game, 1)
        cumulative = CumulativeResult.objects.filter(game=self.game)
        self.assertEqual(cumulative.count(), 3)

    def test_cumulative_results_ranking(self):
        for team in self.teams:
            Decision.objects.create(
                team=team, game=self.game, round_number=1,
                room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                food_budget=50000, marketing_budget=30000,
                staff_training_budget=20000, renovation_budget=10000,
                service_quality_target=7.0, is_submitted=True,
            )

        self.engine.calculate_round(self.game, 1)
        cumulative = list(CumulativeResult.objects.filter(game=self.game).order_by('rank'))
        ranks = [c.rank for c in cumulative]
        self.assertEqual(sorted(ranks), [1, 2, 3])
        for i in range(len(cumulative) - 1):
            self.assertGreaterEqual(
                cumulative[i].final_score,
                cumulative[i + 1].final_score
            )

    def test_multiple_rounds_accumulate(self):
        for rn in [1, 2]:
            for team in self.teams:
                Decision.objects.create(
                    team=team, game=self.game, round_number=rn,
                    room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                    food_budget=50000, marketing_budget=30000,
                    staff_training_budget=20000, renovation_budget=10000,
                    service_quality_target=7.0, is_submitted=True,
                )
            self.engine.calculate_round(self.game, rn)

        cumulative = CumulativeResult.objects.filter(game=self.game)
        self.assertEqual(cumulative.count(), 3)
        for c in cumulative:
            self.assertEqual(c.rounds_played, 2)

    def test_round_result_persists(self):
        for team in self.teams:
            Decision.objects.create(
                team=team, game=self.game, round_number=1,
                room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                food_budget=50000, marketing_budget=30000,
                staff_training_budget=20000, renovation_budget=10000,
                service_quality_target=7.0, is_submitted=True,
            )

        self.engine.calculate_round(self.game, 1)
        round_results = RoundResult.objects.filter(game=self.game, round_number=1)
        self.assertEqual(round_results.count(), 3)

    def test_recalculate_round_replaces_results(self):
        for team in self.teams:
            Decision.objects.create(
                team=team, game=self.game, round_number=1,
                room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                food_budget=50000, marketing_budget=30000,
                staff_training_budget=20000, renovation_budget=10000,
                service_quality_target=7.0, is_submitted=True,
            )

        self.engine.calculate_round(self.game, 1)
        first_count = RoundResult.objects.filter(game=self.game, round_number=1).count()

        self.engine.calculate_round(self.game, 1)
        second_count = RoundResult.objects.filter(game=self.game, round_number=1).count()
        self.assertEqual(first_count, second_count)

    def test_seasonal_factor_affects_results(self):
        for team in self.teams:
            Decision.objects.create(
                team=team, game=self.game, round_number=1,
                room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
                food_budget=50000, marketing_budget=30000,
                staff_training_budget=20000, renovation_budget=10000,
                service_quality_target=7.0, is_submitted=True,
            )

        self.engine.calculate_round(self.game, 1)
        round1_occupancy = RoundResult.objects.get(
            game=self.game, team=self.teams[0], round_number=1
        ).occupancy_rate_standard

        GameParameter.objects.filter(game=self.game, round_number=1).update(seasonal_factor=1.5)
        self.engine.calculate_round(self.game, 1)
        round1_high_season = RoundResult.objects.get(
            game=self.game, team=self.teams[0], round_number=1
        ).occupancy_rate_standard

        self.assertGreater(round1_high_season, round1_occupancy)

    def test_satisfaction_bounds(self):
        Decision.objects.create(
            team=self.teams[0], game=self.game, round_number=1,
            room_rate_standard=500, room_rate_deluxe=800, room_rate_suite=1500,
            food_budget=0, marketing_budget=0,
            staff_training_budget=0, renovation_budget=0,
            service_quality_target=0, is_submitted=True,
        )
        Decision.objects.create(
            team=self.teams[1], game=self.game, round_number=1,
            room_rate_standard=100, room_rate_deluxe=100, room_rate_suite=100,
            food_budget=200000, marketing_budget=200000,
            staff_training_budget=200000, renovation_budget=200000,
            service_quality_target=10, is_submitted=True,
        )

        results = self.engine.calculate_round(self.game, 1)
        for r in results:
            self.assertGreaterEqual(r.customer_satisfaction, 1.0)
            self.assertLessEqual(r.customer_satisfaction, 10.0)


class TestAdvanceRoundAndGameFlow(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.classroom_id, self.team_ids = self._create_classroom_with_teams()
        self.game_id = self._create_game(self.classroom_id, total_rounds=3)
        self._start_game(self.game_id)

    def test_advance_round_creates_results(self):
        for i, team_id in enumerate(self.team_ids):
            self._submit_decision(self.game_id, team_id, self.students[i * 2])

        resp = self._advance_round(self.game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['current_round'], 2)

        round_results = RoundResult.objects.filter(game_id=self.game_id, round_number=1)
        self.assertEqual(round_results.count(), 3)

    def test_advance_round_when_not_running(self):
        self._pause_game(self.game_id)
        resp = self._advance_round(self.game_id)
        self.assertEqual(resp.status_code, 400)

    def test_game_finishes_after_last_round(self):
        for round_num in range(1, 4):
            for i, team_id in enumerate(self.team_ids):
                self._submit_decision(self.game_id, team_id, self.students[i * 2], {
                    'room_rate_standard': 500,
                    'room_rate_deluxe': 800,
                    'room_rate_suite': 1500,
                    'food_budget': 50000,
                    'marketing_budget': 30000,
                    'staff_training_budget': 20000,
                    'renovation_budget': 10000,
                    'service_quality_target': 7.0,
                })
            resp = self._advance_round(self.game_id)
            if round_num < 3:
                self.assertEqual(resp.data['current_round'], round_num + 1)
                self.assertEqual(resp.data['status'], 'running')
            else:
                self.assertEqual(resp.data['status'], 'finished')
                self.assertIsNotNone(resp.data['finished_at'])

    def test_cumulative_results_after_multiple_rounds(self):
        for round_num in range(1, 4):
            for i, team_id in enumerate(self.team_ids):
                self._submit_decision(self.game_id, team_id, self.students[i * 2], {
                    'room_rate_standard': 500 + round_num * 10,
                    'room_rate_deluxe': 800 + round_num * 10,
                    'room_rate_suite': 1500 + round_num * 10,
                    'food_budget': 50000,
                    'marketing_budget': 30000,
                    'staff_training_budget': 20000,
                    'renovation_budget': 10000,
                    'service_quality_target': 7.0,
                })
            self._advance_round(self.game_id)

        cumulative = CumulativeResult.objects.filter(game_id=self.game_id)
        self.assertEqual(cumulative.count(), 3)
        for c in cumulative:
            self.assertEqual(c.rounds_played, 3)
            self.assertGreater(c.total_revenue, 0)
            self.assertGreater(c.total_cost, 0)


class TestDashboardAndResultViewing(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.classroom_id, self.team_ids = self._create_classroom_with_teams()
        self.game_id = self._create_game(self.classroom_id, total_rounds=3)
        self._start_game(self.game_id)

        for i, team_id in enumerate(self.team_ids):
            self._submit_decision(self.game_id, team_id, self.students[i * 2])
        self._advance_round(self.game_id)

    def test_teacher_views_dashboard(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('game', resp.data)
        self.assertIn('current_round_results', resp.data)
        self.assertIn('cumulative_results', resp.data)
        self.assertIn('round_history', resp.data)

    def test_student_views_dashboard(self):
        self._login(self.students[0])
        resp = self.client.get(f'/api/games/{self.game_id}/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('game', resp.data)

    def test_dashboard_current_round_results(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/dashboard/')
        round_history = resp.data['round_history']
        self.assertGreater(len(round_history), 0)
        for r in round_history:
            self.assertIn('revenue_total', r)
            self.assertIn('cost_total', r)
            self.assertIn('profit', r)
            self.assertIn('customer_satisfaction', r)
            self.assertIn('market_share', r)
            self.assertIn('score', r)

    def test_dashboard_cumulative_results(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/dashboard/')
        cumulative = resp.data['cumulative_results']
        self.assertGreater(len(cumulative), 0)
        for c in cumulative:
            self.assertIn('rounds_played', c)
            self.assertIn('total_revenue', c)
            self.assertIn('total_cost', c)
            self.assertIn('total_profit', c)
            self.assertIn('final_score', c)
            self.assertIn('rank', c)

    def test_ranking_view(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/ranking/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)

        ranks = [r['rank'] for r in resp.data]
        self.assertEqual(sorted(ranks), [1, 2, 3])

        for i in range(len(resp.data) - 1):
            self.assertGreaterEqual(
                resp.data[i]['final_score'],
                resp.data[i + 1]['final_score']
            )

    def test_round_result_view(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/results/1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)

        for r in resp.data:
            self.assertIn('occupancy_rate_standard', r)
            self.assertIn('occupancy_rate_deluxe', r)
            self.assertIn('occupancy_rate_suite', r)
            self.assertIn('revenue_room', r)
            self.assertIn('revenue_food', r)
            self.assertIn('revenue_total', r)
            self.assertIn('cost_operation', r)
            self.assertIn('cost_marketing', r)
            self.assertIn('cost_staff', r)
            self.assertIn('cost_renovation', r)
            self.assertIn('cost_total', r)
            self.assertIn('profit', r)
            self.assertIn('customer_satisfaction', r)
            self.assertIn('market_share', r)
            self.assertIn('score', r)

    def test_team_trend_view(self):
        self._login(self.teacher)
        team_id = self.team_ids[0]
        resp = self.client.get(f'/api/games/{self.game_id}/trend/{team_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_ranking_nonexistent_game(self):
        self._login(self.teacher)
        resp = self.client.get('/api/games/99999/ranking/')
        self.assertEqual(resp.status_code, 404)

    def test_round_result_nonexistent_game(self):
        self._login(self.teacher)
        resp = self.client.get('/api/games/99999/results/1/')
        self.assertEqual(resp.status_code, 404)


class TestFullSimulationFlow(BaseTestCase):
    def test_complete_hotel_simulation_lifecycle(self):
        self._login(self.teacher)

        # === Phase 1: Teacher creates classroom ===
        resp = self.client.post('/api/classrooms/', {'name': '2024级酒店管理班', 'description': '期末模拟实训'})
        self.assertEqual(resp.status_code, 201)
        classroom_id = resp.data['id']

        # === Phase 2: Teacher creates teams and assigns students ===
        team_ids = []
        team_configs = [
            ('星际酒店集团', [0, 1]),
            ('皇冠酒店集团', [2, 3]),
            ('翡翠酒店集团', [4, 5]),
        ]
        for team_name, student_indices in team_configs:
            resp = self.client.post(f'/api/classrooms/{classroom_id}/teams/', {'name': team_name, 'class_room': classroom_id})
            self.assertEqual(resp.status_code, 201)
            tid = resp.data['id']
            team_ids.append(tid)
            member_ids = [self.students[i].id for i in student_indices]
            resp = self.client.post(
                f'/api/classrooms/{classroom_id}/teams/{tid}/add-members/',
                {'user_ids': member_ids},
                content_type='application/json'
            )
            self.assertEqual(resp.status_code, 200)

        # === Phase 3: Teacher creates game ===
        resp = self.client.post('/api/games/', {
            'name': '酒店经营模拟-期末实训',
            'class_room': classroom_id,
            'total_rounds': 3,
            'description': '综合模拟实训考核'
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 201)
        game_id = resp.data['id']

        # === Phase 4: Verify game parameters generated ===
        resp = self.client.get(f'/api/games/{game_id}/parameters/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 4)

        # === Phase 5: Teacher starts game ===
        resp = self.client.post(f'/api/games/{game_id}/start/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'running')
        self.assertEqual(resp.data['current_round'], 1)

        # === Phase 6: Round 1 - Students submit decisions ===
        strategies = [
            {
                'room_rate_standard': 480, 'room_rate_deluxe': 780, 'room_rate_suite': 1400,
                'food_budget': 60000, 'marketing_budget': 40000,
                'staff_training_budget': 25000, 'renovation_budget': 15000,
                'service_quality_target': 8.0,
            },
            {
                'room_rate_standard': 520, 'room_rate_deluxe': 850, 'room_rate_suite': 1600,
                'food_budget': 45000, 'marketing_budget': 35000,
                'staff_training_budget': 20000, 'renovation_budget': 20000,
                'service_quality_target': 7.5,
            },
            {
                'room_rate_standard': 500, 'room_rate_deluxe': 800, 'room_rate_suite': 1500,
                'food_budget': 55000, 'marketing_budget': 30000,
                'staff_training_budget': 22000, 'renovation_budget': 12000,
                'service_quality_target': 7.0,
            },
        ]
        for i, (team_id, strategy) in enumerate(zip(team_ids, strategies)):
            self._submit_decision(game_id, team_id, self.students[i * 2], strategy)

        # === Phase 7: Teacher advances round ===
        resp = self._advance_round(game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['current_round'], 2)

        # === Phase 8: Teacher views Round 1 results ===
        resp = self.client.get(f'/api/games/{game_id}/results/1/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)
        r1_scores = {r['team_name']: r['score'] for r in resp.data}

        # === Phase 9: Round 2 - Different strategies ===
        r2_strategies = [
            {
                'room_rate_standard': 460, 'room_rate_deluxe': 750, 'room_rate_suite': 1350,
                'food_budget': 65000, 'marketing_budget': 45000,
                'staff_training_budget': 28000, 'renovation_budget': 18000,
                'service_quality_target': 8.5,
            },
            {
                'room_rate_standard': 540, 'room_rate_deluxe': 900, 'room_rate_suite': 1700,
                'food_budget': 40000, 'marketing_budget': 30000,
                'staff_training_budget': 15000, 'renovation_budget': 25000,
                'service_quality_target': 7.0,
            },
            {
                'room_rate_standard': 510, 'room_rate_deluxe': 820, 'room_rate_suite': 1550,
                'food_budget': 50000, 'marketing_budget': 35000,
                'staff_training_budget': 24000, 'renovation_budget': 14000,
                'service_quality_target': 7.5,
            },
        ]
        for i, (team_id, strategy) in enumerate(zip(team_ids, r2_strategies)):
            self._submit_decision(game_id, team_id, self.students[i * 2], strategy)

        resp = self._advance_round(game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['current_round'], 3)

        # === Phase 10: Round 3 - Final round ===
        r3_strategies = [
            {
                'room_rate_standard': 450, 'room_rate_deluxe': 720, 'room_rate_suite': 1300,
                'food_budget': 70000, 'marketing_budget': 50000,
                'staff_training_budget': 30000, 'renovation_budget': 20000,
                'service_quality_target': 9.0,
            },
            {
                'room_rate_standard': 500, 'room_rate_deluxe': 820, 'room_rate_suite': 1550,
                'food_budget': 50000, 'marketing_budget': 40000,
                'staff_training_budget': 25000, 'renovation_budget': 18000,
                'service_quality_target': 8.0,
            },
            {
                'room_rate_standard': 520, 'room_rate_deluxe': 850, 'room_rate_suite': 1600,
                'food_budget': 48000, 'marketing_budget': 38000,
                'staff_training_budget': 23000, 'renovation_budget': 16000,
                'service_quality_target': 7.8,
            },
        ]
        for i, (team_id, strategy) in enumerate(zip(team_ids, r3_strategies)):
            self._submit_decision(game_id, team_id, self.students[i * 2], strategy)

        resp = self._advance_round(game_id)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'finished')
        self.assertIsNotNone(resp.data['finished_at'])

        # === Phase 11: Verify complete round results ===
        for rn in range(1, 4):
            resp = self.client.get(f'/api/games/{game_id}/results/{rn}/')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.data), 3)

        # === Phase 12: Teacher views ranking (cumulative results) ===
        resp = self.client.get(f'/api/games/{game_id}/ranking/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 3)

        ranks = [r['rank'] for r in resp.data]
        self.assertEqual(sorted(ranks), [1, 2, 3])

        for r in resp.data:
            self.assertEqual(r['rounds_played'], 3)
            self.assertGreater(r['total_revenue'], 0)
            self.assertGreater(r['total_cost'], 0)

        # === Phase 13: Teacher views dashboard ===
        resp = self.client.get(f'/api/games/{game_id}/dashboard/')
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(len(resp.data['round_history']), 9)
        self.assertEqual(len(resp.data['cumulative_results']), 3)

        cumulative = resp.data['cumulative_results']
        cumulative_sorted = sorted(cumulative, key=lambda x: x['rank'])
        self.assertEqual(cumulative_sorted[0]['rank'], 1)
        self.assertGreaterEqual(
            cumulative_sorted[0]['final_score'],
            cumulative_sorted[1]['final_score']
        )

        # === Phase 14: Team trend view ===
        for team_id in team_ids:
            resp = self.client.get(f'/api/games/{game_id}/trend/{team_id}/')
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(resp.data), 3)

        # === Phase 15: Verify game state is finished ===
        resp = self.client.get(f'/api/games/{game_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['status'], 'finished')

        # === Phase 16: Verify data completeness ===
        total_round_results = RoundResult.objects.filter(game_id=game_id).count()
        self.assertEqual(total_round_results, 9)

        total_cumulative = CumulativeResult.objects.filter(game_id=game_id).count()
        self.assertEqual(total_cumulative, 3)

        total_decisions = Decision.objects.filter(game_id=game_id).count()
        self.assertEqual(total_decisions, 9)

        # === Phase 17: Student can still view results ===
        self._login(self.students[0])
        resp = self.client.get(f'/api/games/{game_id}/dashboard/')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(f'/api/games/{game_id}/ranking/')
        self.assertEqual(resp.status_code, 200)

        resp = self.client.get(f'/api/games/{game_id}/trend/{team_ids[0]}/')
        self.assertEqual(resp.status_code, 200)


class TestGameListAndFiltering(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.classroom_id, self.team_ids = self._create_classroom_with_teams()

    def test_teacher_sees_all_games_in_classroom(self):
        self._create_game(self.classroom_id)
        self._create_game(self.classroom_id)

        self._login(self.teacher)
        resp = self.client.get(f'/api/games/?class_room={self.classroom_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)

    def test_student_sees_only_games_with_their_team(self):
        self._create_game(self.classroom_id)

        self._login(self.students[0])
        resp = self.client.get('/api/games/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_student_not_in_team_sees_no_games(self):
        extra_student = User.objects.create_user(
            username='lonely_student', password='testpass123',
            role='student', email='lonely@test.com'
        )
        self._create_game(self.classroom_id)

        self._login(extra_student)
        resp = self.client.get('/api/games/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 0)


class TestEdgeCasesAndErrorHandling(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.classroom_id, self.team_ids = self._create_classroom_with_teams()
        self.game_id = self._create_game(self.classroom_id, total_rounds=2)
        self._start_game(self.game_id)

    def test_advance_round_without_decisions(self):
        resp = self._advance_round(self.game_id)
        self.assertEqual(resp.status_code, 200)
        round_results = RoundResult.objects.filter(game_id=self.game_id, round_number=1)
        self.assertEqual(round_results.count(), 0)

    def test_advance_round_with_partial_decisions(self):
        self._submit_decision(self.game_id, self.team_ids[0], self.students[0])

        resp = self._advance_round(self.game_id)
        self.assertEqual(resp.status_code, 200)

        round_results = RoundResult.objects.filter(game_id=self.game_id, round_number=1)
        self.assertEqual(round_results.count(), 1)

    def test_nonexistent_game_returns_404(self):
        self._login(self.teacher)
        resp = self.client.get('/api/games/99999/')
        self.assertEqual(resp.status_code, 404)

    def test_nonexistent_classroom_returns_404(self):
        self._login(self.teacher)
        resp = self.client.get('/api/classrooms/99999/')
        self.assertEqual(resp.status_code, 404)

    def test_delete_game(self):
        self._login(self.teacher)
        resp = self.client.delete(f'/api/games/{self.game_id}/')
        self.assertEqual(resp.status_code, 204)

        resp = self.client.get(f'/api/games/{self.game_id}/')
        self.assertEqual(resp.status_code, 404)

    def test_update_game_info(self):
        self._login(self.teacher)
        resp = self.client.put(
            f'/api/games/{self.game_id}/',
            {'name': '更新后的模拟', 'description': '更新描述'},
            content_type='application/json'
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data['name'], '更新后的模拟')

    def test_student_cannot_delete_game(self):
        self._login(self.students[0])
        resp = self.client.delete(f'/api/games/{self.game_id}/')
        self.assertEqual(resp.status_code, 403)

    def test_game_detail_shows_parameters(self):
        self._login(self.teacher)
        resp = self.client.get(f'/api/games/{self.game_id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('parameters', resp.data)
        self.assertGreater(len(resp.data['parameters']), 0)

    def test_decision_for_nonexistent_game(self):
        self._login(self.students[0])
        resp = self.client.post('/api/games/99999/decisions/', {
            'team': self.team_ids[0],
            'room_rate_standard': 500,
            'room_rate_deluxe': 800,
            'room_rate_suite': 1500,
            'food_budget': 50000,
            'marketing_budget': 30000,
            'staff_training_budget': 20000,
            'renovation_budget': 10000,
            'service_quality_target': 7.0,
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 404)

    def test_decision_for_nonexistent_team(self):
        self._login(self.students[0])
        resp = self.client.post(f'/api/games/{self.game_id}/decisions/', {
            'team': 99999,
            'room_rate_standard': 500,
            'room_rate_deluxe': 800,
            'room_rate_suite': 1500,
            'food_budget': 50000,
            'marketing_budget': 30000,
            'staff_training_budget': 20000,
            'renovation_budget': 10000,
            'service_quality_target': 7.0,
        }, content_type='application/json')
        self.assertEqual(resp.status_code, 404)
