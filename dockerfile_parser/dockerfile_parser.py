from pathlib import Path
from typing import Iterable
import re
from .dockerfile_instruction import DockerfileInstruction

heredoc_begin_regex = re.compile(
    r'''\s<<(\w+)\b'''
)
instruction_regex = re.compile(
    r'''^\s*(#|\S+)\s*'''
)


def read_dockerfile(dockerfile_path: Path) -> Iterable[DockerfileInstruction]:
    return parse_instructions(dockerfile_path.read_text(encoding='utf-8'))


def parse_instructions(dockerfile_contents: str) -> Iterable[DockerfileInstruction]:
    current_instruction = ''
    line_no = 0
    line_begin = 0
    line_continuation = False
    inside_heredoc = None

    for line in dockerfile_contents.splitlines(): # TODO: ensure ends in \n? so dont need to emit one more result
        line_no += 1
        if not line_continuation and not inside_heredoc:
            current_instruction = line
            line_begin = line_no
        else:
            current_instruction += '\n' + line

        line_continuation = line.endswith('\\') or (line_continuation and line.lstrip().startswith('#'))
        if not line_continuation:
            if not inside_heredoc:
                heredoc_match = heredoc_begin_regex.search(line) # TODO: do we need to ignore heredocs in comments etc? nested heredocs?
                if heredoc_match:
                    inside_heredoc = heredoc_match.groups()[0]
            elif line == inside_heredoc: # if the line consists of only an unindented HEREDOC, then the heredoc and the instruction ends
                inside_heredoc = None

            if not inside_heredoc:
                instruction_match = instruction_regex.match(current_instruction)
                yield DockerfileInstruction(
                    line_begin,
                    line_no,
                    current_instruction, # NOTE: we are even emitting blank lines here, so the Dockerfile can be fully reconstructed later with no changes
                    instruction_match.groups()[0] if instruction_match else None,
                    instruction_match.end() if instruction_match else 0,
                )
