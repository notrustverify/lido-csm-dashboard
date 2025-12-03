"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .routes import router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="CSM Operator Dashboard",
        description="Track your Lido CSM validator earnings",
        version="0.1.0",
    )

    app.include_router(router, prefix="/api")

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return """
<!DOCTYPE html>
<html>
<head>
    <title>CSM Operator Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 text-white min-h-screen p-8">
    <div class="max-w-4xl mx-auto">
        <h1 class="text-3xl font-bold mb-2">CSM Operator Dashboard</h1>
        <p class="text-gray-400 mb-8">Track your Lido Community Staking Module validator earnings</p>

        <form id="lookup-form" class="mb-8">
            <div class="flex gap-4">
                <input type="text" id="address"
                       placeholder="Enter Ethereum address or Operator ID"
                       class="flex-1 p-3 bg-gray-800 rounded text-white border border-gray-700 focus:border-blue-500 focus:outline-none" />
                <button type="submit"
                        class="px-6 py-3 bg-blue-600 rounded hover:bg-blue-700 font-medium">
                    Check Rewards
                </button>
            </div>
        </form>

        <div id="loading" class="hidden">
            <div class="flex items-center justify-center p-8">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <span class="ml-3">Loading...</span>
            </div>
        </div>

        <div id="error" class="hidden bg-red-900/50 border border-red-500 rounded p-4 mb-4">
            <p id="error-message" class="text-red-300"></p>
        </div>

        <div id="results" class="hidden">
            <div class="bg-gray-800 rounded-lg p-6 mb-6">
                <h2 class="text-xl font-bold mb-4">
                    Operator #<span id="operator-id"></span>
                </h2>
                <div class="grid grid-cols-2 gap-4 text-sm">
                    <div>
                        <span class="text-gray-400">Manager:</span>
                        <span id="manager-address" class="font-mono text-xs break-all"></span>
                    </div>
                    <div>
                        <span class="text-gray-400">Rewards:</span>
                        <span id="reward-address" class="font-mono text-xs break-all"></span>
                    </div>
                </div>
            </div>

            <div class="grid grid-cols-3 gap-4 mb-6">
                <div class="bg-gray-800 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold" id="total-validators">0</div>
                    <div class="text-gray-400 text-sm">Total Validators</div>
                </div>
                <div class="bg-gray-800 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-green-400" id="active-validators">0</div>
                    <div class="text-gray-400 text-sm">Active</div>
                </div>
                <div class="bg-gray-800 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-500" id="exited-validators">0</div>
                    <div class="text-gray-400 text-sm">Exited</div>
                </div>
            </div>

            <div class="bg-gray-800 rounded-lg p-6">
                <h3 class="text-lg font-bold mb-4">Earnings Summary</h3>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Current Bond</span>
                        <span><span id="current-bond">0</span> ETH</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Required Bond</span>
                        <span><span id="required-bond">0</span> ETH</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-400">Excess Bond</span>
                        <span class="text-green-400"><span id="excess-bond">0</span> ETH</span>
                    </div>
                    <hr class="border-gray-700">
                    <div class="flex justify-between">
                        <span class="text-gray-400">Unclaimed Rewards</span>
                        <span class="text-green-400"><span id="unclaimed-rewards">0</span> ETH</span>
                    </div>
                    <hr class="border-gray-700">
                    <div class="flex justify-between text-xl font-bold">
                        <span>Total Claimable</span>
                        <span class="text-yellow-400"><span id="total-claimable">0</span> ETH</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('lookup-form');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const errorMessage = document.getElementById('error-message');
        const results = document.getElementById('results');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const input = document.getElementById('address').value.trim();

            if (!input) return;

            // Reset UI
            loading.classList.remove('hidden');
            error.classList.add('hidden');
            results.classList.add('hidden');

            try {
                const response = await fetch(`/api/operator/${input}`);
                const data = await response.json();

                loading.classList.add('hidden');

                if (!response.ok) {
                    error.classList.remove('hidden');
                    errorMessage.textContent = data.detail || 'An error occurred';
                    return;
                }

                // Populate results
                document.getElementById('operator-id').textContent = data.operator_id;
                document.getElementById('manager-address').textContent = data.manager_address;
                document.getElementById('reward-address').textContent = data.reward_address;

                document.getElementById('total-validators').textContent = data.validators.total;
                document.getElementById('active-validators').textContent = data.validators.active;
                document.getElementById('exited-validators').textContent = data.validators.exited;

                document.getElementById('current-bond').textContent = data.rewards.current_bond_eth.toFixed(6);
                document.getElementById('required-bond').textContent = data.rewards.required_bond_eth.toFixed(6);
                document.getElementById('excess-bond').textContent = data.rewards.excess_bond_eth.toFixed(6);
                document.getElementById('unclaimed-rewards').textContent = data.rewards.unclaimed_eth.toFixed(6);
                document.getElementById('total-claimable').textContent = data.rewards.total_claimable_eth.toFixed(6);

                results.classList.remove('hidden');
            } catch (err) {
                loading.classList.add('hidden');
                error.classList.remove('hidden');
                errorMessage.textContent = err.message || 'Network error';
            }
        });
    </script>
</body>
</html>
        """

    return app
