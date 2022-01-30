import platform

version = "2.9.1"


def user_agent(api_version="v2"):
    return f"twarc/{version} ({platform.system()} {platform.machine()}) API/{api_version} {platform.python_implementation()}/{platform.python_version()}"
