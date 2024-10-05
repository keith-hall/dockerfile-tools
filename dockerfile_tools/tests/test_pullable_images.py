from dockerfile_tools.get_pullable_images import get_pullable_images
from dockerfile_parser import parse_instructions
import pytest


@pytest.mark.integration
def test_can_resolve_args():
    instructions = parse_instructions(
        '''\
        ARG COMPOSER_VERSION="2.5.5"
        ARG PHP_VERSION="8.2.20"
        FROM public.ecr.aws/r7q2p6e2/gossm:0.3.0 AS gossm
        FROM composer:${COMPOSER_VERSION} AS composer
        FROM php:${PHP_VERSION}-apache-bullseye
        # prove irrelevant instructions are ignored for the purpose of resolving stage images
        COPY --link --from=composer /usr/bin/composer /usr/local/bin/composer
        '''
    )

    result = list(get_pullable_images(instructions))

    assert result == [
        'public.ecr.aws/r7q2p6e2/gossm:0.3.0',
        'composer:2.5.5',
        'php:8.2.20-apache-bullseye',
    ]
