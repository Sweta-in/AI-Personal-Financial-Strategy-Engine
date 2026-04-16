"""
Router integration tests — CRUD + quant endpoints.
"""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_root(client):
    response = await client.get("/")
    assert response.status_code == 200
    assert "disclaimer" in response.json()


# --- Loans ---

@pytest.mark.asyncio
async def test_create_loan(auth_client):
    response = await auth_client.post("/api/loans/", json={
        "name": "SBI Home Loan",
        "loan_type": "home",
        "principal": 3000000,
        "annual_rate": 8.5,
        "tenure_months": 240,
        "outstanding_balance": 2500000,
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "SBI Home Loan"
    assert data["emi"] is not None  # Auto-calculated


@pytest.mark.asyncio
async def test_list_loans(auth_client):
    await auth_client.post("/api/loans/", json={
        "name": "Test Loan",
        "loan_type": "personal",
        "principal": 500000,
        "annual_rate": 12,
        "tenure_months": 60,
        "outstanding_balance": 400000,
    })
    response = await auth_client.get("/api/loans/")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_calculate_emi_public(client):
    response = await client.post(
        "/api/loans/calculate-emi",
        params={"principal": 3000000, "annual_rate": 8.5, "tenure_months": 240},
    )
    assert response.status_code == 200
    data = response.json()
    assert abs(data["monthly_emi"] - 26049) < 50


# --- Assets ---

@pytest.mark.asyncio
async def test_create_asset(auth_client):
    response = await auth_client.post("/api/assets/", json={
        "name": "Mutual Funds",
        "asset_type": "equity",
        "current_value": 1500000,
        "invested_value": 1000000,
        "annual_return_pct": 15.0,
    })
    assert response.status_code == 201
    assert response.json()["name"] == "Mutual Funds"


# --- Insurance ---

@pytest.mark.asyncio
async def test_create_insurance(auth_client):
    response = await auth_client.post("/api/insurance/", json={
        "name": "HDFC Term Plan",
        "insurance_type": "term_life",
        "provider": "HDFC Life",
        "sum_assured": 10000000,
        "annual_premium": 15000,
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_insurance_gap_analysis(client):
    response = await client.post(
        "/api/insurance/gap-analysis",
        params={
            "annual_income": 1200000,
            "age": 30,
            "dependents": 2,
            "outstanding_loans": 3000000,
            "current_coverage": 5000000,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "adequacy_pct" in data
    assert "recommendation" in data


# --- Financial ---

@pytest.mark.asyncio
async def test_net_worth(auth_client):
    # Add an asset
    await auth_client.post("/api/assets/", json={
        "name": "Savings",
        "asset_type": "cash",
        "current_value": 500000,
    })
    # Add a loan
    await auth_client.post("/api/loans/", json={
        "name": "Personal Loan",
        "loan_type": "personal",
        "principal": 200000,
        "annual_rate": 12,
        "tenure_months": 24,
        "outstanding_balance": 200000,
    })
    response = await auth_client.get("/api/financial/net-worth")
    assert response.status_code == 200
    data = response.json()
    assert data["net_worth"] == 300000


# --- Portfolio Simulation ---

@pytest.mark.asyncio
async def test_monte_carlo_simulation(client):
    response = await client.post(
        "/api/portfolio/simulate",
        params={
            "initial_value": 1000000,
            "monthly_sip": 25000,
            "time_horizon_months": 60,
            "n_simulations": 100,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "final_value" in data
    assert data["final_value"]["p50"] > 0


# --- Decisions ---

@pytest.mark.asyncio
async def test_out_of_scope_question(auth_client):
    response = await auth_client.post("/api/decisions/ask", json={
        "question": "Which stock will go up tomorrow?"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["question_type"] == "out_of_scope"
