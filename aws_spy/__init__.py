"""ServerlessPy package ;D"""

__version__ = "0.2.0"

from aws_spy import responses
from aws_spy.core.logging import logger
from aws_spy.core.params_alias import Header, Path, Query
from aws_spy.core.schemas import (
    CORS,
    VPC,
    Authorizer,
    CloudFormationRef,
    HTTPApi,
    JSONFileRef,
    Provider,
    ServerlessConfig,
    build_cognito_issue_url,
)
from aws_spy.main import SpyAPI, SpyRouter

__all__ = (
    "SpyAPI",
    "SpyRouter",
    "Query",
    "Path",
    "Header",
    "ServerlessConfig",
    "Provider",
    "VPC",
    "HTTPApi",
    "CORS",
    "Authorizer",
    "build_cognito_issue_url",
    "JSONFileRef",
    "CloudFormationRef",
    "logger",
    "responses",
)
