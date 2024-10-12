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
    assert result[4] == DockerfileInstruction(
        line_begin=11,
        line_end=12,
        raw_content='    RUN cat /tmp/test.txt | tee \\\n    && false',
        instruction_type='RUN',
        argument_begin_index=8,
    )


def test_can_parse_multiple_switches() -> None:
    result = get_instructions(
        '''\
        FROM --platform=$BUILDPLATFORM ubuntu
        RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache
        RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \\
          --mount=type=cache,target=/var/lib/apt,sharing=locked \\
          apt update && apt-get --no-install-recommends install -y gcc
        '''
    )

    assert len(result) == 3
    assert result[0] == DockerfileInstruction(
        line_begin=1,
        line_end=1,
        raw_content='FROM --platform=$BUILDPLATFORM ubuntu',
        instruction_type='FROM',
        argument_begin_index=5,
    )
    switches = list(result[0].parse_switches())
    assert result[0].argument_begin_index == 30
    assert len(switches) == 1
    assert switches[0].switch == 'platform'
    assert switches[0].value == '$BUILDPLATFORM'

    assert result[1] == DockerfileInstruction(
        line_begin=2,
        line_end=2,
        raw_content='''RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache''',
        instruction_type='RUN',
        argument_begin_index=4,
    )
    switches = list(result[1].parse_switches())
    assert result[1].argument_begin_index == 4
    assert len(switches) == 0
    
    assert result[2] == DockerfileInstruction(
        line_begin=3,
        line_end=5,
        raw_content='RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \\\n' +
          '  --mount=type=cache,target=/var/lib/apt,sharing=locked \\\n' +
          '  apt update && apt-get --no-install-recommends install -y gcc',
        instruction_type='RUN',
        argument_begin_index=4,
    )
    switches = list(result[2].parse_switches())
    assert result[2].argument_begin_index == 120
    assert len(switches) == 2
    assert switches[0].switch == 'mount'
    assert switches[0].value == 'type=cache,target=/var/cache/apt,sharing=locked'
    assert switches[1].switch == 'mount'
    assert switches[1].value == 'type=cache,target=/var/lib/apt,sharing=locked'
    assert result[2].instruction_content(strip_line_continuations=False, strip_comments=False).strip() == 'apt update && apt-get --no-install-recommends install -y gcc'

def test_can_parse_switch_with_no_value() -> None:
    result = get_instructions(
        '''\
        FROM scratch
        COPY --link /foo /bar
        '''
    )

    assert len(result) == 2
    assert result[0] == DockerfileInstruction(
        line_begin=1,
        line_end=1,
        raw_content='FROM scratch',
        instruction_type='FROM',
        argument_begin_index=5,
    )
    switches = list(result[0].parse_switches())
    assert result[0].argument_begin_index == 5
    assert len(switches) == 0
    
    assert result[1] == DockerfileInstruction(
        line_begin=2,
        line_end=2,
        raw_content='''COPY --link /foo /bar''',
        instruction_type='COPY',
        argument_begin_index=5,
    )
    switches = list(result[1].parse_switches())
    assert result[1].argument_begin_index == 11
    assert len(switches) == 1
    assert switches[0].switch == 'link'
    assert switches[0].value is None
