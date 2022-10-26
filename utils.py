from subprocess import run, Popen, PIPE

def call(command):
    # return os.popen().read()
    result = run(command, check=True, capture_output=True, encoding='utf8')
    return result.stdout


def call_in_bg(command):
    Popen(command, stdout=PIPE)


class LazyImport:
    def __init__(self, module_name):
        self.module_name = module_name
        self.module = None

    def __getattr__(self, func_name):
        if self.module is None:
            self.module = __import__(self.module_name)
        return getattr(self.module, func_name)
