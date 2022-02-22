import requests, time, pprint, datetime
from typing import Dict, List, Any



def nlp_completion(req_session, model: str, prompt: str, temp: float, maxlen: int) -> str:
    url = "http://127.0.0.1:8000/v1/nlp-completion"
    data = {
        "prompt": prompt,
        "model": model,
        "temp": temp,
        "maxlen": maxlen,
    }
    t0 = time.time()
    resp = req_session.post(url, json=data)
    t1 = time.time()
    print("%0.1fms %s" % (1000*(t1 - t0), url))
    if resp.status_code != 200:
        raise Exception("nlp_completion failed: %i %s" % (resp.status_code, resp.text))
    json_resp = resp.json()
    import pprint
    pprint.pprint(json_resp)
    ticket = json_resp["ticket"]
    return ticket


def nlp_status(req_session, ticket: str) -> Dict[str, Any]:
    url = "http://127.0.0.1:8000/v1/nlp-completion-status"
    t0 = time.time()
    resp = req_session.get(url, params={"ticket": ticket})
    if resp.status_code != 200:
        raise Exception("nlp_status failed: %i %s" % (resp.status_code, resp.text))
    json_resp = resp.json()
    t1 = time.time()
    ymd_hms = datetime.datetime.now().strftime("%H%M%S.%f")
    print(ymd_hms, "%0.1fms" % (1000*(t1 - t0)), pprint.pformat(json_resp))
    return json_resp


def ping_test(req_session) -> None:
    url = "http://127.0.0.1:8000/ping"
    t0 = time.time()
    resp = req_session.get(url)
    if resp.status_code != 200:
        raise Exception("ping_test failed: %i %s" % (resp.status_code, resp.text))
    json_resp = resp.json()
    t1 = time.time()
    print("%0.1fms %s" % (1000*(t1 - t0), url))


def alt_test(req_session, n):
    req_session = requests.Session()
    req_session.headers.update({
        "X-Account": "oleg@smallcloud.ai",
        "X-Secret-API-Key": "aaabbbxxxyyy",
    })
    url = "http://127.0.0.1:8000/altsleep/2"
    print("started %i" % n)
    resp = req_session.get(url)
    if resp.status_code != 200:
        raise Exception("alt_test failed: %i %s" % (resp.status_code, resp.text))
    json_resp = resp.json()
    pprint.pprint(json_resp)
    return json_resp


def test_thread(n):
    req_session = requests.Session()
    req_session.headers.update({
        "X-Account": "oleg@smallcloud.ai",
        "X-Secret-API-Key": "aaabbbxxxyyy",
    })
    # alt_test(req_session, n)
    for i in range(5):
        ping_test(req_session)
    ticket = nlp_completion(req_session, "append_world", "hello", 0.7, 50)
    for i in range(10):
        nlp_status(req_session, ticket)


def multi_thread_test(n):
    t1 = time.time()
    import concurrent.futures
    threads = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=128) as executor:
        for n in range(100):
            threads.append(executor.submit(test_thread, n))
    reslist = []
    for thread in threads:
        r = thread.result()
        reslist.append(str(r))
    t2 = time.time()
    print("reslist len", len(reslist))
    print("reslist set", len(set(reslist)))
    print("total %0.1fms" % (1000*(t2 - t1)))


def single_thread_test():
    t1 = time.time()
    test_thread(0)
    t2 = time.time()
    print("total %0.1fms" % (1000*(t2 - t1)))


if __name__ == "__main__":
    single_thread_test()
