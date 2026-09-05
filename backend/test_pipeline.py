import asyncio
import logging
from app.services.analysis_pipeline import run_full_analysis

logging.basicConfig(level=logging.INFO)

async def test_pipeline():
    print("Running end-to-end pipeline analysis...")
    # Using Rajasthan desert coordinates
    result = await run_full_analysis(
        latitude=26.9124, 
        longitude=75.7873, 
        system_capacity_kw=10000, 
        land_area_sqkm=2.5, 
        energy_type="hybrid", 
        land_cover="open"
    )
    print("\n--- Pipeline Result Summary ---")
    print(f"Feasible: {result['feasibility']['is_feasible']}")
    print(f"Suitability Score: {result['suitability']['overall_score']}")
    print(f"Solar Capacity: {result['micrositing']['solar_capacity_mw']} MW")
    print(f"Wind Capacity: {result['micrositing']['wind_capacity_mw']} MW")
    print(f"Total Yield: {result['energy_yield']['annual_energy_yield_mwh']} MWh")
    print(f"NPV: {result['financial']['npv_usd']}")
    if result.get("ai_narrative") and result["ai_narrative"].get("narrative"):
        print("AI Narrative: Generated Successfully")
    else:
        print("AI Narrative: Unavailable/Fallback")
    print("-------------------------------")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
