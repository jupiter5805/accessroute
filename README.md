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
