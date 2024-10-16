from dockerfile_parser import DockerfileInstruction
from instruction_parser import parser
from instruction_parser.instructions import RunInstruction
from typing import Iterable
from pathlib import Path
import re
from textwrap import dedent

http_proxy_env_regex = re.compile(r'''\bhttps?_proxy=\S+''')
injected_comment_regex = re.compile(r'''^# BEGIN INJECTED (?P<injected_item>.*)? INSTRUCTIONS$''')
php_regex = re.compile(r'''\b(?:pecl|composer|php)\b''')
pip_regex = re.compile(r'''\bpip\s+install\b''')
command_invocations_requiring_env_var_regex = re.compile(r'''\b(?:composer\s+install|apt-get|curl(?P<https>)|apk(?P<https>))\b''')


def inject_ca_cert_and_proxy_env(raw_instructions: Iterable[DockerfileInstruction], ca_cert_pem: Path, proxy_url: str) -> Iterable[str]:
    config_injected = {}

    for raw_instruction in raw_instructions:
        if raw_instruction.instruction_type == '#':
            injected_comment_match = injected_comment_regex.match(raw_instruction.raw_content)
            if injected_comment_match:
                config_injected[injected_comment_match.group('injected_item')] = raw_instruction
        if raw_instruction.instruction_type != 'RUN':
            # TODO: buffer comments so that i.e. "lint instructions" stay bound to the instruction they belong to below
            yield raw_instruction.raw_content
            continue
        
        if not config_injected.get('CA CERT', None):
            # TODO: be more clever about checking which stage it was injected in and whether it still applies for future stages
            for instruction_line in create_ca_cert_instructions(ca_cert_pem):
                yield instruction_line
            config_injected['CA CERT'] = True # NOTE/TODO: here we are not setting to a raw instruction, do we need to?

        instruction = parser.parse_raw_instruction(raw_instruction)

        if php_regex.search(instruction.shell_command) and not config_injected.get('PHP PROXY CONFIG', None):
            config_injected['PHP PROXY CONFIG'] = True # NOTE/TODO: here we are not setting to a raw instruction, do we need to?
            for instruction_line in inject_php_proxy_config(proxy_url):
                yield instruction_line
        if pip_regex.search(instruction.shell_command) and not config_injected.get('PIP PROXY CONFIG', None):
            config_injected['PIP PROXY CONFIG'] = True # NOTE/TODO: here we are not setting to a raw instruction, do we need to?
            for instruction_line in inject_pip_proxy_config(proxy_url):
                yield instruction_line

        if command_invocations_requiring_env_var_regex.search(instruction.shell_command):
            if not http_proxy_env_regex.search(instruction.shell_command):
                # proxy not specified, add it
                yield add_proxy_before_command_invocations(proxy_url, instruction, command_invocations_requiring_env_var_regex)
            else:
                # proxy already specified, yield unchanged instruction
                yield instruction.raw_content
        else:
            yield instruction.raw_content


def create_ca_cert_instructions(ca_cert_pem: Path) -> Iterable[str]:
    ca_cert_contents = ca_cert_pem.read_text(encoding='utf-8')

    yield '# BEGIN INJECTED CA CERT INSTRUCTIONS'
    yield f'RUN cat <<EOF > /etc/ssl/certs/proxyCA.pem\n{ca_cert_contents}\nEOF'
    yield 'RUN cat /etc/ssl/certs/proxyCA.pem >> /etc/ssl/certs/ca-certificates.crt'
    yield '# END INJECTED CA CERT INSTRUCTIONS'


def inject_php_proxy_config(proxy_url: str) -> Iterable[str]:
    yield '# BEGIN INJECTED PHP PROXY CONFIG INSTRUCTIONS'

    yield dedent('''\
        RUN printf "[openssl]\\nopenssl.cafile = /etc/ssl/certs/ca-certificates.crt\\n" | tee >> ${PHP_INI_DIR}/php.ini && \\
            printf "[curl]\\ncurl.cainfo = /etc/ssl/certs/ca-certificates.crt\\n" | tee >> ${PHP_INI_DIR}/php.ini
    ''')

    proxy_url = proxy_url.replace('http://', 'https://')
    yield f'RUN pear config-set http_proxy {proxy_url}'
    yield 'RUN pear config-set php_ini ${PHP_INI_DIR}/php.ini'

    yield '# END INJECTED PHP PROXY CONFIG INSTRUCTIONS'


def inject_pip_proxy_config(proxy_url: str) -> Iterable[str]:
    yield '# BEGIN INJECTED PIP PROXY CONFIG INSTRUCTIONS'

    yield dedent('''\
        RUN mkdir -p $HOME/.config/pip && cat <<EOF >> $HOME/.config/pip/pip.conf
        [global]
        proxy = ''' + proxy_url + '''
        cert = /etc/ssl/certs/proxyCA.pem
        EOF
    ''')

    yield '# END INJECTED PIP PROXY CONFIG INSTRUCTIONS'


def add_proxy_before_command_invocations(proxy_url: str, instruction: RunInstruction, regex: re.Pattern) -> str:
    """NOTE: currently extremely naive... would be nice to parse the bash script to find where the command invocations actually are..."""
    index = instruction.argument_begin_index
    new_instruction = instruction.raw_content[0:instruction.argument_begin_index]
    while index < len(instruction.raw_content):
        match = regex.search(instruction.raw_content, index)
        if match:
            env_var_name = 'https_proxy' if match.group('https') else 'http_proxy' # NOTE: intentionally keeps the http:// url, needed for alpine apk
            new_instruction += instruction.raw_content[index:match.start()] + f'{env_var_name}={proxy_url} ' + \
                instruction.raw_content[match.start():match.end()]
            index = match.end()
        else:
            break

    return new_instruction + instruction.raw_content[index:]
