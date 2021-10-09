import json
import requests
from jsonpath_rw import parse
from dateutil.parser import parse as date_parse

deliveries_for_planning_response = requests.get("http://localhost:3001/Deliveries_for_planning")
planned_route_response = requests.get("http://localhost:3000/planned_route")


def test_a():
    assert deliveries_for_planning_response.status_code == 200
    assert planned_route_response.status_code == 200

    response_json = json.loads(deliveries_for_planning_response.text)
    jsonpath_expr = parse('[*].id')
    filter_only_planned = [x for x in response_json if x['current_state'] == 'planned']
    delivery_for_planning_ids = [match.value for match in jsonpath_expr.find(filter_only_planned)]

    response_json = json.loads(planned_route_response.text)
    jsonpath_expr = parse('deliveries[*].id')
    planned_route_ids = [match.value for match in jsonpath_expr.find(response_json)]
    check = all(item in planned_route_ids for item in delivery_for_planning_ids)

    assert check is True


def test_b():
    response_json = json.loads(planned_route_response.text)
    carrying_capacity = response_json['resource']['carrying_capacity']

    planned_route_id_parser = parse('deliveries[*].id')
    planned_route_ids = [match.value for match in planned_route_id_parser.find(response_json)]
    total = 0

    for x in planned_route_ids:
        deliveries_for_planning_per_id_response = requests.get("http://localhost:3001/Deliveries_for_planning?id=" + x)
        if deliveries_for_planning_per_id_response.status_code == 200:
            response_json = json.loads(deliveries_for_planning_per_id_response.text)
            try:
                weight = response_json[0]['algorithm_fields']['weight']
                total = total + weight
            except IndexError:
                print(x + " does not have any value in Delivery for Planning")
    assert carrying_capacity > total


def test_c():
    response_json = json.loads(planned_route_response.text)
    deliveries = response_json['deliveries']
    route_min_time = date_parse(response_json['route_min_time'])
    route_max_time = date_parse(response_json['route_max_time'])
    jsonpath_expr = parse('[*]')
    filter_only_delivery = [x for x in deliveries if x['algorithm_fields']['type'] == 'delivery']
    deliveries_list = [match.value for match in jsonpath_expr.find(filter_only_delivery)]
    id_list = []

    for x in deliveries_list:
        eta = date_parse(x['algorithm_fields']['eta'])
        if not route_min_time < eta < route_max_time:
            id_list.append(x['id'])
    error_string = "Error ids ", id_list
    assert id_list == [], error_string


def test_d():
    response_json = json.loads(planned_route_response.text)
    deliveries = response_json['deliveries']
    jsonpath_expr = parse('[*]')
    deliveries_list = [match.value for match in jsonpath_expr.find(deliveries)]
    id_list = []

    for x in deliveries_list:
        eta = date_parse(x['algorithm_fields']['eta'])
        min_time = date_parse(x['min_time'])
        max_time = date_parse(x['max_time'])
        if not min_time < eta < max_time:
            id_list.append(x['id'])

    error_string = "Error ids ", id_list
    assert id_list == [], error_string


def test_e():
    response_json = json.loads(planned_route_response.text)
    deliveries = response_json['deliveries']
    jsonpath_expr = parse('[*].algorithm_fields.eta')
    eta_list = [match.value for match in jsonpath_expr.find(deliveries)]
    jsonpath_expr = parse('[*].algorithm_fields.time_to_next')
    time_to_next_list = [match.value for match in jsonpath_expr.find(deliveries)]
    id_list = []

    for x in range(len(time_to_next_list)):
        difference_time_in_seconds = (date_parse(eta_list[x + 1]) - date_parse(eta_list[x])).total_seconds()
        if not time_to_next_list[x] <= difference_time_in_seconds:
            id_list.append(deliveries[x]['id'])

    error_string = "Error ids ", id_list
    assert id_list == [], error_string
