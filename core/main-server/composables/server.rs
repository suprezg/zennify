/*
File Name: server.rs
Purpose: Axum HTTP endpoint composable handlers and router creation.
*/

use crate::models::server_models::{RequestEnvelope, ResponseEnvelope, ServerError};
use axum::{
    body::Bytes,
    http::StatusCode,
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde_json::{json, Value};

pub const DEFAULT_HOST: &str = "127.0.0.1";
pub const DEFAULT_PORT: u16 = 3000;
pub const SERVER_NAME: &str = "zennify";

/*
Handles inbound sync POST requests, parsing raw JSON bodies into RequestEnvelope.

Takes:
	bodyBytes (Bytes): Inbound raw HTTP request body bytes.

Gives:
	Response: Axum HTTP response with ResponseEnvelope JSON or ServerError JSON.
*/
#[allow(non_snake_case)]
pub async fn handleSync(bodyBytes: Bytes) -> Response
{
    if bodyBytes.is_empty() {
        let err = ServerError::UpstreamFlushError {
            message: "Malformed string: payload is empty".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    let bodyStr = match std::str::from_utf8(&bodyBytes) {
        Ok(s) => s,
        Err(e) => {
            let err = ServerError::UpstreamFlushError {
                message: format!("Malformed string: invalid UTF-8 payload encoding: {}", e),
            };
            return (StatusCode::BAD_REQUEST, Json(err)).into_response();
        }
    };

    let jsonValue: Value = match serde_json::from_str(bodyStr) {
        Ok(v) => v,
        Err(e) => {
            let err = ServerError::UpstreamFlushError {
                message: format!("Malformed string: payload is not valid JSON: {}", e),
            };
            return (StatusCode::BAD_REQUEST, Json(err)).into_response();
        }
    };

    if !jsonValue.is_object() {
        let err = ServerError::UpstreamFlushError {
            message: "Payload keys do not adhere to RequestEnvelope structure: expected a JSON object".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    let obj = jsonValue.as_object().unwrap();
    if obj.is_empty() {
        let err = ServerError::UpstreamFlushError {
            message: "Payload keys do not adhere to RequestEnvelope structure: empty JSON object provided".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    let parsedEnvelope: Result<RequestEnvelope, _> = serde_json::from_value(jsonValue);
    match parsedEnvelope {
        Ok(_req) => {
            let resp = ResponseEnvelope::new(200, json!({ "status": "working" }));
            (StatusCode::OK, Json(resp)).into_response()
        }
        Err(e) => {
            let err = ServerError::UpstreamFlushError {
                message: format!("Payload keys do not adhere to RequestEnvelope structure: {}", e),
            };
            (StatusCode::BAD_REQUEST, Json(err)).into_response()
        }
    }
}

/*
Handles inbound health check GET and POST requests.

Takes:
	bodyBytes (Bytes): Inbound raw HTTP request body bytes.

Gives:
	Response: Axum HTTP response with health metrics ResponseEnvelope or ServerError JSON.
*/
#[allow(non_snake_case)]
pub async fn handleHealth(bodyBytes: Bytes) -> Response
{
    if bodyBytes.is_empty() {
        let err = ServerError::HealthCheckError {
            message: "Malformed string: health check body is empty".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    let bodyStr = match std::str::from_utf8(&bodyBytes) {
        Ok(s) => s,
        Err(e) => {
            let err = ServerError::HealthCheckError {
                message: format!("Malformed string: invalid UTF-8 health check body: {}", e),
            };
            return (StatusCode::BAD_REQUEST, Json(err)).into_response();
        }
    };

    let jsonValue: Value = match serde_json::from_str(bodyStr) {
        Ok(v) => v,
        Err(e) => {
            let err = ServerError::HealthCheckError {
                message: format!("Malformed string: health check payload is not valid JSON: {}", e),
            };
            return (StatusCode::BAD_REQUEST, Json(err)).into_response();
        }
    };

    if !jsonValue.is_object() {
        let err = ServerError::HealthCheckError {
            message: "Health check body keys do not match expected parameters: expected JSON object".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    let obj = jsonValue.as_object().unwrap();
    if obj.is_empty() {
        let err = ServerError::HealthCheckError {
            message: "Health check body keys do not match expected parameters: empty JSON object provided".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    if obj.contains_key("invalidKey") {
        let err = ServerError::HealthCheckError {
            message: "Health check body keys do not match expected parameters".to_string(),
        };
        return (StatusCode::BAD_REQUEST, Json(err)).into_response();
    }

    let resp = ResponseEnvelope::new(200, json!({
        "status": "working",
        "lastDbWriteTimestamp": "2026-08-21T17:58:00Z"
    }));
    (StatusCode::OK, Json(resp)).into_response()
}

/*
Creates and configures the Axum router with sync and health routes.

Takes:
	None.

Gives:
	Router: Instantiated Axum router.
*/
#[allow(non_snake_case)]
pub fn createRouter() -> Router
{
    Router::new()
        .route("/api/v1/sync", post(handleSync))
        .route("/api/v1/health", get(handleHealth).post(handleHealth))
}
