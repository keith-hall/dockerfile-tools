from .get_pullable_images import get_pullable_images
from dockerfile_parser import read_dockerfile
from pathlib import Path
import sys

if sys.argv[1] == 'get_pullable_images':
    print('\n'.join(get_pullable_images(read_dockerfile(Path(sys.argv[2])))))
else:
    print('unknown command')
    exit(1)
