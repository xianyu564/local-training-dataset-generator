from unsloth import FastLanguageModel
import torch

# Load the saved LoRA model
model_name = "qwen2.5-0.5b-lora"
max_seq_length = 2048
load_in_4bit = True

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    load_in_4bit = load_in_4bit,
)

# Export to GGUF
# You can choose "q4_k_m", "q5_k_m", "q8_0", "f16" etc.
print("Exporting to GGUF (q8_0)...")
model.save_pretrained_gguf("model_q8_0", tokenizer, quantization_method = "q8_0")

print("GGUF export finished.")
