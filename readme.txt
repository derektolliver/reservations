# Instructions

## Dependencies

Dependencies can be installed using the following:

```
pip install -r requirements.txt
```

Server can be ran by using the following:
```
python3 server.py
```

# APIs

APIs are documented in `availability.py`

# Considerations before going production

1. Testing. I didn't include this for the exercise but we would absolutely need unit test and API tests implemented with ample coverage (95%+ should be achievable).
2. AuthN/Z. None of the routes currently support any form of auth. Before going live, we should restrict our endpoints to only support requests from trusted sources who have the right permission(s). 
2. Containerization. Preparing dockerfile(s) for easily shared development, building in CI/CD, and deploying would be ideal to simplify the respective processes.
3. Validation. The endpoints have some validation in place, but ideally we would implement tighter constraints on provided input to meet our assumptions and alleviate incorrect use of the API. This should optimally leverage shared middlewares so we can use it across all of our routes and respond with the proper status codes.

# Testing

A reasonable testing flow is as follows:

1. Call POST on /availability to submit an availability

```
curl -X "POST" "http://127.0.0.1:5000/availability" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "providerId": "<some uuid>",
  "startTime": "2024-08-30 11:00:00",
  "endTime": "2024-08-30 14:00:00"
}'
```

2. Call GET on /availability to retrieve availability within a given start and end time

```
curl "http://127.0.0.1:5000/availability?startTime=2024-08-30%2012%3A00%3A00&endTime=2024-08-30%2013%3A00%3A00"
```

3. Call POST on /availability/reserve to reserve a time slot

```
curl -X "POST" "http://127.0.0.1:5000/availability/reserve?startTime=2024-08-27%2012%3A00%3A00&endTime=2024-08-27%2013%3A00%3A00" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "clientId": "<some uuid>",
  "timeSlot": "2024-08-30 12:00:00",
  "timeSlotId": "<some timeSlotId uuid from previous request that matches our provided timeSlot>"
}'
```

4. Call PUT on /availability/confirm/\<timeSlotId\> to confirm the reservation

```
curl -X "PUT" "http://127.0.0.1:5000/availability/confirm/<timeSlotId>" \
     -H 'Content-Type: application/json; charset=utf-8' \
     -d $'{
  "timeSlot": "2024-08-30 12:00:00"
}'
```


