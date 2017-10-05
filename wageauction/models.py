from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
from django import forms
import time
import datetime

from django.db import models as djmodels

author = 'Essi Kujansuu, EUI, essi.kujansuu@eui.eu, adapting work of Philipp Chapkovski, UZH, chapkovski@gmail.com'

doc = """
Adaptation of Fehr et al. 1993 auction.
"""


class Constants(BaseConstants):
    name_in_url = 'wageauction'
    players_per_group = 5
    num_rounds = 2
    starting_time = 1500
    num_employers = 2
    num_workers = players_per_group - num_employers
    task_time = 300


class Subsession(BaseSubsession):
    def creating_session(self):
        for g in self.get_groups():
            g.matched1 = 0
            g.matched2 = 0
            g.matched3 = 0
            g.matched4 = 0
            g.matched5 = 0
            g.standing1 = 0
            g.standing2 = 0
            g.standing3 = 0
            g.standing4 = 0
            g.standing5 = 0

        tax_outcome = random.randint(1, 3)
        for p in self.get_players():
            p.tasks_attempted = 0
            p.tasks_correct = 0
            # potentially change the tax_outcome to a group outcome common to all in the experiment (room).
            p.tax_outcome = tax_outcome


class Group(BaseGroup):
    auctionenddate = models.FloatField()

    matched1 = models.IntegerField()
    matched2 = models.IntegerField()
    matched3 = models.IntegerField()
    matched4 = models.IntegerField()
    matched5 = models.IntegerField()

    standing1 = models.IntegerField()
    standing2 = models.IntegerField()
    standing3 = models.IntegerField()
    standing4 = models.IntegerField()
    standing5 = models.IntegerField()

    def time_left(self):
        now = time.time()
        time_left = self.auctionenddate - now
        time_left = round(time_left) if time_left > 0 else 0
        return time_left

    def set_payoffs(self):
        for person in self.get_players():
            if person.role() == 'employer':
                if person.partner_id == 0:
                    person.payoff = 0
                else:
                    if person.tax_outcome == 2:
                        person.payoff = 40 - (
                        person.wage_offer + person.wage_adjustment) + 0.8 * 20 * person.tasks_correct
                    else:
                        person.payoff = 40 - (person.wage_offer + person.wage_adjustment) + 20 * person.tasks_correct
            if person.role() == 'worker':
                if person.partner_id == 0:
                    person.payoff = 20
                else:
                    if person.tax_outcome == 3:
                        person.payoff = 0.8 * (person.wage_offer + person.wage_adjustment)
                    else:
                        person.payoff = (person.wage_offer + person.wage_adjustment)


class Player(BasePlayer):
    wage_offer = models.IntegerField()
    partner_id = models.IntegerField()
    tax_outcome = models.PositiveIntegerField()
    wage_adjustment = models.IntegerField()
    tasks_attempted = models.PositiveIntegerField()
    tasks_correct = models.PositiveIntegerField()
    partner_payoff = models.CurrencyField()

    def role(self):
        if self.participant.id_in_session < Constants.num_employers + 1:
            return 'employer'
        if self.participant.id_in_session > Constants.num_employers:
            return 'worker'


class Request(djmodels.Model):
    employer = djmodels.ForeignKey(Player, related_name='requests')
    amount = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class JobContract(djmodels.Model):
    employer = djmodels.ForeignKey(Player, related_name='contract', unique=True)
    worker = djmodels.ForeignKey(Player, blank=True, null=True, related_name='work_to_do')
    amount = models.IntegerField()
    accepted = models.BooleanField()
    amount_updated = models.IntegerField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)