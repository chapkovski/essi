from channels import Group
from channels.sessions import channel_session
from .models import Group as OtreeGroup, Request, JobContract, Player, Constants
import json
import time
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder


def ws_connect(message, group_name):
    Group(group_name).add(message.reply_channel)

def get_contracts(group):
    contracts = {}
    active_contracts = list(
        JobContract.objects.filter(accepted=False, employer__group=group).values('pk', 'amount'))
    active_contracts = json.dumps(active_contracts, cls=DjangoJSONEncoder)
    closed_contracts = list(
        JobContract.objects.filter(accepted=True, employer__group=group).values())
    closed_contracts = json.dumps(closed_contracts, cls=DjangoJSONEncoder)
    contracts['active_contracts'] = active_contracts
    contracts['closed_contracts'] = closed_contracts
    return contracts

def process_employer_request(jsonmessage, group):
    print('message from employer')
    employer = Player.objects.get(pk=jsonmessage['player_pk'])
    wage_offer = jsonmessage['wage_offer']
    employer.requests.create(amount=wage_offer)
    contract, created = employer.contract.get_or_create(defaults={'amount': wage_offer,
                                                                  'accepted': False, })
    if not created:
        contract.amount = wage_offer
        contract.save()




def process_worker_request(jsonmessage, respondent, group):
    worker = Player.objects.get(pk=jsonmessage['player_pk'])
    contract = JobContract.objects.get(pk=jsonmessage['contract_to_accept']);
    response = {}
    if contract.accepted:
        response['already_taken'] = True
    else:
        contract.worker = worker
        contract.accepted = True
        contract.save()
        response['already_taken'] = False
    response.update(get_contracts(group))
    respondent.send({'text': json.dumps(response)})


def ws_message(message, group_name):
    group_id = group_name[5:]
    jsonmessage = json.loads(message.content['text'])
    group = OtreeGroup.objects.get(id=group_id)

    # Messages from employers: wage offers
    if jsonmessage.get('role') == "employer":
        process_employer_request(jsonmessage, group=group)
    # Messages from workers: acceptances
    elif jsonmessage.get('role') == "worker":
        process_worker_request(jsonmessage, respondent=message.reply_channel, group=group)

    textforgroup = get_contracts(group)
    closed_contracts_num = JobContract.objects.filter(accepted=True, employer__group=group).count()
    if closed_contracts_num >= Constants.num_employers:
        group.day_over = True
        group.save()
        textforgroup['day_over'] = group.day_over
    Group(group_name).send({
        "text": json.dumps(textforgroup),
    })



# Connected to websocket.disconnect
def ws_disconnect(message, group_name):
    Group(group_name).discard(message.reply_channel)
