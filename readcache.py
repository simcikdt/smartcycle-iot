from diskcache import Cache

with Cache('/tmp/mycachedir') as cache:
    print('Heartrate: ', cache[b'heartrate'])
    print('Speed: ', cache[b'speed'])
    print('Cadence: ', cache[b'cadence'])