import platform

import zensvi
from zensvi.cv import ClassifierLighting
from zensvi.download import MLYDownloader
from zensvi.metadata import MLYMetadata


print(f"Python: {platform.python_version()}")
print(f"ZenSVI: {zensvi.__version__}")
print("MLYDownloader: OK")
print("MLYMetadata: OK")
print("ClassifierLighting: OK")
