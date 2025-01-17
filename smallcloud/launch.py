import os, json, requests, termcolor, functools
from typing import Optional, List, Dict, Any, Union, Callable
import cloudpickle
from smallcloud import config, call_api


MAX_UPLOAD_SIZE = 25*1024*1024


def upload_file(fn: str):
    config.read_config_file()
    size = os.path.getsize(fn)
    if size > MAX_UPLOAD_SIZE:
        raise Exception("Maximum archive size is %0.1fM, your code %0.1fM" % (MAX_UPLOAD_SIZE/1024/1024, size/1024/1024))
    url = config.v1_url + "task-file-upload"
    headers = config.account_and_secret_key_headers()
    files = {
        'file1': (os.path.basename(fn), open(fn, 'rb'), 'application/zip'),
    }
    print(url, "POST", os.path.basename(fn))
    r = requests.post(url, files=files, headers=headers)
    if r.status_code != 200:
        print("HTTP STATUS", r.status_code)
        quit(1)
    j = json.loads(r.text)
    if j["retcode"] != "OK":
        print(termcolor.colored(j["retcode"], "red"), j["human_readable_message"])
        quit(1)
    return j["upload_id"]


@functools.lru_cache()
def code_upload():
    from smallcloud import code_to_zip
    return upload_file(code_to_zip())


def launch_task(
    task_name: str,
    training_function: Union[Callable, str],
    args: List[Any] = [],
    kwargs: Dict[str, Any] = {},
    gpu_type="a5000",  # or more specifically cluster/gpu_type, "ant/a5000"
    gpus: int = 0,
    shutdown: str = "auto",  # "always", "never", "auto" doesn't shutdown if there's an error so you can look at the logs.
    nice: int = 1,  # 0 preempts others, 1 normal, 2 low
    os_image: str = "",
    env: Dict[str, str] = {},
    upload_code_zip: bool = False,
    call_function_directly: Optional[bool] = None,
):
    if call_function_directly or (call_function_directly is None and config.already_running_in_cloud):
        for k, v in env.items():
            os.environ[k] = v
        training_function(*args, **kwargs)
        return
    config.read_config_file()
    os.makedirs("/tmp/smc-temp", exist_ok=True)
    pickle_filename = f"/tmp/smc-temp/pickle-call-{task_name}.pkl"
    cloudpickle.dump({
        "training_function": training_function,
        "args": args,
        "kwargs": kwargs,
        "shutdown": shutdown,
        "env": {"TASK_NAME": task_name, **env},
        }, open(pickle_filename, "wb"))
    pickle_upload_id = upload_file(pickle_filename)
    code_zip = ""
    if upload_code_zip:
        code_zip = code_upload()
    post_json = {
    "task_name": task_name,
    "tenant_image": os_image,
    "gpu_type": gpu_type,
    "gpu_min": int(gpus),
    "gpu_max": int(gpus),
    "gpus_incr": 1,
    "file_zip": code_zip,
    "file_pkl": pickle_upload_id,
    "nice": nice,
    }
    ret = call_api.fetch_json(config.v1_url + "reserve", post_json, headers=config.account_and_secret_key_headers())
    call_api.pretty_print_response(ret)
