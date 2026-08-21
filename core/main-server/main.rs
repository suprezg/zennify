/*
File Name: main.rs
Purpose: Binary entry point for the Zennify host server CLI.
*/

use clap::Parser;
use std::net::SocketAddr;
use zennifyserver::composables::server::{createRouter, SERVER_NAME, DEFAULT_HOST, DEFAULT_PORT};

/*
Command line arguments parser for Zennify server CLI.
*/
#[allow(non_snake_case)]
#[derive(Parser, Debug)]
#[command(name = SERVER_NAME, author, version, about = "Zennify Core Server CLI")]
pub struct CliArgs
{
    /*
    Flag to start the Axum host server.
    */
    #[arg(short = 's', long = "start-server", help = "Start the Axum host server")]
    pub startServer: bool,
}

/*
Main asynchronous entry point parsing arguments and starting the server.

Takes:
	None.

Gives:
	Result<(), Box<dyn std::error::Error>>: Exit status.
*/
#[allow(non_snake_case)]
#[tokio::main]
pub async fn main() -> Result<(), Box<dyn std::error::Error>>
{
    let args = CliArgs::parse();

    if args.startServer {
        println!("Starting Zennify Axum Host Server...");
        let router = createRouter();
        let addrStr = format!("{}:{}", DEFAULT_HOST, DEFAULT_PORT);
        let addr: SocketAddr = addrStr.parse()?;

        println!("Server listening on http://{}", addrStr);
        let listener = tokio::net::TcpListener::bind(addr).await?;
        axum::serve(listener, router).await?;
    } else {
        println!("Zennify Server CLI");
        println!("Usage: zennify --start-server (or -s)");
        println!("Pass --start-server to launch the Axum host server.");
    }

    Ok(())
}
