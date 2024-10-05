from dataclasses import dataclass

@dataclass
class DockerfileInstruction:
    line_begin: int
    line_end: int
    raw_content: str
    instruction_type: str # FROM/ARG/#/RUN etc.
    argument_begin_index: int

    def instruction_content(self, strip_line_continuations: bool, strip_comments: bool) -> str:
        content = self.raw_content[self.argument_begin_index:]
        # TODO: to strip comments, would need to skip inside strings if mounting volumes for example?
        if strip_comments:
            if (comment_pos := content.find('#')) > -1:
                content = content[0:comment_pos]
        if strip_line_continuations:
            content = content.replace('\\\n', ' ')
        return content
