from dataclasses import dataclass
import re
from typing import Iterable, Optional

@dataclass
class InstructionSwitch:
    raw_content: str
    switch: str
    value: Optional[str]


line_continuation_regex = re.compile(
    r'''
    \s*(?:\\\n)
    ''',
    re.X
)

switch_regex = re.compile(
    r'''
        \s*
        --(?P<switch_name>\w+)         # switch name
        (?:=(?P<switch_value>[^\s]+))? # optional value
    ''',
    re.X
)

@dataclass
class DockerfileInstruction:
    line_begin: int
    line_end: int
    raw_content: str
    instruction_type: str # FROM/ARG/#/RUN etc.
    argument_begin_index: int

    def instruction_content(self, strip_line_continuations: bool, strip_comments: bool) -> str:
        content = self.raw_content[self.argument_begin_index:]
        if strip_comments:
            if (comment_pos := content.find('#')) > -1:
                content = content[0:comment_pos]
        if strip_line_continuations:
            content = content.replace('\\\n', ' ')
        return content

    # TODO: move elsewhere?
    def parse_switches(self) -> Iterable[InstructionSwitch]:
        """parse switches and update argument_begin_index"""
        while self.argument_begin_index < len(self.raw_content):
            match = line_continuation_regex.match(self.raw_content, self.argument_begin_index)
            if match:
                self.argument_begin_index = match.end()
                continue

            match = switch_regex.match(self.raw_content, self.argument_begin_index)
            if not match:
                break

            matched_groups = match.groupdict()
            yield InstructionSwitch(
                switch=matched_groups['switch_name'],
                value=matched_groups['switch_value'],
                raw_content=self.raw_content[self.argument_begin_index:match.span(0)[1]],
            )
            self.argument_begin_index = match.end()
