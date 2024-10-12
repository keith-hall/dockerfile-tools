from .get_pullable_images import get_pullable_images
from .inject_proxy_ca import inject_ca_cert_and_proxy_env
from dockerfile_parser import read_dockerfile
from pathlib import Path
import sys
from os.path import expanduser
import os


if sys.argv[1] == 'get_pullable_images':
    print('\n'.join(get_pullable_images(read_dockerfile(Path(sys.argv[2])))))
elif sys.argv[1] == 'inject_proxy_ca':
    output = inject_ca_cert_and_proxy_env(
        read_dockerfile(Path(sys.argv[2])),
        Path(expanduser(sys.argv[3])),
        os.getenv('http_proxy')
    )
    print('\n'.join(output))
else:
    print('unknown command')
    exit(1)
