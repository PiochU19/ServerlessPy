"""ServerlessPy package ;D"""

__version__ = "0.1.0"

from aws_spy.core.params_alias import Header, Path, Query
from aws_spy.core.schemas import (
    CORS,
    VPC,
    Authorizers,
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
    "Authorizers",
    "build_cognito_issue_url",
    "JSONFileRef",
    "CloudFormationRef",
)
