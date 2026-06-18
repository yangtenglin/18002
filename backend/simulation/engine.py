from django.db.models import Sum, Count, Avg
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
        decisions_qs = Decision.objects.filter(
            game_id=game.pk, round_number=round_number, is_submitted=True
        ).select_related('team')
        all_decisions = list(decisions_qs)
        if not all_decisions:
            return []

        param = self._get_parameters(game, round_number)
        total_teams = game.class_room.teams.count()
        results = []

        n = len(all_decisions)
        avg_standard_rate = sum(d.room_rate_standard for d in all_decisions) / n
        avg_deluxe_rate = sum(d.room_rate_deluxe for d in all_decisions) / n
        avg_suite_rate = sum(d.room_rate_suite for d in all_decisions) / n

        for decision in all_decisions:
            result = self._calculate_team_result(
                decision, param, total_teams, round_number,
                avg_standard_rate, avg_deluxe_rate, avg_suite_rate
            )
            results.append(result)

        self._calculate_market_shares(results, total_teams)
        self._calculate_scores(results)

        RoundResult.objects.filter(game_id=game.pk, round_number=round_number).delete()
        RoundResult.objects.bulk_create(results, batch_size=200)

        self._update_cumulative_results_optimized(game)

        return results

    def _get_parameters(self, game, round_number):
        params = list(GameParameter.objects.filter(
            game_id=game.pk, round_number__in=[round_number, 0]
        ))
        for p in params:
            if p.round_number == round_number:
                return p
        for p in params:
            if p.round_number == 0:
                return p
        return GameParameter(game_id=game.pk, round_number=round_number)

    def _calculate_team_result(self, decision, param, total_teams, round_number,
                                avg_standard_rate, avg_deluxe_rate, avg_suite_rate):
        result = RoundResult(
            team_id=decision.team_id,
            game_id=decision.game_id,
            round_number=round_number,
        )

        result.occupancy_rate_standard = self._calc_occupancy(
            decision.room_rate_standard, avg_standard_rate, param, decision.marketing_budget
        )
        result.occupancy_rate_deluxe = self._calc_occupancy(
            decision.room_rate_deluxe, avg_deluxe_rate, param, decision.marketing_budget
        )
        result.occupancy_rate_suite = self._calc_occupancy(
            decision.room_rate_suite, avg_suite_rate, param, decision.marketing_budget
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

        result.customer_satisfaction = self._calc_satisfaction(
            decision, avg_standard_rate, avg_deluxe_rate, avg_suite_rate
        )
        result.customer_satisfaction = min(max(result.customer_satisfaction, 1.0), 10.0)

        return result

    def _calc_occupancy(self, rate, avg_rate, param, marketing_budget):
        price_competitiveness = avg_rate / max(rate, 1)
        occupancy = self.BASE_OCCUPANCY * price_competitiveness
        occupancy *= param.seasonal_factor * param.economic_factor
        marketing_effect = min(marketing_budget / 50000, 1.5) * 0.15
        occupancy += marketing_effect
        competition_effect = (1 - param.competition_intensity) * 0.1
        occupancy += competition_effect
        return occupancy

    def _calc_satisfaction(self, decision, avg_standard, avg_deluxe, avg_suite):
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

    def _calculate_market_shares(self, results, total_teams):
        total_revenue = sum(r.revenue_total for r in results)
        if total_revenue > 0:
            inv = 1.0 / total_revenue
            for r in results:
                r.market_share = r.revenue_total * inv
        else:
            share = 1.0 / total_teams
            for r in results:
                r.market_share = share

    def _calculate_scores(self, results):
        if not results:
            return

        max_profit = max((r.profit for r in results), default=0) or 1
        max_revenue = max((r.revenue_total for r in results), default=0) or 1
        max_satisfaction = max((r.customer_satisfaction for r in results), default=0) or 1

        profit_coef = 40 / max_profit if max_profit > 0 else 0
        revenue_coef = 25 / max_revenue if max_revenue > 0 else 0
        sat_coef = 20 / max_satisfaction if max_satisfaction > 0 else 0

        for r in results:
            profit_score = r.profit * profit_coef if max_profit > 0 else 0
            revenue_score = r.revenue_total * revenue_coef if max_revenue > 0 else 0
            satisfaction_score = r.customer_satisfaction * sat_coef if max_satisfaction > 0 else 0
            market_score = r.market_share * 100 * 0.15
            r.score = max(profit_score + revenue_score + satisfaction_score + market_score, 0)

    def _update_cumulative_results_optimized(self, game):
        from django.db.models import Sum as DbSum, Count as DbCount, Avg as DbAvg

        all_rounds = RoundResult.objects.filter(game_id=game.pk)

        aggregates = all_rounds.values('team_id').annotate(
            rounds_played=DbCount('id'),
            total_revenue=DbSum('revenue_total'),
            total_cost=DbSum('cost_total'),
            total_profit=DbSum('profit'),
            avg_satisfaction=DbAvg('customer_satisfaction'),
            avg_market_share=DbAvg('market_share'),
            round_score_sum=DbSum('score'),
        )

        agg_by_team = {row['team_id']: row for row in aggregates}

        existing_cumulative = CumulativeResult.objects.filter(game_id=game.pk)
        existing_by_team = {cr.team_id: cr for cr in existing_cumulative}

        to_create = []
        to_update = []

        for team_id, row in agg_by_team.items():
            rp = row['rounds_played']
            if rp == 0:
                continue
            total_rev = row['total_revenue'] or 0
            total_prof = row['total_profit'] or 0
            score_sum = row['round_score_sum'] or 0
            final_score = (score_sum / rp) * (1 + total_prof / max(total_rev, 1))

            data = {
                'rounds_played': rp,
                'total_revenue': total_rev,
                'total_cost': row['total_cost'] or 0,
                'total_profit': total_prof,
                'avg_satisfaction': row['avg_satisfaction'] or 0,
                'avg_market_share': row['avg_market_share'] or 0,
                'final_score': final_score,
            }

            if team_id in existing_by_team:
                cr = existing_by_team[team_id]
                for k, v in data.items():
                    setattr(cr, k, v)
                to_update.append(cr)
            else:
                to_create.append(CumulativeResult(
                    game_id=game.pk, team_id=team_id, **data
                ))

        if to_create:
            CumulativeResult.objects.bulk_create(to_create, batch_size=200)
        if to_update:
            CumulativeResult.objects.bulk_update(
                to_update,
                fields=['rounds_played', 'total_revenue', 'total_cost',
                        'total_profit', 'avg_satisfaction', 'avg_market_share',
                        'final_score'],
                batch_size=200,
            )

        ranked = list(
            CumulativeResult.objects.filter(game_id=game.pk)
            .only('id', 'final_score')
            .order_by('-final_score')
        )
        for idx, cr in enumerate(ranked, 1):
            cr.rank = idx
        if ranked:
            CumulativeResult.objects.bulk_update(ranked, fields=['rank'], batch_size=200)
