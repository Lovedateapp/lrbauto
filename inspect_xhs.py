
import inspect
from xhs import core

source = inspect.getsource(core.XhsClient.request)
print(source)
