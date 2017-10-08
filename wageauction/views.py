from otree.api import Currency as c, currency_range
from . import models
from ._builtin import Page, WaitPage
from .models import Constants, Group, Subsession, JobContract
import time
from random import randint
from channels import Group as ChannelGroup


class EmployerPage(Page):
    def is_displayed(self):
        return self.player.role() == 'employer' and self.extra_is_displayed()

    def extra_is_displayed(self):
        return True


class WorkerPage(Page):
    def is_displayed(self):
        return self.player.role() == 'worker' and self.extra_is_displayed()

    def extra_is_displayed(self):
        return True


class ActiveWorkerPage(Page):
    def is_displayed(self):
        closed_contract = self.player.work_to_do.filter(accepted=True).exists()
        return self.player.role() == 'worker' and self.extra_is_displayed() and closed_contract

    def extra_is_displayed(self):
        return True


class WP(WaitPage):
    def after_all_players_arrive(self):
        now = time.time()
        self.group.auctionenddate = now + Constants.starting_time


class Auction(EmployerPage):
    def extra_is_displayed(self):
        closed_contract = self.player.contract.filter(accepted=True).exists()
        return not any([self.group.day_over, closed_contract])

    def vars_for_template(self):
        active_contracts = JobContract.objects.filter(accepted=False, employer__group=self.group)
        return {'time_left': self.group.time_left(),
                'active_contracts': active_contracts,
                }


class Accept(WorkerPage):
    def extra_is_displayed(self):
        closed_contract = self.player.work_to_do.filter(accepted=True).exists()
        return not any([self.group.day_over, closed_contract])

    def vars_for_template(self):
        active_contracts = JobContract.objects.filter(accepted=False, employer__group=self.group).values('pk', 'amount')
        return {'time_left': self.group.time_left(),
                'active_contracts': active_contracts}


class AfterAuctionDecision(EmployerPage):
    form_model = models.Player
    form_fields = ["wage_adjustment"]

    def extra_is_displayed(self):
        closed_contract = self.player.contract.filter(accepted=True).exists()
        return closed_contract

    def before_next_page(self):
        closed_contract = self.player.contract.get(accepted=True)
        closed_contract.amount_updated = self.player.wage_adjustment


class AuctionResultsEmployer(EmployerPage):
    ...


class AuctionResultsWorker(ActiveWorkerPage):
    ...


class Start(ActiveWorkerPage):
    ...


class WorkPage(ActiveWorkerPage):
    timer_text = 'Time left to complete this section:'

    timeout_seconds = 300

    def vars_for_template(self):
        x = randint(50, 100)
        y = randint(50, 100)
        listx = [randint(10, x)]
        listy = [randint(10, y)]
        for i in range(0, 99):
            listx.append(randint(10, x))
            listy.append(randint(10, y))
        answer = max(listx) + max(listy)

        return {
            "mat1": listx,
            "mat2": listy,
            "correct_answer": answer,
        }

    def before_next_page(self):
        ...


class WaitP(WaitPage):
    def after_all_players_arrive(self):
        self.group.set_payoffs()


class Results(Page):
    ...


page_sequence = [
    WP,
    Auction, Accept,
    AfterAuctionDecision,
    AuctionResultsEmployer, AuctionResultsWorker,
    Start,
    WorkPage
    WaitP,
    Results
]
