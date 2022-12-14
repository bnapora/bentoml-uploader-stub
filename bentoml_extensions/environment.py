import os
import sys
import re
import subprocess
import platform

def get_env(name):
    "Return env var value if it's defined and not an empty string, or return Unknown"
    res = os.environ.get(name,'')
    return res if len(res) else "Unknown"

def show_install(show_nvidia_smi:bool=True):
    "Print user's setup information"
    #https://github.com/fastai/fastai1/blob/master/fastai/utils/collect_env.py#L22
    info = {}

    info["python"] = platform.python_version()

    # nvidia-smi
    cmd = "nvidia-smi"
    have_nvidia_smi = False
    try: result = subprocess.run(cmd.split(), shell=False, check=False, stdout=subprocess.PIPE)
    except: pass
    else:
        if result.returncode == 0 and result.stdout: have_nvidia_smi = True

    # XXX: if nvidia-smi is not available, another check could be:
    # /proc/driver/nvidia/version on most systems, since it's the
    # currently active version

    if have_nvidia_smi:
        smi = result.stdout.decode('utf-8')
        # matching: "Driver Version: 396.44"
        match = re.findall(r'Driver Version: +(\d+\.\d+)', smi)
        if match: 
            info["nvidia driver"] = match[0]

    # it's possible that torch might not see what nvidia-smi sees?
    gpu_total_mem = []
    nvidia_gpu_cnt = 0
    if have_nvidia_smi:
        try:
            cmd = "nvidia-smi --query-gpu=memory.total --format=csv,nounits,noheader"
            result = subprocess.run(cmd.split(), shell=False, check=False, stdout=subprocess.PIPE)
        except:
            info["nvidia-smi"] = "have nvidia-smi, but failed to query it"
        else:
            if result.returncode == 0 and result.stdout:
                output = result.stdout.decode('utf-8')
                gpu_total_mem = [int(x) for x in output.strip().split('\n')]
                nvidia_gpu_cnt = len(gpu_total_mem)


    if nvidia_gpu_cnt:  info["nvidia gpus"] = nvidia_gpu_cnt

    try:
        import torch

        info["torch"] = torch.__version__
        available = "available" if torch.cuda.is_available() else "**Not available** "
        info["torch cuda"] = f"{torch.version.cuda} / is {available}"
        info["torch cuda arch list"] = torch.cuda.get_arch_list()

        # no point reporting on cudnn if cuda is not available, as it
        # seems to be enabled at times even on cpu-only setups
        if torch.cuda.is_available():
            enabled = "enabled" if torch.backends.cudnn.enabled else "**Not enabled** "
            info["torch cudnn"] = f"{torch.backends.cudnn.version()} / is {enabled}"

        torch_gpu_cnt = torch.cuda.device_count()
        if torch_gpu_cnt:
            info["torch devices"] = torch_gpu_cnt
            # information for each gpu
            for i in range(torch_gpu_cnt):
                info[f"  - gpu{i}"] = (f"{gpu_total_mem[i]}MB | " if gpu_total_mem else "") + torch.cuda.get_device_name(i)
        else:
            if nvidia_gpu_cnt:
                info[nvidia_gpu_cnt] = f"Have {nvidia_gpu_cnt} GPU(s), but torch can't use them (check nvidia driver)"
            else:
                info[f"No GPUs available"] = None
    except:
        info["torch"] = "not installed"

    try:
        import tensorflow as tf
        info["tensorflow"] = tf.__version__
        info["list_physical_devices"] = tf.config.list_physical_devices()

    except:
        info["tensorflow"] = "not installed"


    if platform.system() == 'Linux':
        try:
            import distro
            info["distro"] = ' '.join(distro.linux_distribution())
        
        except:
            # partial distro info
            info["distro"] = platform.uname().version


    info["platform"] = platform.platform()
    info["conda env"] = get_env('CONDA_DEFAULT_ENV')
    info["python"] = sys.executable
    info["sys.path"] = "\n".join(sys.path)

    if have_nvidia_smi:
        if show_nvidia_smi: 
            info["nvidia-smi"] = f"\n{smi}"
    else:
        if torch_gpu_cnt: 
            info["no nvidia-smi is found"] = None
        else: 
            info["no supported gpus found on this system"] = None

    return info
