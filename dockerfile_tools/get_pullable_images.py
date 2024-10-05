from dockerfile_parser import DockerfileInstruction
from instruction_parser import parser
from instruction_parser.instructions import FromInstruction, ArgInstruction
from typing import Iterable, Optional


def parse_stages(raw_instructions: Iterable[DockerfileInstruction], build_args: Optional[dict] = None) -> Iterable[FromInstruction]:
    arg_map = {**build_args} if build_args else {} # clone the input dict so we don't mutate it
    stages = []
    for raw_instruction in raw_instructions:
        if raw_instruction.instruction_type not in ('ARG', 'FROM'):
            continue
        
        # replace ARG references # TODO: think about moving to parser or even raw_instruction.instruction_content method?
        for arg_name, value in arg_map.items():
            # NOTE: is it possible for an instruction to be interpolated from an ARG?
            # TODO: concept of raw contents vs interpolated?
            raw_instruction.raw_content = raw_instruction.raw_content.replace('${' + arg_name + '}', value or '') # TODO: case insensitive?

        instruction = parser.parse_raw_instruction(raw_instruction)
        match instruction:
            case FromInstruction() as from_instruction:
                stages.append(from_instruction)
            case ArgInstruction() as arg_instruction:
                if arg_instruction.arg_value is not None or arg_instruction.arg_name not in arg_map:
                    arg_map[arg_instruction.arg_name] = arg_instruction.arg_value or ''

    return stages


def get_pullable_images(raw_instructions: Iterable[DockerfileInstruction], build_args: Optional[dict] = None) -> Iterable[str]:
    stage_list = parse_stages(raw_instructions, build_args)
    stages = {}
    for stage in stage_list:
        if stage.image_name in stages:
            continue

        stages[stage.stage_name] = stage

        if stage.image_hash or stage.image_version:
            yield stage.image_ref()

