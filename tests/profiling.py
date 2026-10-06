import time
import uuid
import json
from typing import Callable, Any, Dict, List
from src.schemas.llm import LLMExecuteResponse

class SystemProfiler:
    """
    End-to-End System Latency & Cost Profiling Harness
    Used to benchmark the complete agent workflow.
    """
    
    # Example pricing (per 1M tokens) - Adjust based on actual model (e.g. Gemini 1.5 Flash)
    COST_PER_1M_PROMPT_TOKENS = 0.075 
    COST_PER_1M_COMPLETION_TOKENS = 0.30

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def profile_workflow(self, workflow_name: str, workflow_fn: Callable[..., LLMExecuteResponse], *args, **kwargs) -> Dict[str, Any]:
        """
        Executes an agent workflow function, measuring latency and calculating cost.
        The workflow function must return an LLMExecuteResponse containing token counts.
        """
        print(f"\n[Profiler] Starting test: {workflow_name}...")
        
        start_time = time.time()
        
        try:
            # Execute the End-to-End agent workflow
            response: LLMExecuteResponse = workflow_fn(*args, **kwargs)
            status = "Success"
        except Exception as e:
            print(f"[Profiler] Workflow failed: {e}")
            response = LLMExecuteResponse(
                request_id=str(uuid.uuid4()),
                raw_output=f"Error: {str(e)}",
                latency_ms=(time.time() - start_time) * 1000,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0
            )
            status = "Failed"

        end_time = time.time()
        total_latency_ms = (end_time - start_time) * 1000
        
        # Calculate cost
        prompt_tokens = response.prompt_tokens or 0
        comp_tokens = response.completion_tokens or 0
        
        prompt_cost = (prompt_tokens / 1_000_000) * self.COST_PER_1M_PROMPT_TOKENS
        comp_cost = (comp_tokens / 1_000_000) * self.COST_PER_1M_COMPLETION_TOKENS
        total_cost = prompt_cost + comp_cost

        report = {
            "workflow_name": workflow_name,
            "status": status,
            "latency_ms": round(total_latency_ms, 2),
            "prompt_tokens": prompt_tokens,
            "completion_tokens": comp_tokens,
            "total_tokens": prompt_tokens + comp_tokens,
            "estimated_cost_usd": round(total_cost, 6)
        }
        
        self.results.append(report)
        print(f"[Profiler] Finished: {total_latency_ms:.2f}ms | Cost: ${total_cost:.6f}")
        return report

    def generate_report(self) -> str:
        """Generates a JSON summary report of all profiled workflows."""
        if not self.results:
            return "No profiling data collected."
            
        total_latency = sum(r['latency_ms'] for r in self.results)
        total_cost = sum(r['estimated_cost_usd'] for r in self.results)
        
        summary = {
            "total_workflows_tested": len(self.results),
            "average_latency_ms": round(total_latency / len(self.results), 2),
            "total_estimated_cost_usd": round(total_cost, 6),
            "detailed_runs": self.results
        }
        
        return json.dumps(summary, indent=4)

if __name__ == "__main__":
    # --- Example Usage (To be run once the agent is fully integrated) ---
    print("Initializing Profiling Harness...")
    profiler = SystemProfiler()
    
    # Dummy mock workflow for demonstration purposes
    def mock_agent_workflow(*args, **kwargs):
        time.sleep(1.2) # Simulate agent thinking
        return LLMExecuteResponse(
            raw_output="The student's issue has been resolved.",
            latency_ms=1200,
            prompt_tokens=450,
            completion_tokens=50,
            total_tokens=500
        )
        
    # Run a test profile
    profiler.profile_workflow("Test Scenario 1: Get Status", mock_agent_workflow)
    profiler.profile_workflow("Test Scenario 2: Draft Ticket", mock_agent_workflow)
    
    print("\n=== FINAL PROFILING REPORT ===")
    print(profiler.generate_report())
