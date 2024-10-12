from dockerfile_parser import DockerfileInstruction
from instruction_parser import parser
from instruction_parser.instructions import RunInstruction
from typing import Iterable
from pathlib import Path
import re
from textwrap import dedent

http_proxy_env_regex = re.compile(r'''\bhttp_proxy=\S+''')
php_regex = re.compile(r'''\b(?:pecl|composer|php)\b''')
command_invocations_requiring_env_var_regex = re.compile(r'''\b(?:composer\s+install|apt-get)\b''')


def inject_ca_cert_and_proxy_env(raw_instructions: Iterable[DockerfileInstruction], ca_cert_pem: Path, proxy_url: str) -> Iterable[str]:
    ca_cert_injected = False
    php_config_injected = False

    for raw_instruction in raw_instructions:
        if raw_instruction.instruction_type == '#' and raw_instruction.raw_content == '# BEGIN INJECTED CA CERT INSTRUCTIONS':
            ca_cert_injected = True
        if raw_instruction.instruction_type == '#' and raw_instruction.raw_content == '# BEGIN INJECTED PHP PROXY CONFIG INSTRUCTIONS':
            php_config_injected = True
        if raw_instruction.instruction_type != 'RUN':
            yield raw_instruction.raw_content
            continue
        
        if not ca_cert_injected:
            # TODO: be more clever about checking which stage it was injected in and whether it still applies for future stages
            for instruction_line in create_ca_cert_instructions(ca_cert_pem):
                yield instruction_line
            ca_cert_injected = True

        instruction = parser.parse_raw_instruction(raw_instruction)

        if php_regex.search(instruction.shell_command) and not php_config_injected:
            php_config_injected = True
            for instruction_line in inject_php_proxy_config(proxy_url):
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


def add_proxy_before_command_invocations(proxy_url: str, instruction: RunInstruction, regex: re.Pattern) -> str:
    """NOTE: currently extremely naive... would be nice to parse the bash script to find where the command invocations actually are..."""
    index = instruction.argument_begin_index
    new_instruction = instruction.raw_content[0:instruction.argument_begin_index]
    while index < len(instruction.raw_content):
        match = regex.search(instruction.raw_content, index)
        if match:
            new_instruction += instruction.raw_content[index:match.start()] + f'http_proxy={proxy_url} ' + \
                instruction.raw_content[match.start():match.end()]
            index = match.end()
        else:
            break

    return new_instruction + instruction.raw_content[index:]
