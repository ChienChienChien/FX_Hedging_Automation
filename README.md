**English** | [繁體中文](README_ZH-TW.md)

# Pre-Recognition FX Exposure Management via Automated Internal FX Transactions

## Objective

Shift the start of FX exposure management upstream—from the recognition of accounts receivable and accounts payable to the confirmation of the underlying foreign-currency sales contracts and purchase commitments—so that exposures can be captured and managed from the moment they arise.

Under this operating model, the business unit remains focused on core operations, while the risk management function centrally manages FX exposure. The solution converts sales, procurement, and finance data into standardized internal FX transactions between the business unit and the risk management function, creating a controlled workflow from exposure origination and position monitoring through internal risk transfer. Any subsequent decision to hedge externally—including whether, when, and how—is made independently by the risk management function and falls outside the system’s scope.

## Outcomes

| Area | Project Outcome |
|---|---|
| Risk management coverage | Established controls for pre-recognition FX exposures across USD- and EUR-denominated sales contracts, as well as USD-denominated purchases of steel coils, alloys, and other raw materials |
| Automation scale | Processes approximately USD 100 million of internal FX transfer transactions each month across sales and procurement |
| Daily automated processing | Consolidates data, evaluates business events, generates internal FX transactions, and posts them to downstream systems each day, with manual intervention limited to exceptions |
| Risk governance | Enables the business unit to monitor internal positions and P&L while routing identified exposures to the risk management function through internal FX transactions; any decision to hedge externally remains outside the system |
| Production track record | Has operated reliably in production for more than four years |

> Processes approximately USD 100 million in internal FX transaction volume per month across sales and procurement; it is not the outstanding FX exposure at any single point in time.

## Approach

### 1. Translate Risk Management Principles into Internal Transfer Rules

In partnership with the risk management function, the project defined risk ownership, exposure management periods, applicable currencies, and exchange-rate conventions, then translated these cross-functional policies into consistent data rules and transaction logic for internal FX transfers.

For sales, the exposure management period begins when a foreign-currency contract is confirmed and ends when the corresponding accounts receivable is recognized. For procurement, it begins when a foreign-currency purchase commitment is established and ends when the corresponding accounts payable is recognized.

### 2. Detect Business Events and Generate Internal FX Transactions

The processing pipeline integrates sales, procurement, A/R and A/P recognition, exchange-rate, and existing-position data. By comparing changes in business status and transaction amounts, it automatically detects exposure inception, amount adjustments, cancellations, and close-out upon accounting recognition, then generates standardized internal FX transfer transactions.

Managing the full exposure lifecycle allows the system to continuously reflect changes in the underlying business rather than relying on a static, point-in-time position snapshot.

### 3. Build Parallel Downstream Integrations and Exception Controls

Once transactions are generated, the system posts them automatically to two internal destinations in parallel:

- PAS, which enables the business unit to monitor internal FX positions and P&L and supports month-end close and reporting.
- RMD interface tables, which deliver internal FX transaction records to the risk management function, completing the system-managed portion of the internal risk-transfer process.

The system also maintains execution logs and sends exception alerts, enabling automated daily processing while limiting operational intervention to issues such as missing data or failed runs.

> **Terminology:** PAS is an existing position management system that calculates internal positions and P&L from transaction records. RMD refers to the interface tables used to exchange internal FX transfer transaction data with the risk management function.

## Architecture

```mermaid
flowchart TB
    A["Sales and procurement data<br> A/R and A/P"] --> D["Python<br>Internal transaction-processing layer"]
    B["Spot and forward FX rates"] --> D

    D --> E["PAS<br>Internal position<br>P&L monitoring"]
    D --> F["RMD<br>Internal transaction interface"]
    D --> G["Execution logs<br>exception alerts"]

    F --> H["Risk management function"]
    H -.-> I["External hedging decision and execution (separate process)"]
```

The Python internal FX transaction-processing layer is the core of the architecture. It handles cross-system data integration, state-change comparison, business-event evaluation, transaction generation, and data validation.

All transactions generated by the system are internal. PAS supports position and P&L monitoring within the business unit, while RMD delivers the corresponding internal FX transaction records to the risk management function. The system’s scope ends once those records have been delivered through RMD. The risk management function independently decides whether, when, and how to hedge the exposures in external markets.

## Technology

| Category | Technology / Tool | Project Application |
|---|---|---|
| Programming and data processing | Python | Cross-system data integration, business-event evaluation, amount calculation, and internal FX transaction generation |
| Database integration | SQL Server, SQL | Reads business data plus A/R and A/P recognition records and writes internal transaction records to PAS and RMD |
| Web automation | Selenium | Automatically retrieves external forward FX rates |
| Scheduling and monitoring | Windows Task Scheduler, Microsoft Teams | Runs the daily batch process and sends run-status and exception notifications |
