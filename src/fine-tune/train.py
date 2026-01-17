import os
from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
from unsloth import is_bfloat16_supported

# 1. Configuration
model_name = "unsloth/Qwen2.5-0.5B-Instruct" # Base model
max_seq_length = 2048 # Supports RoPE Scaling internally
load_in_4bit = True # Use 4bit quantization to reduce memory usage

# 2. Load Model & Tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    max_seq_length = max_seq_length,
    load_in_4bit = load_in_4bit,
)

# 3. Add LoRA weights
model = FastLanguageModel.get_peft_model(
    model,
    r = 16, # Rank
    target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj",],
    lora_alpha = 16,
    lora_dropout = 0, # Optimized for 0
    bias = "none",    # Optimized for "none"
    use_gradient_checkpointing = "unsloth", # 4x longer contexts
    random_state = 3407,
    use_rslora = False,
    loftq_config = None,
)

# 4. Data Preparation
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        # Format for Qwen2.5 Instruct
        text = f"<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n<|im_start|>user\n{instruction}\n\n{input}<|im_end|>\n<|im_start|>assistant\n{output}<|im_end|>"
        texts.append(text)
    return { "text" : texts, }

# Load local data
dataset = load_dataset("json", data_files={"train": "data/train_dataset_20260117_194659.jsonl", "test": "data/val_dataset_20260117_194659.jsonl"}, split="train")
dataset = dataset.map(formatting_prompts_func, batched = True,)

# 5. Trainer Setup
trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can make training 5x faster for short sequences.
    args = TrainingArguments(
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        max_steps = 60, # Small number for demonstration
        learning_rate = 2e-4,
        fp16 = not is_bfloat16_supported(),
        bf16 = is_bfloat16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

# 6. Train
trainer_stats = trainer.train()

# 7. Save
model.save_pretrained("qwen2.5-0.5b-lora") # Local saving
tokenizer.save_pretrained("qwen2.5-0.5b-lora")

print("Training finished. Model saved to qwen2.5-0.5b-lora")
