# KR ETF RiskBudget Live Input Map

## Purpose

- fix where live core inputs come from
- close the operating path for ETF universe and price inputs

## Input Sources

- Korea ETF universe input:
  - external reference to the existing operating universe / operating price flow
- Korea ETF price input:
  - external reference to the existing operating price flow under the main project data path

## Live Core Handling Decision

- do not copy price input files into `live_core` at this stage
- keep data inputs as external references
- keep live core focused on operating outputs and operating documents

## Current Operating Rule

- portfolio, order sheet, and pre-trade control outputs inside `live_core` are the daily operating artifacts
- ETF universe and price data remain upstream external inputs feeding those artifacts
- operator does not inspect raw price files during the daily manual order decision unless a freshness issue is raised by pre-trade control
