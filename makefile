agent-build:
	docker compose build

agent-up:
	docker compose up -d

agent-down:
	docker compose down

agent-rebuild:
	docker compose down
	docker compose build
	docker compose up -d

agent-logs:
	docker compose logs -f

agent-check-model:
	docker exec -it ida_invoice_agent du -sh /app/hf_models/Qwen2.5-VL-7B-Instruct
	
agent-list-model:
	docker exec -it ida_invoice_agent ls -la /app/hf_models/Qwen2.5-VL-7B-Instruct


# allows to access the container's filesystem, inspect files
agent-shell:
	docker exec -it ida_invoice_agent bash  

agent-volume-check:
	docker volume ls | grep qwen_model_data

agent-clear-gpu:
	docker exec -it ida_invoice_agent python3 -c "import torch; torch.cuda.empty_cache(); print('GPU cache cleared')"
