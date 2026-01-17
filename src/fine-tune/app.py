import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

# Configuration
base_model_path = "unsloth/Qwen2.5-0.5B-Instruct"
lora_path = "./qwen2.5-0.5b-lora" # Local folder after training

# Load tokenizer and model
print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(base_model_path)
model = AutoModelForCausalLM.from_pretrained(
    base_model_path,
    torch_dtype=torch.float16,
    device_map="auto"
)

# Try to load LoRA if it exists
try:
    model = PeftModel.from_pretrained(model, lora_path)
    print("LoRA weights loaded successfully.")
except Exception as e:
    print(f"LoRA loading skipped or failed: {e}")

def respond(message, history):
    # Format according to Qwen Instruct template
    prompt = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n"
    for user_msg, assistant_msg in history:
        prompt += f"<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant\n{assistant_msg}<|im_end|>\n"
    prompt += f"<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n"
    
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7, top_p=0.9)
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response

# UI
demo = gr.ChatInterface(
    fn=respond,
    title="Qwen2.5 Fine-tuned Demo",
    description="Demo for the model fine-tuned on local code slices with Reasoning Traces."
)

if __name__ == "__main__":
    demo.launch()
