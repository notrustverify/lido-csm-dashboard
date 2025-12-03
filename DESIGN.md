# Lido CSM Operator Dashboard
## Technical Design Document

**Version:** 1.0  
**Date:** December 2, 2025  
**Author:** Design Document for Dagan

---

## Executive Summary

This document outlines the design for a Python application that enables Lido Community Staking Module (CSM) operators to track their validator earnings, excess bond, and cumulative rewards. The application will support both a web interface for real-time monitoring and a CLI mode for quick lookups.

**Feasibility Assessment: YES, this is very achievable.**

The required data is fully accessible through:
- On-chain smart contract calls (CSModule, CSAccounting, CSFeeDistributor)
- The csm-rewards GitHub repository (Merkle trees with reward allocations)
- Beacon chain APIs for validator performance data
- Lido's Subgraph for historical data

---

## Existing Solutions & Landscape

### Official Lido Tools
| Tool | Description | Gap for Your Use Case |
|------|-------------|----------------------|
| **CSM Widget** (csm.lido.fi) | Official UI for managing operators | Limited historical earnings view |
| **csm-rewards repo** | Pre-generated Merkle proofs | Raw data, no visualization |
| **Lido Subgraph** | GraphQL API for protocol data | Doesn't include CSM-specific rewards |

### Third-Party Tools
| Tool | Description | Gap for Your Use Case |
|------|-------------|----------------------|
| **Sedge** (Nethermind) | Monitoring stack with Grafana dashboards | Requires full node setup |
| **DappNode CSM Package** | Integrated monitoring | Tied to DappNode infrastructure |
| **Launchnodes** | Hosted validator monitoring | Commercial service |
| **ethereum-validators-monitoring** (Lido) | Performance bot | Designed for professional operators |

### The Gap Your Tool Fills
**No existing standalone tool provides:**
- Simple address → earnings lookup without running infrastructure
- Combined view of excess bond + cumulative rewards
- Lightweight web/CLI interface for quick checks
- Historical earnings tracking over time

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     CSM Operator Dashboard                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   CLI Mode   │    │   Web Mode   │    │   API Server     │  │
│  │   (Typer)    │    │   (FastAPI)  │    │   (Optional)     │  │
│  └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘  │
│         │                   │                      │            │
│         └───────────────────┴──────────────────────┘            │
│                             │                                    │
│                    ┌────────┴────────┐                          │
│                    │   Core Engine   │                          │
│                    └────────┬────────┘                          │
│                             │                                    │
│    ┌────────────────────────┼────────────────────────┐          │
│    │                        │                        │          │
│    ▼                        ▼                        ▼          │
│ ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│ │  On-Chain    │    │   Rewards    │    │    Beacon        │   │
│ │  Data Layer  │    │   Tree Layer │    │    Chain Layer   │   │
│ │  (web3.py)   │    │   (IPFS/GH)  │    │    (API)         │   │
│ └──────────────┘    └──────────────┘    └──────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────────────┐
        │              External Data Sources           │
        ├─────────────────────────────────────────────┤
        │  • Ethereum RPC (Infura/Alchemy/Local)      │
        │  • CSM Smart Contracts                       │
        │  • csm-rewards GitHub (Merkle Trees)        │
        │  • IPFS (Reward Tree Backup)                │
        │  • Beacon Chain API (beaconcha.in/local)    │
        └─────────────────────────────────────────────┘
```

---

## Data Sources & Contract Addresses

### Mainnet CSM Contracts
```python
CONTRACTS = {
    "CSModule": "0x1eB6d4da13ca9566c17F526aE0715325d7a07665",          # Main module
    "CSAccounting": "0x4d72BFF1BeaC69925F8Bd12526a39BAAb069e5Da",      # Bond & rewards
    "CSFeeDistributor": "0xD99CC66fEC647E68294C6477B40fC7E0F6F618D0", # Fee distribution
    "CSFeeOracle": "0x4D4074628678Bd302921c20573EEa1ed38DdF7FB",       # Oracle reports
    "stETH": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",             # stETH token
}
```

### External Data Sources
| Source | Purpose | Rate Limits |
|--------|---------|-------------|
| Ethereum RPC | Contract calls | Varies by provider |
| GitHub csm-rewards | Merkle tree & proofs | None |
| IPFS Gateway | Backup tree access | Varies |
| Beacon Chain API | Validator performance | ~10 req/sec |

---

## Core Features & Data Model

### 1. Operator Lookup (Input: Ethereum Address)

```python
@dataclass
class CSMOperator:
    node_operator_id: int
    manager_address: str
    rewards_address: str
    total_validators: int
    deposited_validators: int
    exited_validators: int
    validators: List[ValidatorInfo]
    
@dataclass
class ValidatorInfo:
    pubkey: str
    index: int  # Beacon chain index
    status: str  # pending, active, exited
    activation_epoch: int
    balance: int  # Current balance in Gwei
```

### 2. Rewards Calculation (YOUR PRIMARY USE CASE)

```python
@dataclass
class OperatorRewards:
    # Bond Information
    current_bond: float          # Total stETH bond held
    required_bond: float         # Minimum required bond
    excess_bond: float           # current_bond - required_bond (CLAIMABLE!)
    
    # Cumulative Rewards
    total_rewards_earned: float  # All-time staking rewards (stETH shares)
    claimed_rewards: float       # Already claimed
    unclaimed_rewards: float     # Available to claim now
    
    # Bond Rebase (stETH appreciation)
    bond_rebase_earnings: float  # Earnings from stETH rebasing
    
    # Calculated Totals
    total_claimable: float       # excess_bond + unclaimed_rewards
    
    # Performance Metrics
    current_frame_performance: float
    meets_threshold: bool
```

**Key Formula from Lido Docs:**
```
claimable_rewards = totalBond + nodeOperatorRewards - bondRequired
                  = excess_bond + unclaimed_staking_rewards
```

### 3. Historical Tracking

```python
@dataclass
class RewardsSnapshot:
    timestamp: datetime
    block_number: int
    oracle_frame: int            # 28-day frames
    
    # Point-in-time values
    bond_balance: float
    rewards_accumulated: float
    excess_bond: float
    eth_price_usd: float         # Optional
    
    # Delta since last snapshot
    rewards_delta: float
    bond_rebase_delta: float
```

---

## Implementation Details

### Phase 1: Core Data Retrieval

#### 1.1 Find Operator by Address
```python
from web3 import Web3

async def find_operator_by_address(address: str) -> Optional[int]:
    """
    Search for CSM operator by manager or rewards address.
    Returns node_operator_id or None.
    """
    csm_module = w3.eth.contract(
        address=CONTRACTS["CSModule"],
        abi=CSM_MODULE_ABI
    )
    
    # Get total operator count
    total_operators = csm_module.functions.getNodeOperatorsCount().call()
    
    # Search through operators (can be optimized with events)
    for op_id in range(total_operators):
        op_data = csm_module.functions.getNodeOperator(op_id).call()
        if op_data['managerAddress'] == address or op_data['rewardAddress'] == address:
            return op_id
    
    return None
```

#### 1.2 Get Operator Validators
```python
async def get_operator_validators(operator_id: int) -> List[str]:
    """Get all validator pubkeys for an operator."""
    csm_module = w3.eth.contract(
        address=CONTRACTS["CSModule"],
        abi=CSM_MODULE_ABI
    )
    
    # Get signing keys for operator
    keys_count = csm_module.functions.getNodeOperator(operator_id).call()[3]  # totalAddedKeys
    
    keys = []
    for i in range(keys_count):
        key_data = csm_module.functions.getSigningKey(operator_id, i).call()
        keys.append(key_data[0])  # pubkey
    
    return keys
```

#### 1.3 Get Bond & Rewards Data
```python
async def get_rewards_data(operator_id: int) -> OperatorRewards:
    """
    Fetch all reward-related data for an operator.
    This is the core function for your use case.
    """
    cs_accounting = w3.eth.contract(
        address=CONTRACTS["CSAccounting"],
        abi=CS_ACCOUNTING_ABI
    )
    
    # Get bond information
    bond_summary = cs_accounting.functions.getBondSummary(operator_id).call()
    # Returns: (current, required)
    current_bond = bond_summary[0] / 1e18  # Convert from wei
    required_bond = bond_summary[1] / 1e18
    excess_bond = max(0, current_bond - required_bond)
    
    # Get cumulative rewards from Merkle tree
    tree_data = await fetch_rewards_tree()
    operator_rewards = tree_data.get(f"CSM Operator {operator_id}", {})
    total_rewards = int(operator_rewards.get("cumulativeFeeShares", 0)) / 1e18
    
    # Get claimed rewards
    claimed = cs_accounting.functions.getClaimedRewards(operator_id).call() / 1e18
    
    unclaimed = total_rewards - claimed
    
    return OperatorRewards(
        current_bond=current_bond,
        required_bond=required_bond,
        excess_bond=excess_bond,
        total_rewards_earned=total_rewards,
        claimed_rewards=claimed,
        unclaimed_rewards=unclaimed,
        bond_rebase_earnings=calculate_bond_rebase(operator_id),  # See below
        total_claimable=excess_bond + unclaimed,
        current_frame_performance=await get_frame_performance(operator_id),
        meets_threshold=True  # From performance oracle
    )
```

#### 1.4 Fetch Rewards Tree
```python
import httpx

REWARDS_TREE_URL = "https://raw.githubusercontent.com/lidofinance/csm-rewards/main/tree.json"

async def fetch_rewards_tree() -> dict:
    """
    Fetch the latest rewards Merkle tree from GitHub.
    This contains cumulative rewards for all operators.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(REWARDS_TREE_URL)
        tree_data = response.json()
    
    # Parse tree into operator -> rewards mapping
    rewards_map = {}
    for entry in tree_data.get("values", []):
        # Entry format: [nodeOperatorId, cumulativeFeeShares]
        op_id = entry["value"][0]
        cumulative = entry["value"][1]
        rewards_map[f"CSM Operator {op_id}"] = {
            "cumulativeFeeShares": cumulative,
            "proof": entry.get("proof", [])
        }
    
    return rewards_map
```

### Phase 2: Bond Rebase Calculation

```python
async def calculate_bond_rebase(operator_id: int) -> float:
    """
    Calculate earnings from stETH bond rebasing.
    
    stETH is a rebasing token - the balance increases as staking rewards
    accumulate. The "bond rebase" is the appreciation of the bond value
    due to this mechanism.
    """
    cs_accounting = w3.eth.contract(
        address=CONTRACTS["CSAccounting"],
        abi=CS_ACCOUNTING_ABI
    )
    steth = w3.eth.contract(
        address=CONTRACTS["stETH"],
        abi=STETH_ABI
    )
    
    # Get operator's bond shares (not ETH value)
    bond_shares = cs_accounting.functions.getBondShares(operator_id).call()
    
    # Get current share rate
    total_pooled_eth = steth.functions.getTotalPooledEther().call()
    total_shares = steth.functions.getTotalShares().call()
    share_rate = total_pooled_eth / total_shares
    
    # Current bond value in ETH
    current_bond_eth = (bond_shares * share_rate) / 1e18
    
    # Original bond deposited (from events or storage)
    original_deposit = await get_original_bond_deposit(operator_id)
    
    # Rebase earnings = current value - original deposit
    rebase_earnings = current_bond_eth - original_deposit
    
    return rebase_earnings
```

### Phase 3: CLI Implementation

```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()

@app.command()
def check(
    address: str = typer.Argument(..., help="Ethereum address (manager or rewards)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show validator details")
):
    """
    Check CSM operator rewards and earnings for an address.
    """
    console.print(f"\n[bold]Checking CSM operator for address:[/bold] {address}\n")
    
    # Find operator
    operator_id = asyncio.run(find_operator_by_address(address))
    
    if operator_id is None:
        console.print("[red]No CSM operator found for this address[/red]")
        raise typer.Exit(1)
    
    console.print(f"[green]Found Operator ID:[/green] {operator_id}\n")
    
    # Get rewards data
    rewards = asyncio.run(get_rewards_data(operator_id))
    
    # Display summary table
    table = Table(title="💰 Earnings Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Notes", style="dim")
    
    table.add_row(
        "Current Bond",
        f"{rewards.current_bond:.4f} stETH",
        f"Required: {rewards.required_bond:.4f}"
    )
    table.add_row(
        "Excess Bond",
        f"{rewards.excess_bond:.4f} stETH",
        "⭐ Claimable!"
    )
    table.add_row(
        "Bond Rebase Earnings",
        f"{rewards.bond_rebase_earnings:.4f} stETH",
        "From stETH appreciation"
    )
    table.add_row("", "", "")  # Spacer
    table.add_row(
        "Total Rewards Earned",
        f"{rewards.total_rewards_earned:.4f} stETH",
        "All-time cumulative"
    )
    table.add_row(
        "Already Claimed",
        f"{rewards.claimed_rewards:.4f} stETH",
        ""
    )
    table.add_row(
        "Unclaimed Rewards",
        f"{rewards.unclaimed_rewards:.4f} stETH",
        "⭐ Claimable!"
    )
    table.add_row("", "", "")  # Spacer
    table.add_row(
        "TOTAL CLAIMABLE",
        f"[bold]{rewards.total_claimable:.4f} stETH[/bold]",
        "Excess bond + unclaimed"
    )
    
    console.print(table)
    
    # Performance status
    if rewards.meets_threshold:
        console.print("\n✅ [green]Performance meets threshold - earning full rewards[/green]")
    else:
        console.print("\n⚠️  [yellow]Performance below threshold - reduced rewards this frame[/yellow]")

@app.command()
def watch(
    address: str = typer.Argument(..., help="Ethereum address to monitor"),
    interval: int = typer.Option(300, "--interval", "-i", help="Refresh interval in seconds")
):
    """
    Continuously monitor rewards with live updates.
    """
    import time
    
    while True:
        console.clear()
        check(address, detailed=False)
        console.print(f"\n[dim]Refreshing every {interval} seconds... Press Ctrl+C to stop[/dim]")
        time.sleep(interval)

if __name__ == "__main__":
    app()
```

### Phase 4: Web Interface

```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="CSM Operator Dashboard")

@app.get("/api/operator/{address}")
async def get_operator(address: str):
    """API endpoint to fetch operator data."""
    operator_id = await find_operator_by_address(address)
    
    if operator_id is None:
        raise HTTPException(status_code=404, detail="Operator not found")
    
    rewards = await get_rewards_data(operator_id)
    validators = await get_operator_validators(operator_id)
    
    return {
        "operator_id": operator_id,
        "address": address,
        "rewards": {
            "current_bond": rewards.current_bond,
            "required_bond": rewards.required_bond,
            "excess_bond": rewards.excess_bond,
            "total_rewards_earned": rewards.total_rewards_earned,
            "claimed_rewards": rewards.claimed_rewards,
            "unclaimed_rewards": rewards.unclaimed_rewards,
            "bond_rebase_earnings": rewards.bond_rebase_earnings,
            "total_claimable": rewards.total_claimable,
        },
        "validators": {
            "total": len(validators),
            "pubkeys": validators
        },
        "performance": {
            "meets_threshold": rewards.meets_threshold,
            "current_frame": rewards.current_frame_performance
        }
    }

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the main dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CSM Operator Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    </head>
    <body class="bg-gray-900 text-white min-h-screen">
        <!-- React/HTMX frontend here -->
    </body>
    </html>
    """
```

---

## Project Structure

```
csm-dashboard/
├── pyproject.toml              # Poetry/pip dependencies
├── README.md
├── .env.example                # RPC URLs, API keys
│
├── src/
│   ├── __init__.py
│   ├── main.py                 # Entry point
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Configuration & constants
│   │   ├── contracts.py        # Contract ABIs & addresses
│   │   └── types.py            # Data classes
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── onchain.py          # Web3 contract interactions
│   │   ├── rewards_tree.py     # Merkle tree fetching
│   │   ├── beacon.py           # Beacon chain API
│   │   └── cache.py            # Data caching layer
│   │
│   ├── cli/
│   │   ├── __init__.py
│   │   └── commands.py         # Typer CLI commands
│   │
│   └── web/
│       ├── __init__.py
│       ├── app.py              # FastAPI application
│       ├── routes.py           # API endpoints
│       └── templates/          # HTML templates
│
├── tests/
│   ├── test_onchain.py
│   ├── test_rewards.py
│   └── conftest.py
│
└── abis/                       # Contract ABIs
    ├── CSModule.json
    ├── CSAccounting.json
    └── CSFeeDistributor.json
```

---

## Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"

# Core
web3 = "^6.0"                   # Ethereum interaction
httpx = "^0.25"                 # Async HTTP client

# CLI
typer = "^0.9"                  # CLI framework
rich = "^13.0"                  # Beautiful terminal output

# Web
fastapi = "^0.104"              # Web framework
uvicorn = "^0.24"               # ASGI server
jinja2 = "^3.1"                 # Templates

# Data
pydantic = "^2.5"               # Data validation
python-dotenv = "^1.0"          # Environment variables

# Optional
sqlalchemy = "^2.0"             # For historical tracking DB
redis = "^5.0"                  # For caching (optional)
```

---

## Configuration

```python
# src/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # RPC Configuration
    ETH_RPC_URL: str = "https://eth.llamarpc.com"
    
    # Beacon Chain API
    BEACON_API_URL: str = "https://beaconcha.in/api/v1"
    
    # Data Sources
    REWARDS_TREE_URL: str = "https://raw.githubusercontent.com/lidofinance/csm-rewards/main/tree.json"
    
    # Cache Settings
    CACHE_TTL_SECONDS: int = 300  # 5 minutes
    
    # Network
    NETWORK: str = "mainnet"  # or "holesky" for testnet
    
    class Config:
        env_file = ".env"
```

---

## Usage Examples

### CLI Mode
```bash
# Quick check
$ csm-dashboard check 0xYourAddress

# Detailed view with validators
$ csm-dashboard check 0xYourAddress --detailed

# Continuous monitoring
$ csm-dashboard watch 0xYourAddress --interval 60

# Export to JSON
$ csm-dashboard check 0xYourAddress --format json > rewards.json
```

### Web Mode
```bash
# Start server
$ csm-dashboard serve --port 8080

# Access at http://localhost:8080
```

### Python API
```python
from csm_dashboard import CSMClient

client = CSMClient(rpc_url="https://eth.llamarpc.com")

# Get rewards for your ~200 validators
rewards = await client.get_rewards("0xYourAddress")

print(f"Total Claimable: {rewards.total_claimable:.4f} stETH")
print(f"Excess Bond: {rewards.excess_bond:.4f} stETH")
print(f"Unclaimed Rewards: {rewards.unclaimed_rewards:.4f} stETH")
```

---

## Estimated Development Timeline

| Phase | Description | Time Estimate |
|-------|-------------|---------------|
| 1 | Core data retrieval (contracts + rewards tree) | 2-3 days |
| 2 | CLI implementation | 1-2 days |
| 3 | Web interface (basic) | 2-3 days |
| 4 | Historical tracking | 2-3 days |
| 5 | Polish & testing | 1-2 days |
| **Total** | | **8-13 days** |

---

## Special Considerations for Your Setup (~200 Validators)

1. **Batch Queries**: With 200+ validators, use multicall to batch contract reads
2. **Caching**: Cache validator data to avoid hitting RPC limits
3. **Rewards Tree Size**: Your operator entry will be one of the larger ones in the tree
4. **Performance Tracking**: Consider tracking per-validator performance to identify underperformers

---

## Next Steps

1. **Validate Contract ABIs**: Fetch current ABIs from Etherscan for CSM contracts
2. **Test with Your Address**: Verify the operator lookup works with your actual address
3. **Start with CLI**: Build CLI first as it's simpler and validates the core logic
4. **Add Web Later**: Layer on the web interface once CLI is working

---

## References

- [Lido CSM Documentation](https://docs.lido.fi/staking-modules/csm/intro/)
- [CSM Rewards Repository](https://github.com/lidofinance/csm-rewards)
- [CSM Deployed Contracts](https://docs.lido.fi/deployed-contracts/)
- [Lido Python SDK](https://github.com/lidofinance/lido-python-sdk)
- [CSM Architecture](https://hackmd.io/@lido/rJMcGj0Ap)
