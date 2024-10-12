from .instructions import FromInstruction, ArgInstruction, RunInstruction
from dockerfile_parser import DockerfileInstruction
import re
from dataclasses import asdict


def parse_raw_instruction(instruction: DockerfileInstruction) -> DockerfileInstruction:
    match instruction.instruction_type:
        case 'FROM':
            return parse_from_instruction(instruction)
        case 'ARG':
            return parse_arg_instruction(instruction)
        case 'RUN':
            return parse_run_instruction(instruction)
    raise ValueError('unknown instruction type', instruction)


from_regex = re.compile(
    r'''
        ^\s*
        (?P<image_name>[^\s:@]+)
        
        (?:\s*:\s*
            (?P<image_version>[^\s@]+)
        )?
        (?:\s*@\s*
            (?P<image_hash>[^\s@]+)
        )?
        (?:
            \s*(?i:AS)\s*
            (?P<stage_name>\S+)
        )?
    ''',
    re.X
)


def parse_arg_instruction(instruction: DockerfileInstruction) -> None:
    arg = instruction.instruction_content(strip_line_continuations=True, strip_comments=True).split('=', 1)
    return ArgInstruction(
        **asdict(instruction),
        arg_name=arg[0],
        arg_value=remove_surrounding_quotes(arg[1]) if len(arg) > 1 else None
    )


def remove_surrounding_quotes(value: str) -> str:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    return value


def parse_from_instruction(instruction: DockerfileInstruction) -> None:
    switches = list(instruction.parse_switches())
    match = from_regex.match(instruction.instruction_content(strip_line_continuations=True, strip_comments=True))

    if not match:
        raise ValueError('unable to parse from instruction', instruction)

    from_detail = match.groupdict()
    return FromInstruction(**asdict(instruction), switches=switches, **from_detail)


def parse_run_instruction(instruction: DockerfileInstruction) -> None:
    switches = list(instruction.parse_switches())
    # line continuations and comments are valid in shell script # TODO: check also applies to PowerShell...
    shell_command = instruction.instruction_content(strip_line_continuations=False, strip_comments=False)

    return RunInstruction(**asdict(instruction), switches=switches, shell_command=shell_command)
