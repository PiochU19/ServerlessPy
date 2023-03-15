import pytest

from aws_spy import (
    CORS,
    Authorizer,
    HTTPApi,
    Provider,
    ServerlessConfig,
    SpyAPI,
    build_cognito_issue_url,
)


@pytest.fixture(scope="session")
def authorizer() -> Authorizer:
    return Authorizer(
        issuerUrl=build_cognito_issue_url("eu-central-1_abc123"),
        audience=["abc123"],
    )


@pytest.fixture(scope="session")
def cors() -> CORS:
    return CORS(
        allowedHeaders=["Content-Type", "Authorization"],
        exposedResponseHeaders=["X-Total-Count"],
        allowedMethods=["GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"],
        allowedOrigins=["*"],
    )


@pytest.fixture(scope="session")
def http_api(authorizer: Authorizer, cors: CORS) -> HTTPApi:
    return HTTPApi(authorizers={"jwt": authorizer}, cors=cors)


@pytest.fixture(scope="session")
def provider(http_api: HTTPApi) -> Provider:
    return Provider(
        region="us-east-1",
        role="arn:aws:iam::123456789:role/TestLambdaRole",
        httpApi=http_api,
    )


@pytest.fixture(scope="session")
def config(provider: Provider) -> ServerlessConfig:
    return ServerlessConfig(
        service="lambdas",
        plugins=["serverless-python-requirements"],
        provider=provider,
    )


@pytest.fixture
def app(config: ServerlessConfig) -> SpyAPI:
    return SpyAPI(config=config)
