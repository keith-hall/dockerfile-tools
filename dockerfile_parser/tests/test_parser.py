from dockerfile_parser import parse_instructions, DockerfileInstruction
from textwrap import dedent


def get_instructions(content: str) -> list[DockerfileInstruction]:
    content = dedent(content)
    instructions = list(parse_instructions(content))
    return instructions


def test_heredoc_and_indented_run() -> None:
    result = get_instructions(
        '''\
        FROM composer:2.5.5 AS my_base

        RUN cat <<EOF > /tmp/test.txt
            1
            2
            3
            4
            5
        EOF

            RUN cat /tmp/test.txt | tee \\
            && false
        '''
    )

    assert len(result) == 5
    assert result[0] == DockerfileInstruction(
        line_begin=1,
        line_end=1,
        raw_content='FROM composer:2.5.5 AS my_base',
        instruction_type='FROM',
        argument_begin_index=5,
    )
    assert result[1] == DockerfileInstruction(
        line_begin=2,
        line_end=2,
        raw_content='',
        instruction_type=None,
        argument_begin_index=0,
    )
    assert result[2] == DockerfileInstruction(
        line_begin=3,
        line_end=9,
        raw_content='RUN cat <<EOF > /tmp/test.txt\n    1\n    2\n    3\n    4\n    5\nEOF',
        instruction_type='RUN',
        argument_begin_index=4,
    )
    assert result[3] == DockerfileInstruction(
        line_begin=10,
        line_end=10,
        raw_content='',
        instruction_type=None,
        argument_begin_index=0,
    )
    print(result[4])
    assert result[4] == DockerfileInstruction(
        line_begin=11,
        line_end=12,
        raw_content='    RUN cat /tmp/test.txt | tee \\\n    && false',
        instruction_type='RUN',
        argument_begin_index=8,
    )
