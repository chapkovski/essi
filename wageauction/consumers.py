from channels import Group
from channels.sessions import channel_session
from .models import Group as OtreeGroup, Request, JobContract, Player
import json
import time
from django.core import serializers
from django.core.serializers.json import DjangoJSONEncoder


def ws_connect(message, group_name):
    Group(group_name).add(message.reply_channel)


def process_employer_request(jsonmessage, mygroup):
    curemployer_id = jsonmessage['id_employer']
    wage_offer = jsonmessage['wage_offer']
    curplayer = Player.objects.get(pk=curemployer_id)
    curplayer.requests.create(amount=wage_offer)
    allrequests = curplayer.requests.all()
    print('ALL REQUESTS:: ', allrequests)
    latest_request = curplayer.requests.latest('created_at')
    print('THE MOST RECENT REQUEST:: ', latest_request)
    contract, created = curplayer.contract.get_or_create(defaults={'amount': wage_offer,
                                                                   'accepted': False, })
    if not created:
        contract.amount = wage_offer
        contract.save()
    print('CONTRACT TO FILL IN:: ', contract)
    active_contracts = list(JobContract.objects. \
        filter(accepted=False, employer__group=mygroup).values('pk', 'amount'))
    serialized_contracts = json.dumps(active_contracts, cls=DjangoJSONEncoder)
    # print(serializers.serialize("json", active_contracts))
    print(active_contracts)
    curemployer_id_id_in_group = jsonmessage['id_employer_in_group']
    wage_offer = jsonmessage['wage_offer']
    employers_left_in = jsonmessage['employers_left']
    now = time.time()
    time_left = round(mygroup.auctionenddate - now)

    if curemployer_id_id_in_group == 1:
        mygroup.standing1 = wage_offer
    elif curemployer_id_id_in_group == 2:
        mygroup.standing2 = wage_offer
    elif curemployer_id_id_in_group == 3:
        mygroup.standing3 = wage_offer
    elif curemployer_id_id_in_group == 4:
        mygroup.standing4 = wage_offer
    elif curemployer_id_id_in_group == 5:
        mygroup.standing5 = wage_offer

    mygroup.save()

    textforgroup = json.dumps({
        "from": "employer",
        "employer_id": curemployer_id,
        "employer_id_in_group": curemployer_id_id_in_group,
        "wage_offered": wage_offer,
        "time_left": time_left,
        "employers_left": employers_left_in,
        'active_contracts': serialized_contracts,

    })
    return textforgroup


def process_worker_request(jsonmessage, mygroup):
    curworker_id_id_in_group = jsonmessage['id_worker_in_group']
    curemployer_id_id_in_group = jsonmessage['id_employer_in_group']
    wage_accepted = jsonmessage['wage_accepted']
    now = time.time()
    employers_left_in = jsonmessage['num_employers_left']
    employers_left_in -= 1
    are_you_matched = 0
    time_left = round(mygroup.auctionenddate - now)

    # Are you matched directly?
    if curemployer_id_id_in_group == 1:
        mygroup.matched1 += 1
        if mygroup.matched1 == 1:
            are_you_matched = 1  # yes!
    elif curemployer_id_id_in_group == 2:
        mygroup.matched2 += 1
        if mygroup.matched2 == 1:
            are_you_matched = 1  # yes
    elif curemployer_id_id_in_group == 3:
        mygroup.matched3 += 1
        if mygroup.matched3 == 1:
            are_you_matched = 1  # yes
    elif curemployer_id_id_in_group == 4:
        mygroup.matched4 += 1
        if mygroup.matched4 == 1:
            are_you_matched = 1  # yes
    elif curemployer_id_id_in_group == 5:
        mygroup.matched5 += 1
        if mygroup.matched5 == 1:
            are_you_matched = 1  # yes:

    # If you are not matched directly, are there other standing offers identical to the one you have just accepted?
    if are_you_matched == 0:
        if wage_accepted == mygroup.standing1:
            if mygroup.matched1 != 1:
                curemployer_id_id_in_group = 1  # match them!
                mygroup.matched1 = 1
                are_you_matched = 2
        elif wage_accepted == mygroup.standing2:
            if mygroup.matched2 != 1:
                curemployer_id_id_in_group = 2  # match them!
                mygroup.matched2 = 1
                are_you_matched = 2
        elif wage_accepted == mygroup.standing3:
            if mygroup.matched3 != 1:
                curemployer_id_id_in_group = 3  # match them!
                mygroup.matched3 = 1
                are_you_matched = 2
        elif wage_accepted == mygroup.standing4:
            if mygroup.matched4 != 1:
                curemployer_id_id_in_group = 4  # match them!
                mygroup.matched4 = 1
                are_you_matched = 2
        elif wage_accepted == mygroup.standing5:
            if mygroup.matched5 != 1:
                curemployer_id_id_in_group = 5  # match them!
                mygroup.matched5 = 1
                are_you_matched = 2

    if are_you_matched == 0:
        employers_left_in += 1
    elif are_you_matched == 2:
        employers_left_in -= 1

    mygroup.save()

    # do something with those that are not first in the receiving end.
    textforgroup = json.dumps({
        "from": "worker",
        "employer_id_in_group": curemployer_id_id_in_group,
        "worker_id_in_group": curworker_id_id_in_group,
        "wage_accepted": wage_accepted,
        "time_left": time_left,
        "employers_left": employers_left_in,
        "first": are_you_matched,
    })
    return textforgroup


def ws_message(message, group_name):
    group_id = group_name[5:]
    jsonmessage = json.loads(message.content['text'])
    mygroup = OtreeGroup.objects.get(id=group_id)

    # Messages from employers: wage offers
    if (jsonmessage['role'] == "employer"):
        textforgroup = process_employer_request(jsonmessage, mygroup=mygroup)
    # Messages from workers: acceptances
    elif (jsonmessage['role'] == "worker"):
        textforgroup = process_worker_request(jsonmessage, mygroup=mygroup)
    Group(group_name).send({
        "text": textforgroup,
    })


# Connected to websocket.disconnect
def ws_disconnect(message, group_name):
    Group(group_name).discard(message.reply_channel)
