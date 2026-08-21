/*
File Name: server_models.rs
Purpose: Data structures and models for server requests, responses, and errors.
*/

use serde::{Deserialize, Serialize};
use serde_json::Value;

pub const DEFAULT_SERVER_VERSION: u64 = 1;

/*
Device form factor classification for Backend-For-Frontend payload adaptation.
*/
#[allow(non_snake_case)]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub enum DeviceType
{
    Desktop,
    Mobile,
    EmbeddedSlint,
}

/*
Inbound request envelope sent by client form factors containing metadata and payload.
*/
#[allow(non_snake_case)]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct RequestEnvelope
{
    pub clientId: String,
    pub deviceType: DeviceType,
    pub payload: Value,
}

/*
Outbound response envelope returned by the host server containing status code, version, and payload.
*/
#[allow(non_snake_case)]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase")]
pub struct ResponseEnvelope
{
    pub statusCode: u16,
    pub serverVersion: u64,
    pub payload: Value,
}

/*
Server error categories representing upstream flush, payload generation, or health check failures.
*/
#[allow(non_snake_case)]
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "camelCase", tag = "type")]
pub enum ServerError
{
    UpstreamFlushError
    {
        message: String,
    },
    PayloadGenerationError
    {
        message: String,
    },
    HealthCheckError
    {
        message: String,
    },
}

impl ResponseEnvelope
{
    /*
    Constructs a new ResponseEnvelope with default server version.

    Takes:
    	statusCode (u16): HTTP status code integer.
    	payload (Value): Serde JSON payload value.

    Gives:
    	ResponseEnvelope: Instantiated response envelope struct.
    */
    #[allow(non_snake_case)]
    pub fn new(statusCode: u16, payload: Value) -> Self
    {
        Self
        {
            statusCode,
            serverVersion: DEFAULT_SERVER_VERSION,
            payload,
        }
    }
}
