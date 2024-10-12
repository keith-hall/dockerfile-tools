from dataclasses import dataclass
from dockerfile_parser import DockerfileInstruction, InstructionSwitch
from typing import Optional


@dataclass
class FromInstruction(DockerfileInstruction):
    image_name: str
    image_version: Optional[str]
    image_hash: Optional[str]
    stage_name: Optional[str]
    switches: list[InstructionSwitch]

    def image_ref(self) -> str:
        image_ref = self.image_name
        if self.image_version:
            image_ref += ':' + self.image_version
        if self.image_hash:
            image_ref += '@' + self.image_hash
        return image_ref


@dataclass
class ArgInstruction(DockerfileInstruction):
    arg_name: str
    arg_value: Optional[str]


@dataclass
class RunInstruction(DockerfileInstruction):
    switches: list[InstructionSwitch]
    shell_command: str
