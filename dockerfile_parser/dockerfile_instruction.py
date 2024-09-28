from dataclasses import dataclass

@dataclass
class DockerfileInstruction:
    line_begin: int
    line_end: int
    raw_content: str
    instruction_type: str # FROM/ARG/#/RUN etc.
    argument_begin_index: int

    def instruction_content(self) -> str:
        return self.raw_content[self.argument_begin_index:]
        # TODO: (for anything other than a RUN instruction which already supports comments)?, split at a comment marker so that parsing FROM ... # blah doesn't affect the stage name etc?
        # actually, `FROM composer:2.5.5 AS my_base # test` is a syntax error. Probably same applies for other instructions too, except RUN etc/
