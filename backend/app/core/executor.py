from concurrent.futures import ThreadPoolExecutor

# CTO-Grade Global Thread Pool: 
# Reuse threads across all agent workflows to reduce context switch latency.
# For 2 vCPUs (Hugging Face), we use a larger pool because our agents are primarily I/O Wait bound.
GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=20, thread_name_prefix="agent_worker")
