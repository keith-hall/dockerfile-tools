from instruction_parser import parser
from instruction_parser.instructions import FromInstruction, ArgInstruction
from dockerfile_parser import DockerfileInstruction
import pytest


def test_from():
    raw_instruction = DockerfileInstruction(
        line_begin=1,
        line_end=1,
        raw_content='FROM composer:2.5.5\\\n AS my_base # php',
        instruction_type='FROM',
        argument_begin_index=5,
    )

    result = parser.parse_raw_instruction(raw_instruction)

    assert isinstance(result, FromInstruction)
    assert result.image_name == 'composer'
    assert result.image_version == '2.5.5'
    assert result.stage_name == 'my_base'
    # TODO: assert base fields all still present and correct


def test_arg():
    raw_instruction = DockerfileInstruction(
        line_begin=2,
        line_end=2,
        raw_content='ARG hello="world"',
        instruction_type='ARG',
        argument_begin_index=4,
    )

    result = parser.parse_raw_instruction(raw_instruction)

    assert isinstance(result, ArgInstruction)
    assert result.arg_name == 'hello'
    assert result.arg_value == 'world'


@pytest.mark.parametrize('instruction',
    [
        'FROM --platform=linux/amd64 abc:1.2.3',
        'FROM --platform=linux/amd64 \\\nabc:1.2.3',
        'FROM \\\n --platform=linux/amd64 abc:1.2.3',
        'FROM \\\n--platform=linux/amd64 \\\n abc:1.2.3  ',
    ]
)
def test_from_platform(instruction: str):
    raw_instruction = DockerfileInstruction(
        line_begin=1,
        line_end=1,
        raw_content=instruction,
        instruction_type='FROM',
        argument_begin_index=5,
    )

    result = parser.parse_raw_instruction(raw_instruction)

    assert isinstance(result, FromInstruction)
    assert result.image_name == 'abc'
    assert result.image_version == '1.2.3'
    assert result.stage_name is None
    assert len(result.switches) == 1
    assert result.switches[0].switch == 'platform'
    assert result.switches[0].value == 'linux/amd64'
    # TODO: assert base fields all still present and correct
