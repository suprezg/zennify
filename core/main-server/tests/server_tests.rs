/*
File Name: server_tests.rs
Purpose: Integration and unit tests for Axum sync and health endpoints.
*/

use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use serde_json::json;
use tower::util::ServiceExt;
use zennifyserver::composables::server::createRouter;
use zennifyserver::models::server_models::{ResponseEnvelope, ServerError};

pub const SYNC_ENDPOINT_URI: &str = "/api/v1/sync";
pub const HEALTH_ENDPOINT_URI: &str = "/api/v1/health";

/*
Tests POST /api/v1/sync endpoint with valid RequestEnvelope JSON payload.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testSyncEndpointValidJson()
{
    let app = createRouter();

    let validPayload = json!({
        "clientId": "123e4567-e89b-12d3-a456-426614174000",
        "deviceType": "desktop",
        "payload": {
            "action": "sync_logs"
        }
    });

    let req = Request::builder()
        .method("POST")
        .uri(SYNC_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(validPayload.to_string()))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::OK);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let respEnv: ResponseEnvelope = serde_json::from_slice(&bodyBytes).unwrap();

    assert_eq!(respEnv.statusCode, 200);
    assert_eq!(respEnv.serverVersion, 1);
    assert_eq!(respEnv.payload["status"], "working");
}

/*
Tests POST /api/v1/sync endpoint with empty body.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testSyncEndpointEmptyBody()
{
    let app = createRouter();

    let req = Request::builder()
        .method("POST")
        .uri(SYNC_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::UpstreamFlushError { message } => {
            assert!(message.contains("payload is empty"));
        }
        _ => panic!("Expected UpstreamFlushError variant"),
    }
}

/*
Tests POST /api/v1/sync endpoint with empty JSON object {}.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testSyncEndpointEmptyJsonObject()
{
    let app = createRouter();

    let emptyObjectPayload = json!({});

    let req = Request::builder()
        .method("POST")
        .uri(SYNC_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(emptyObjectPayload.to_string()))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::UpstreamFlushError { message } => {
            assert!(message.contains("empty JSON object provided"));
        }
        _ => panic!("Expected UpstreamFlushError variant"),
    }
}

/*
Tests POST /api/v1/sync endpoint with malformed raw string payload.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testSyncEndpointMalformedString()
{
    let app = createRouter();

    let malformedPayload = "random_malformed_string_not_json";

    let req = Request::builder()
        .method("POST")
        .uri(SYNC_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(malformedPayload))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::UpstreamFlushError { message } => {
            assert!(message.contains("Malformed string"));
        }
        _ => panic!("Expected UpstreamFlushError variant"),
    }
}

/*
Tests POST /api/v1/sync endpoint with valid JSON containing mismatched keys.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testSyncEndpointKeyMismatch()
{
    let app = createRouter();

    let invalidKeysPayload = json!({
        "wrongKey": "testValue",
        "anotherKey": 123
    });

    let req = Request::builder()
        .method("POST")
        .uri(SYNC_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(invalidKeysPayload.to_string()))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::UpstreamFlushError { message } => {
            assert!(message.contains("Payload keys do not adhere to RequestEnvelope structure"));
        }
        _ => panic!("Expected UpstreamFlushError variant"),
    }
}

/*
Tests POST /api/v1/health endpoint with valid request body.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testHealthEndpointValid()
{
    let app = createRouter();

    let validPayload = json!({
        "check": "status"
    });

    let req = Request::builder()
        .method("POST")
        .uri(HEALTH_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(validPayload.to_string()))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::OK);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let respEnv: ResponseEnvelope = serde_json::from_slice(&bodyBytes).unwrap();

    assert_eq!(respEnv.statusCode, 200);
    assert_eq!(respEnv.payload["status"], "working");
    assert!(respEnv.payload["lastDbWriteTimestamp"].is_string());
}

/*
Tests POST /api/v1/health endpoint with empty body.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testHealthEndpointEmptyBody()
{
    let app = createRouter();

    let req = Request::builder()
        .method("POST")
        .uri(HEALTH_ENDPOINT_URI)
        .body(Body::empty())
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::HealthCheckError { message } => {
            assert!(message.contains("health check body is empty"));
        }
        _ => panic!("Expected HealthCheckError variant"),
    }
}

/*
Tests POST /api/v1/health endpoint with empty JSON object {}.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testHealthEndpointEmptyJsonObject()
{
    let app = createRouter();

    let emptyObjectPayload = json!({});

    let req = Request::builder()
        .method("POST")
        .uri(HEALTH_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(emptyObjectPayload.to_string()))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::HealthCheckError { message } => {
            assert!(message.contains("empty JSON object provided"));
        }
        _ => panic!("Expected HealthCheckError variant"),
    }
}

/*
Tests POST /api/v1/health endpoint with malformed string body.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testHealthEndpointMalformedString()
{
    let app = createRouter();

    let malformedPayload = "random_malformed_string_not_json";

    let req = Request::builder()
        .method("POST")
        .uri(HEALTH_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(malformedPayload))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::HealthCheckError { message } => {
            assert!(message.contains("Malformed string"));
        }
        _ => panic!("Expected HealthCheckError variant"),
    }
}

/*
Tests POST /api/v1/health endpoint with valid JSON containing mismatched keys.

Takes:
	None.

Gives:
	None.
*/
#[allow(non_snake_case)]
#[tokio::test]
async fn testHealthEndpointKeyMismatch()
{
    let app = createRouter();

    let invalidKeysPayload = json!({
        "invalidKey": "randomValue"
    });

    let req = Request::builder()
        .method("POST")
        .uri(HEALTH_ENDPOINT_URI)
        .header("content-type", "application/json")
        .body(Body::from(invalidKeysPayload.to_string()))
        .unwrap();

    let response = app.oneshot(req).await.unwrap();
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);

    let bodyBytes = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let serverErr: ServerError = serde_json::from_slice(&bodyBytes).unwrap();

    match serverErr {
        ServerError::HealthCheckError { message } => {
            assert!(message.contains("Health check body keys do not match expected parameters"));
        }
        _ => panic!("Expected HealthCheckError variant"),
    }
}
