# MSc Project - Dashboard Network System

This repository contains the implementation of my MSc project, **Implementing Dashboard Networks for Visualizing Multivariate Data**.

## Overview

This project implements a rule-based system for generating visualisations from multivariate tabular data and organising them into a dashboard network.

Users can upload a CSV dataset, select variables of interest, and receive suitable visualisation recommendations based on the detected variable types.

## Main Features

CSV dataset upload and preview
Automatic variable type detection
User variable selection and type correction
Optional categorical and temporal filtering
Rule-based visualisation recommendation
Automatic compact dashboard generation
Dashboard network construction based on shared variables
Explanations for recommended visualisations
Basic performance measurement

## Technologies

Python, Streamlit, pandas, Plotly

## Installation

Install the required packages:
pip install -r requirements.txt

## Running the Application

Run the application with:
streamlit run app.py

## Datasets

Two public datasets were used to evaluate the prototype:

- `hotel_bookings.csv` - Hotel Booking Demand dataset, used as the primary case study.
- `hour.csv` - Bike Sharing Dataset, used for cross-dataset validation.

The datasets are included to support reproducibility of the evaluation described in the dissertation.

## Repository Files

app.py - Main Streamlit application
test_datasets.py - Script used to prepare datasets for performance testing
requirements.txt - Required Python packages
hotel_bookings.csv - Dataset used for the primary case study  
hour.csv - Dataset used for cross-dataset validation
