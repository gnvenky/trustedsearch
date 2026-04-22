# Starter Kit Notes

This local project is inspired by a trusted search starter kit that separates ingestion from the API surface.

Key ideas adapted here:
- keep a connector-style ingestion entrypoint that builds the indexes from source files
- expose a simple API boundary for search requests
- combine lexical and vector retrieval
- preserve citations and confidence metadata in the response
- leave room for future auth and audit logging upgrades
