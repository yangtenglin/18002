import math
from dashboard.models import RoundResult, CumulativeResult
from decisions.models import Decision
from simulation.models import GameParameter


class SimulationEngine:
    ROOMS_STANDARD = 60
    ROOMS_DELUXE = 30
    ROOMS_SUITE = 10
    BASE_OCCUPANCY = 0.65
    BASE_FOOD_REVENUE_RATIO = 0.25
    BASE_OPERATION_COST_PER_ROOM = 150
    BASE_SATISFACTION = 6.5
    SATISFACTION_WEIGHT_SERVICE = 0.3
    SATISFACTION_WEIGHT_RENOVATION = 0.2
    SATISFACTION_WEIGHT_PRICE = 0.3
    SATISFACTION_WEIGHT_FOOD = 0.2

    def calculate_round(self, game, round_number):
        decisions = Decision.objects.filter(
            game=game, round_number=round_number, is_submitted=True
        )
        if not decisions.exists():
            return []

        param = self._get_parameters(game, round_number)
        total_teams = game.class_room.teams.count()
        results = []

        all_decisions = list(decisions)
        avg_standard_rate = sum(d.room_rate_standard for d in all_decisions) / len(all_decisions) if all_decisions else 500
        avg_deluxe_rate = sum(d.room_rate_deluxe for d in all_decisions) / len(all_decisions) if all_decisions else 800
        avg_suite_rate = sum(d.room_rate_suite for d in all_decisions) / len(all_decisions) if all_decisions else 1500

        for decision in all_decisions:
            result = self._calculate_team_result(
                decision, param, total_teams, round_number,
                avg_standard_rate, avg_deluxe_rate, avg_suite_rate
            )
            results.append(result)

        self._calculate_market_shares(results, total_teams, param)
        self._calculate_scores(results, game.current_round)

        RoundResult.objects.filter(game=game, round_number=round_number).delete()
        RoundResult.objects.bulk_create(results)

        self._update_cumulative_results(game)

        return results

    def _get_parameters(self, game, round_number):
        param = GameParameter.objects.filter(game=game, round_number=round_number).first()
        if not param:
            param = GameParameter.objects.filter(game=game, round_number=0).first()
        if not param:
            param = GameParameter(game=game, round_number=round_number)
        return param

    def _calculate_team_result(self, decision, param, total_teams, round_number,
                                avg_standard_rate, avg_deluxe_rate, avg_suite_rate):
        result = RoundResult(
            team_id=decision.team_id,
            game_id=decision.game_id,
            round_number=round_number,
        )

        result.occupancy_rate_standard = self._calc_occupancy(
            decision.room_rate_standard, avg_standard_rate, param,
            decision.marketing_budget, total_teams, self.ROOMS_STANDARD
        )
        result.occupancy_rate_deluxe = self._calc_occupancy(
            decision.room_rate_deluxe, avg_deluxe_rate, param,
            decision.marketing_budget, total_teams, self.ROOMS_DELUXE
        )
        result.occupancy_rate_suite = self._calc_occupancy(
            decision.room_rate_suite, avg_suite_rate, param,
            decision.marketing_budget, total_teams, self.ROOMS_SUITE
        )

        result.occupancy_rate_standard = min(max(result.occupancy_rate_standard, 0.05), 0.98)
        result.occupancy_rate_deluxe = min(max(result.occupancy_rate_deluxe, 0.05), 0.98)
        result.occupancy_rate_suite = min(max(result.occupancy_rate_suite, 0.05), 0.98)

        standard_revenue = self.ROOMS_STANDARD * result.occupancy_rate_standard * 30 * decision.room_rate_standard
        deluxe_revenue = self.ROOMS_DELUXE * result.occupancy_rate_deluxe * 30 * decision.room_rate_deluxe
        suite_revenue = self.ROOMS_SUITE * result.occupancy_rate_suite * 30 * decision.room_rate_suite
        result.revenue_room = standard_revenue + deluxe_revenue + suite_revenue

        food_quality_factor = min(decision.food_budget / 50000, 2.0) if decision.food_budget > 0 else 0.3
        total_rooms_occupied = (
            self.ROOMS_STANDARD * result.occupancy_rate_standard +
            self.ROOMS_DELUXE * result.occupancy_rate_deluxe +
            self.ROOMS_SUITE * result.occupancy_rate_suite
        )
        result.revenue_food = total_rooms_occupied * 30 * 200 * food_quality_factor * self.BASE_FOOD_REVENUE_RATIO
        result.revenue_total = result.revenue_room + result.revenue_food

        total_rooms = self.ROOMS_STANDARD + self.ROOMS_DELUXE + self.ROOMS_SUITE
        inflation = (1 + param.cost_inflation_rate) ** round_number
        result.cost_operation = total_rooms * self.BASE_OPERATION_COST_PER_ROOM * 30 * inflation
        result.cost_marketing = decision.marketing_budget
        result.cost_staff = decision.staff_training_budget
        result.cost_renovation = decision.renovation_budget
        result.cost_total = result.cost_operation + result.cost_marketing + result.cost_staff + result.cost_renovation

        result.profit = result.revenue_total - result.cost_total

        result.customer_satisfaction = self._calc_satisfaction(decision, param, avg_standard_rate, avg_deluxe_rate, avg_suite_rate)
        result.customer_satisfaction = min(max(result.customer_satisfaction, 1.0), 10.0)

        return result

    def _calc_occupancy(self, rate, avg_rate, param, marketing_budget, total_teams, room_count):
        price_competitiveness = avg_rate / max(rate, 1)
        occupancy = self.BASE_OCCUPANCY * price_competitiveness
        occupancy *= param.seasonal_factor * param.economic_factor
        marketing_effect = min(marketing_budget / 50000, 1.5) * 0.15
        occupancy += marketing_effect
        competition_effect = (1 - param.competition_intensity) * 0.1
        occupancy += competition_effect
        return occupancy

    def _calc_satisfaction(self, decision, param, avg_standard, avg_deluxe, avg_suite):
        service_score = min(decision.service_quality_target / 10, 1.0) * 3
        renovation_effect = min(decision.renovation_budget / 50000, 1.5) * 2
        avg_rate = (decision.room_rate_standard + decision.room_rate_deluxe + decision.room_rate_suite) / 3
        market_avg = (avg_standard + avg_deluxe + avg_suite) / 3
        price_satisfaction = (market_avg / max(avg_rate, 1)) * 3
        food_effect = min(decision.food_budget / 50000, 1.5) * 2
        satisfaction = (
            self.SATISFACTION_WEIGHT_SERVICE * service_score +
            self.SATISFACTION_WEIGHT_RENOVATION * renovation_effect +
            self.SATISFACTION_WEIGHT_PRICE * price_satisfaction +
            self.SATISFACTION_WEIGHT_FOOD * food_effect
        )
        return satisfaction * 10 / 3

    def _calculate_market_shares(self, results, total_teams, param):
        total_revenue = sum(r.revenue_total for r in results)
        if total_revenue > 0:
            for r in results:
                r.market_share = r.revenue_total / total_revenue
        else:
            for r in results:
                r.market_share = 1.0 / total_teams

    def _calculate_scores(self, results, current_round):
        if not results:
            return

        max_profit = max(r.profit for r in results) or 1
        max_revenue = max(r.revenue_total for r in results) or 1
        max_satisfaction = max(r.customer_satisfaction for r in results) or 1

        for r in results:
            profit_score = (r.profit / max_profit) * 40 if max_profit > 0 else 0
            revenue_score = (r.revenue_total / max_revenue) * 25 if max_revenue > 0 else 0
            satisfaction_score = (r.customer_satisfaction / max_satisfaction) * 20 if max_satisfaction > 0 else 0
            market_score = r.market_share * 100 * 0.15
            r.score = max(profit_score + revenue_score + satisfaction_score + market_score, 0)

    def _update_cumulative_results(self, game):
        teams = game.class_room.teams.all()
        for team in teams:
            round_results = RoundResult.objects.filter(game=game, team=team)
            if not round_results.exists():
                continue

            rounds_played = round_results.count()
            total_revenue = sum(r.revenue_total for r in round_results)
            total_cost = sum(r.cost_total for r in round_results)
            total_profit = sum(r.profit for r in round_results)
            avg_satisfaction = sum(r.customer_satisfaction for r in round_results) / rounds_played
            avg_market_share = sum(r.market_share for r in round_results) / rounds_played

            round_score_sum = sum(r.score for r in round_results)
            final_score = round_score_sum / rounds_played * (1 + total_profit / max(total_revenue, 1))

            CumulativeResult.objects.update_or_create(
                team=team, game=game,
                defaults={
                    'rounds_played': rounds_played,
                    'total_revenue': total_revenue,
                    'total_cost': total_cost,
                    'total_profit': total_profit,
                    'avg_satisfaction': avg_satisfaction,
                    'avg_market_share': avg_market_share,
                    'final_score': final_score,
                }
            )

        all_cumulative = CumulativeResult.objects.filter(game=game).order_by('-final_score')
        for idx, cr in enumerate(all_cumulative, 1):
            cr.rank = idx
            cr.save(update_fields=['rank'])
