# AccessRoute ♿🗺️

AccessRoute is an accessibility-aware routing platform designed to find routes based not only on distance and travel time, but also on individual mobility requirements.

The system will consider factors such as:

- wheelchair accessibility
- stairs
- gradients
- lift availability
- surface conditions
- real-time accessibility disruptions

## Current Status

🚧 Active development

### Implemented

- FastAPI application
- Health-check endpoint
- Automated pytest coverage

## Planned Architecture

OpenStreetMap / Transport Data  
↓  
Data Ingestion  
↓  
PostgreSQL + PostGIS  
↓  
Accessibility Routing Engine  
↓  
FastAPI  
↓  
Interactive Route Application

## Tech Stack

Python · FastAPI · PostgreSQL · PostGIS · NetworkX · PySpark · Airflow · Docker · AWS · Terraform

## Community Accessibility Reporting & Moderation

AccessRoute supports community-submitted accessibility barrier reports across Manchester.

### Features
- Report blocked pavements, construction obstacles and accessibility barriers.
- Store geolocated reports in PostgreSQL/PostGIS.
- Review and approve reports through protected FastAPI endpoints.
- Match verified barriers to nearby OpenStreetMap street segments.
- Exclude verified, active closures from route calculations.
- Automatically stop applying expired closures.
- Preserve unverified reports without affecting routing decisions.

### Validation
- 45 automated tests passed after Phase 12.
- Manchester network: 33,052 nodes.
- Routing graph: 85,997 edges.
- PostgreSQL/PostGIS integration verified.

Future development includes a visual moderation dashboard and decision audit history.
